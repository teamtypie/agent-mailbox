# agent-mailbox

Tiny MCP server (Streamable HTTP at `/mcp`) acting as a shared mailbox between agents.
Tools: `post_message`, `read_messages`, `clear_messages`.

Every request needs `Authorization: Bearer <MAILBOX_TOKEN>`; otherwise 401.

Env: `MAILBOX_TOKEN` (required), `PORT` (default 10000), `DB_PATH` (default `./mailbox.db`).

Deploy on Render with `render.yaml`; set `MAILBOX_TOKEN` in the dashboard. Note: free-tier disk is ephemeral.
