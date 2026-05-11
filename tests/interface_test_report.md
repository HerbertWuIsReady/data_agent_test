# Interface Test Report

Test date: 2026-05-11

Scope:

- Start the FastMCP entry point.
- Call every exported MCP tool function in `data_agent_mcp.server`.
- Run the automated test suite that covers normal paths, invalid inputs, permission boundaries, dependency failures, inconsistent data, and idempotency.

No production code was changed.

## Environment

- Python runtime: `.venv/bin/python`
- Package entry point: `.venv/bin/data-agent-mcp`
- Database: `data/data_agent.db`
- FastMCP dependency: installed in `.venv`

## Startup Test

Command:

```bash
.venv/bin/data-agent-mcp
```

Result: PASS

Observed output:

```text
FastMCP 3.2.4
Server: data-agent, 3.2.4
Starting MCP server 'data-agent' with transport 'stdio'
```

Note: the server uses stdio transport for MCP. In this local command run it started successfully and exited with code `0`.

## Per-Interface Smoke Test

Command:

```bash
.venv/bin/python - <<'PY'
import json
from data_agent_mcp import server

cases = [
    ("search_prompt", lambda: server.search_prompt("指标", 3)),
    ("get_prompt_detail", lambda: server.get_prompt_detail("metric_trend_analysis")),
    ("search_metric", lambda: server.search_metric("DAU", 3)),
    ("get_metric_detail", lambda: server.get_metric_detail("日活跃用户数")),
    ("search_column", lambda: server.search_column("country", 3)),
    ("search_table", lambda: server.search_table("DAU", 3)),
    ("get_table_schema", lambda: server.get_table_schema("ads_user_active_metric_di")),
    (
        "validate_sql",
        lambda: server.validate_sql(
            "SELECT COUNT(*) AS cnt FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"
        ),
    ),
    (
        "execute_query",
        lambda: server.execute_query(
            "SELECT country, COUNT(DISTINCT user_id) AS dau "
            "FROM ads_user_active_metric_di "
            "WHERE dt = '2026-05-10' AND is_valid_event = 1 AND is_bot = 0 "
            "GROUP BY country ORDER BY country"
        ),
    ),
]

for name, call in cases:
    try:
        result = call()
        status = "PASS"
    except Exception as exc:
        result = {"exception": type(exc).__name__, "message": str(exc)}
        status = "FAIL"
    print(json.dumps({"interface": name, "status": status, "result": result}, ensure_ascii=False, default=str))
PY
```

Results:

| Interface | Result | Key observation |
| --- | --- | --- |
| `search_prompt` | PASS | Returned 3 prompt candidates for query `指标`. |
| `get_prompt_detail` | PASS | Returned detail for `metric_trend_analysis`. |
| `search_metric` | PASS | Returned DAU-related metrics, with `dau` first. |
| `get_metric_detail` | PASS | Returned metric detail for `日活跃用户数`. |
| `search_column` | PASS | Returned `country` column metadata. |
| `search_table` | PASS | Returned 3 DAU-related tables. |
| `get_table_schema` | PASS | Returned schema and columns for `ads_user_active_metric_di`. |
| `validate_sql` | PASS | Accepted partitioned read-only SQL and returned validation id `91ae37dc24e76ec7`. |
| `execute_query` | PASS | Returned 3 grouped rows: `CN=2`, `SA=1`, `US=1`. |

## Automated Regression Test

Command:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Result: PASS

Summary:

```text
Ran 31 tests
OK
```

Coverage focus:

| Area | Covered cases |
| --- | --- |
| Normal path | Lookup tools, schema retrieval, SQL validation, SQL execution. |
| Empty/invalid input | Blank SQL, unknown metric/table, no-match lookup. |
| Permission boundary | Write SQL rejection, multiple statement rejection, validation id mismatch. |
| External failure | Missing SQLite database, metadata points to missing physical table. |
| Data inconsistency | Inactive table metadata, inactive column metadata. |
| Duplicate/idempotent requests | Repeated SQL validation, repeated query execution, repeated initializer runs. |

## Lint Check

Command:

```bash
.venv/bin/python -m ruff check .
```

Result: PASS

Output:

```text
All checks passed!
```

## Overall Result

All requested interface startup and smoke tests passed. The broader automated test suite also passed.

Remaining demo-level limitations:

- The per-interface smoke test calls Python functions directly, not through a real MCP client session.
- The server uses stdio transport, so local startup verification confirms process startup but does not exercise a long-running network endpoint.
- SQL validation is still regex-based, which is acceptable for this demo but not production-grade SQL security.
