# Authentication and the MCP server

## storageState

`--storage-state session.json` loads cookies and localStorage before capture. The file is a Playwright
storageState export from a browser the user has already logged in with. Treat it as a secret: it is a
credential. Never print it, commit it, or echo its contents into the chat.

```bash
url2pdf https://app.example.com/report --storage-state ~/secrets/session.json
```

## MCP server (agents and persistent sessions)

The image also runs a Playwright MCP server. Use it when a client needs to drive the browser, or to keep a
named session across runs.

```bash
make mcp-up                  # default session, port 3000
make mcp-up SESSION=mysite   # named session, stored in ./workspace/sessions/mysite.json
MCP_PORT=3001 make mcp-up    # avoid a clash with Grafana or similar
make status                  # containers and health
make mcp-down
```

Endpoints: `http://localhost:<MCP_PORT>/sse` (SSE) and `http://localhost:<MCP_PORT>/mcp` (HTTP). Run these
from the `screenshot/` directory. `uv run ssc.py tools` lists the server's tools. Stop the server when done.
