import sqlite3, time, os, hmac
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
import uvicorn
from starlette.responses import JSONResponse

TOKEN = os.environ.get("MAILBOX_TOKEN", "").strip()
PORT = int(os.environ.get("PORT", "10000"))
DB = os.environ.get("DB_PATH", "./mailbox.db")

def db():
    c = sqlite3.connect(DB)
    c.execute("create table if not exists m(id integer primary key autoincrement,sender text,text text,ts text)")
    return c

mcp = FastMCP("agent-mailbox", host="0.0.0.0", port=PORT, stateless_http=True)
mcp.settings.transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

@mcp.tool()
def post_message(sender: str, text: str) -> int:
    """Post a message to the shared mailbox. Returns the new message id."""
    c = db()
    cur = c.execute("insert into m(sender,text,ts) values(?,?,?)",
                    (sender, text, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    c.commit()
    return cur.lastrowid

@mcp.tool()
def read_messages(since_id: int = 0, limit: int = 50) -> list[dict]:
    """Read messages with id > since_id, oldest first."""
    c = db()
    return [dict(id=r[0], sender=r[1], text=r[2], timestamp=r[3])
            for r in c.execute("select * from m where id>? order by id limit ?", (since_id, min(limit, 500)))]

@mcp.tool()
def clear_messages() -> int:
    """Delete all messages. Returns count deleted."""
    c = db()
    n = c.execute("delete from m").rowcount
    c.commit()
    return n

app = mcp.streamable_http_app()  # serves /mcp

class Auth:
    def __init__(self, a): self.a = a
    async def __call__(self, scope, recv, send):
        if scope["type"] == "http":
            h = dict(scope["headers"]).get(b"authorization", b"").decode("latin-1")
            ok = bool(TOKEN) and hmac.compare_digest(h.encode(), ("Bearer " + TOKEN).encode())
            if not ok:
                return await JSONResponse({"error": "unauthorized"}, 401)(scope, recv, send)
        await self.a(scope, recv, send)

if __name__ == "__main__":
    if not TOKEN:
        print("WARNING: MAILBOX_TOKEN not set; all requests will be refused (401).")
    uvicorn.run(Auth(app), host="0.0.0.0", port=PORT)
