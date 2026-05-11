# data-agent-mcp-init

Node.js initialization scenario for local data-agent workspaces.

It creates:

- `agent.md`: 数据分析师说明书。
- `.mcp.json`: remote MCP server configuration using the common `mcpServers` shape.

The default MCP URL is:

```text
https://voiceless-olive-giraffe.fastmcp.app/mcp
```

## Run From This Repository

```bash
DATA_AGENT_MCP_AUTH=your_fastmcp_token npx ./node-init
```

Initialize another directory:

```bash
DATA_AGENT_MCP_AUTH=your_fastmcp_token npx ./node-init --cwd /path/to/workspace
```

Override the MCP server URL:

```bash
npx ./node-init --auth your_fastmcp_token --mcp-url https://your-mcp-host.example.com/mcp
```

## Options

```text
--mcp-url <url>          Remote MCP server URL.
--auth <token>           FastMCP auth token. Can also use DATA_AGENT_MCP_AUTH.
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
      "url": "https://voiceless-olive-giraffe.fastmcp.app/mcp",
      "headers": {
        "Authorization": "Bearer your_fastmcp_token"
      }
    }
  }
}
```
