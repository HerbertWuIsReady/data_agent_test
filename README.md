# data-agent-mcp

Blank FastMCP project for building a data-agent MCP server.

## Structure

```text
src/data_agent_mcp/server.py
```

## Run

```bash
python -m data_agent_mcp.server
```

When running from source without installing the package first:

```bash
PYTHONPATH=src python3 -m data_agent_mcp.server
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Universal Node.js Local Init Scenario

This repository also includes a Node.js `npx` initializer under `node-init/`.
By default it initializes the current directory for both Codex and Claude Code with:

- `AGENTS.md`
- `.codex/config.toml` remote MCP server config
- `CLAUDE.md`
- `.mcp.json` project-scoped MCP server config

Run from this repository:

```bash
npx ./node-init
```

Initialize another directory:

```bash
npx ./node-init --cwd /path/to/workspace
```

Initialize only one client:

```bash
npx ./node-init --target codex
npx ./node-init --target claude
```

## Claude Code Local Init Scenario

For Claude Code only, you can also use the sibling initializer under `node-init-claude/`.
It initializes the current directory with:

- `CLAUDE.md`
- `.mcp.json` project-scoped MCP server config

Run from this repository:

```bash
npx ./node-init-claude
```

Initialize another directory:

```bash
npx ./node-init-claude --cwd /path/to/workspace
```
