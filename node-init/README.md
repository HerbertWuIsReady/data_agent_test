# data-agent-mcp-init

Node.js initialization scenario for local data-agent workspaces.

It creates:

- `agent.md`: local agent instructions for the data-agent workflow.
- `.mcp.json`: remote MCP server configuration using the common `mcpServers` shape.

## Run From This Repository

```bash
npx ./node-init --mcp-url https://your-mcp-host.example.com/mcp
```

Initialize another directory:

```bash
npx ./node-init --cwd /path/to/workspace --mcp-url https://your-mcp-host.example.com/mcp
```

## Options

```text
--mcp-url <url>          Remote MCP server URL. Required.
--server-name <name>     MCP server name. Default: data-agent
--cwd <path>             Directory to initialize. Default: current directory
--agent-file <path>      Agent instruction file. Default: agent.md
--config-file <path>     MCP config file. Default: .mcp.json
--force                  Overwrite existing generated files.
```

## Generated MCP Config

```json
{
  "mcpServers": {
    "data-agent": {
      "type": "http",
      "url": "https://your-mcp-host.example.com/mcp"
    }
  }
}
```
