# Node.js Init Scenario Test Report

Test date: 2026-05-11  
Target: `node-init/` — Codex + Claude Code workspace initializer  
Node.js version: v26.0.0
MCP Token: fmcp_JPXw3NYlyvgGjqJTQKeGlnW0lhRYUMEtois7Q4vZf_w

## Scope

- Syntax-check `node-init/bin/init.js`
- Test `--target both` (default), `--target codex`, `--target claude`
- Verify generated files for each target
- Test all CLI options and edge cases
- Validate generated output for Codex and Claude Code compatibility
- Verify approval policy settings for Codex

## Test Results

### 1. Syntax Check

| Test | Result |
| --- | --- |
| `node --check ./node-init/bin/init.js` | PASS |

### 2. Target Mode Tests

| # | Test | Args | Result |
| --- | --- | --- | --- |
| 1 | Target both (default) | `--cwd <tmp> --force` | PASS — generates AGENTS.md + .codex/config.toml + CLAUDE.md + .mcp.json |
| 2 | Target codex only | `--target codex --cwd <tmp> --force` | PASS — only AGENTS.md + .codex/config.toml |
| 3 | Target claude only | `--target claude --cwd <tmp> --force` | PASS — only CLAUDE.md + .mcp.json |
| 4 | Invalid target | `--target invalid` | PASS — exits 1 with valid options listed |
| 5 | Skip existing (no force) | default on existing files | PASS — all 4 files skipped |

### 3. CLI Option Tests

| # | Test | Args | Result | Notes |
| --- | --- | --- | --- | --- |
| 1 | Help | `--help` | PASS | All options documented |
| 2 | Custom MCP URL | `--mcp-url https://custom.example.com/mcp` | PASS | URL reflected in both config formats |
| 3 | Custom token env var | `--token-env-var MY_CUSTOM_TOKEN` | PASS | Env var name in both configs |
| 4 | Custom server name | `--server-name my_agent` | PASS | Codex config uses custom name |
| 5 | Custom claude server name | `--claude-server-name my-agent` | PASS | .mcp.json uses custom name |
| 6 | Custom agent/config file paths | `--agent-file` / `--config-file` | PASS | Codex paths honored |
| 7 | Custom claude file paths | `--claude-file` / `--claude-config-file` | PASS | Claude paths honored |
| 8 | Custom cwd | `--cwd /tmp/test-dir` | PASS | Initializes target directory |
| 9 | Force overwrite | `--force` on existing files | PASS | Overwrites previously skipped files |
| 10 | Unknown argument | `--unknown-flag` | PASS | Exits code 1 |
| 11 | Missing value | `--mcp-url` (no value) | PASS | Exits code 1 |

### 4. Generated File Content Verification

#### Codex: `.codex/config.toml`

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

- TOML syntax: PASS
- `default_tools_approval_mode = "approve"` — auto-approves MCP tools: PASS
- `sandbox_mode = "workspace-write"` — allows workspace writes: PASS
- `bearer_token_env_var` references env var: PASS

#### Claude Code: `.mcp.json`

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

- Valid JSON: PASS
- `mcpServers` top-level key: PASS (Claude Code standard)
- `type: "http"` for remote SSE transport: PASS
- `headers.Authorization` with env var expansion `${...}`: PASS
- Server name uses hyphens (`data-agent`): PASS (Claude Code convention)

#### AGENTS.md / CLAUDE.md

Both files are identical. Content is now generic — does not hardcode server names or URLs:
- MCP-agnostic instructions: PASS
- "先发现当前可用的 MCP 工具能力" guidance: PASS
- SQL safety rules: PASS
- Output style guidelines: PASS

### 5. Cross-Platform Compatibility

| Requirement | Codex | Claude Code |
| --- | --- | --- |
| Agent instruction file | `AGENTS.md` | `CLAUDE.md` |
| MCP config file | `.codex/config.toml` | `.mcp.json` |
| Config format | TOML | JSON |
| Auth mechanism | `bearer_token_env_var` | `headers.Authorization` with `${ENV_VAR}` |
| Tool approval | `[apps].default_tools_approval_mode = "approve"` | N/A (Claude Code uses its own permission system) |
| Server naming | `data_agent` (underscore) | `data-agent` (hyphen) |

### 6. Code Review Notes

- **`renderAgent()` no longer takes parameters**: Agent instructions are now MCP-agnostic — good for portability.
- **Default server names differ**: `data_agent` (Codex) vs `data-agent` (Claude) — follows each platform's naming conventions.
- **Claude `.mcp.json` format**: Uses `${DATA_AGENT_MCP_TOKEN}` for env var expansion — Claude Code resolves this at runtime.
- **`--target` validation**: Rejects invalid targets with clear error message listing valid options.
- **`exists()` still uses `readFile`**: Works correctly but `fs.access` would be more idiomatic. Not blocking.

## Overall Result

**PASS** — 16/16 tests passed.

The `node-init` initializer now supports both Codex and Claude Code via the `--target` flag. For Codex, it generates `AGENTS.md` + `.codex/config.toml` with auto-approval settings. For Claude Code, it generates `CLAUDE.md` + `.mcp.json` in the standard Claude Code MCP format. The agent instructions are platform-agnostic and guide the model to discover available MCP tools at runtime rather than hardcoding server names.
