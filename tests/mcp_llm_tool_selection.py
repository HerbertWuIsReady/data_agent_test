import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Client

from data_agent_mcp.server import mcp


REPORT_PATH = Path(__file__).with_name("mcp_llm_tool_selection_report.md")
JSON_PATH = Path(__file__).with_name("mcp_llm_tool_selection_results.json")


SCENARIOS = [
    {
        "name": "metric_candidate_search",
        "user_need": "我想找 DAU 这个指标，先帮我召回候选指标。",
        "expected_tool": "search_metric",
        "result_check": "non_empty_items",
    },
    {
        "name": "metric_detail_lookup",
        "user_need": "请查看日活跃用户数的完整指标口径、公式和来源表。",
        "expected_tool": "get_metric_detail",
        "result_check": "has_item",
    },
    {
        "name": "column_lookup",
        "user_need": "我要按国家分组分析 DAU，请先找 country 字段信息。",
        "expected_tool": "search_column",
        "result_check": "non_empty_items",
    },
    {
        "name": "table_lookup",
        "user_need": "根据 DAU 需求找一下应该使用哪些数据表。",
        "expected_tool": "search_table",
        "result_check": "non_empty_items",
    },
    {
        "name": "schema_lookup",
        "user_need": "请查看 ads_user_active_metric_di 这张表的字段结构。",
        "expected_tool": "get_table_schema",
        "result_check": "has_item",
    },
    {
        "name": "sql_validation",
        "user_need": (
            "请校验这段 SQL 是否安全可执行："
            "SELECT COUNT(*) AS dau FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"
        ),
        "expected_tool": "validate_sql",
        "result_check": "valid_sql",
    },
    {
        "name": "query_execution",
        "user_need": (
            "请执行这个已经带分区条件的只读查询："
            "SELECT country, COUNT(DISTINCT user_id) AS dau "
            "FROM ads_user_active_metric_di "
            "WHERE dt = '2026-05-10' AND is_valid_event = 1 AND is_bot = 0 "
            "GROUP BY country ORDER BY country"
        ),
        "expected_tool": "execute_query",
        "result_check": "successful_query",
    },
    {
        "name": "prompt_search",
        "user_need": "用户想做指标趋势分析，请先找相关 SQL 生成规范 Prompt。",
        "expected_tool": "search_prompt",
        "result_check": "non_empty_items",
    },
]


def compact_tools(tools: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
        }
        for tool in tools
    ]


def choose_tool_with_llm(tools: list[dict[str, Any]], user_need: str) -> dict[str, Any]:
    prompt = f"""
You are choosing one MCP tool for a client.
Return only a JSON object with this shape:
{{"tool": "<tool name>", "arguments": {{...}}}}

Available tools:
{json.dumps(tools, ensure_ascii=False, indent=2)}

User need:
{user_need}

Rules:
- Choose exactly one tool from the available tools.
- Fill required arguments.
- Use small top_n values, usually 3.
- Do not explain.
""".strip()

    completed = subprocess.run(
        [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--json",
            prompt,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    for line in reversed(completed.stdout.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            return json.loads(item["text"])

    raise RuntimeError(f"No LLM tool selection found in output: {completed.stdout}")


def summarize_call_result(result: Any) -> Any:
    if getattr(result, "data", None) is not None:
        return result.data
    if getattr(result, "structured_content", None) is not None:
        return result.structured_content
    return str(result)


def result_quality_passed(result: Any, check_name: str) -> bool:
    if check_name == "non_empty_items":
        return bool(isinstance(result, dict) and result.get("items"))
    if check_name == "has_item":
        return bool(isinstance(result, dict) and result.get("item"))
    if check_name == "valid_sql":
        return bool(isinstance(result, dict) and result.get("is_valid") is True)
    if check_name == "successful_query":
        return bool(
            isinstance(result, dict)
            and result.get("status") == "success"
            and result.get("row_count", 0) > 0
        )
    raise ValueError(f"Unknown result check: {check_name}")


async def run_scenarios() -> list[dict[str, Any]]:
    records = []
    async with Client(mcp) as client:
        tools = await client.list_tools()
        compact = compact_tools(tools)

        for scenario in SCENARIOS:
            selected = choose_tool_with_llm(compact, scenario["user_need"])
            tool_name = selected["tool"]
            arguments = selected.get("arguments") or {}
            record = {
                **scenario,
                "selected_tool": tool_name,
                "arguments": arguments,
                "selection_passed": tool_name == scenario["expected_tool"],
            }

            try:
                call_result = await client.call_tool(tool_name, arguments)
                record["call_passed"] = not call_result.is_error
                result = summarize_call_result(call_result)
                record["result"] = result
                record["result_quality_passed"] = result_quality_passed(result, scenario["result_check"])
            except Exception as exc:
                record["call_passed"] = False
                record["result_quality_passed"] = False
                record["error"] = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }

            records.append(record)

    return records


def write_report(records: list[dict[str, Any]]) -> None:
    JSON_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# MCP LLM Tool Selection Report",
        "",
        f"Test date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Goal: verify that a client can discover MCP tools, ask an LLM to select a tool based on a user need, then execute the selected MCP tool.",
        "",
        "LLM selector: local `codex exec --sandbox read-only --json`.",
        "",
        "MCP client: `fastmcp.Client` connected to the in-process `data-agent` MCP server.",
        "",
        "| Scenario | Expected | LLM selected | Selection | MCP call | Result quality |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for record in records:
        selection = "PASS" if record["selection_passed"] else "FAIL"
        call = "PASS" if record["call_passed"] else "FAIL"
        quality = "PASS" if record["result_quality_passed"] else "FAIL"
        lines.append(
            f"| `{record['name']}` | `{record['expected_tool']}` | "
            f"`{record['selected_tool']}` | {selection} | {call} | {quality} |"
        )

    lines.extend(
        [
            "",
            "## Details",
            "",
        ]
    )

    for record in records:
        lines.extend(
            [
                f"### {record['name']}",
                "",
                f"User need: {record['user_need']}",
                "",
                f"Selected tool: `{record['selected_tool']}`",
                "",
                "Arguments:",
                "",
                "```json",
                json.dumps(record["arguments"], ensure_ascii=False, indent=2),
                "```",
                "",
                "Result summary:",
                "",
                "```json",
                json.dumps(record.get("result", record.get("error")), ensure_ascii=False, indent=2, default=str)[:4000],
                "```",
                "",
            ]
        )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    records = asyncio.run(run_scenarios())
    write_report(records)
    selection_passed = sum(1 for record in records if record["selection_passed"])
    calls_passed = sum(1 for record in records if record["call_passed"])
    quality_passed = sum(1 for record in records if record["result_quality_passed"])
    print(f"selection: {selection_passed}/{len(records)}")
    print(f"calls: {calls_passed}/{len(records)}")
    print(f"result quality: {quality_passed}/{len(records)}")
    print(f"report: {REPORT_PATH}")
    print(f"json: {JSON_PATH}")


if __name__ == "__main__":
    main()
