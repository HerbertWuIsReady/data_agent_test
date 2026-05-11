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

## Node.js Local Init Scenario

This repository also includes a Node.js `npx` initializer under `node-init/`.
It initializes the current directory with:

- `AGENTS.md`
- `.codex/config.toml` remote MCP server config

Run from this repository:

```bash
npx ./node-init
```

Initialize another directory:

```bash
npx ./node-init --cwd /path/to/workspace
```
