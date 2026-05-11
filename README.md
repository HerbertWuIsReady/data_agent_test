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
