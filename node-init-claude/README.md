# data-agent-claude-init

Node.js initialization scenario for Claude Code workspaces.

It creates:

- `CLAUDE.md`: 通用数据分析师说明书。
- `.mcp.json`: Claude Code project-scoped MCP server configuration.

The default MCP URL is:

```text
https://voiceless-olive-giraffe.fastmcp.app/mcp
```

## Run From This Repository

```bash
npx ./node-init-claude
```

Initialize another directory:

```bash
npx ./node-init-claude --cwd /path/to/workspace
```

Override the MCP server URL:

```bash
npx ./node-init-claude --mcp-url https://your-mcp-host.example.com/mcp
```

Before running Claude Code in the initialized workspace, export the bearer token:

```bash
export DATA_AGENT_MCP_TOKEN="your_fastmcp_token"
```

## Options

```text
--mcp-url <url>          Remote MCP server URL.
--token-env-var <name>   Env var expanded by Claude Code for bearer token. Default: DATA_AGENT_MCP_TOKEN
--server-name <name>     MCP server name. Default: data-agent
--cwd <path>             Directory to initialize. Default: current directory
--agent-file <path>      Claude instruction file. Default: CLAUDE.md
--config-file <path>     Claude Code MCP config file. Default: .mcp.json
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
        "Authorization": "Bearer ${DATA_AGENT_MCP_TOKEN}"
      }
    }
  }
}
```
