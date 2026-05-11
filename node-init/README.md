# data-agent-mcp-init

Node.js initialization scenario for local data-agent workspaces.

By default it initializes a workspace for both Codex and Claude Code.

It creates:

- `AGENTS.md`: 数据分析师说明书。
- `.codex/config.toml`: Codex remote MCP server configuration.
- `CLAUDE.md`: Claude Code instruction file.
- `.mcp.json`: Claude Code project-scoped MCP server configuration.

The default MCP URL is:

```text
https://voiceless-olive-giraffe.fastmcp.app/mcp
```

## Run From This Repository

```bash
npx ./node-init
```

Initialize another directory:

```bash
npx ./node-init --cwd /path/to/workspace
```

Initialize only Codex:

```bash
npx ./node-init --target codex
```

Initialize only Claude Code:

```bash
npx ./node-init --target claude
```

Override the MCP server URL:

```bash
npx ./node-init --mcp-url https://your-mcp-host.example.com/mcp
```

Before running Codex in the initialized workspace, export the bearer token:

```bash
export DATA_AGENT_MCP_TOKEN="your_fastmcp_token"
```

## Options

```text
--target <name>         Initialization target: both, codex, claude. Default: both
--mcp-url <url>          Remote MCP server URL.
--token-env-var <name>   Env var used for bearer token. Default: DATA_AGENT_MCP_TOKEN
--server-name <name>     Codex MCP server/app name. Default: data_agent
--claude-server-name <name>
                          Claude Code MCP server name. Default: data-agent
--cwd <path>             Directory to initialize. Default: current directory
--agent-file <path>      Codex instruction file. Default: AGENTS.md
--config-file <path>     Codex MCP config file. Default: .codex/config.toml
--claude-file <path>     Claude instruction file. Default: CLAUDE.md
--claude-config-file <path>
                          Claude MCP config file. Default: .mcp.json
--force                  Overwrite existing generated files.
```

## Generated Codex MCP Config

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[mcp_servers.data_agent]
url = "https://voiceless-olive-giraffe.fastmcp.app/mcp"
bearer_token_env_var = "DATA_AGENT_MCP_TOKEN"
enabled = true
tool_timeout_sec = 60

[apps.data_agent]
default_tools_approval_mode = "approve"
destructive_enabled = false
open_world_enabled = false
```

## Generated Claude Code MCP Config

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
