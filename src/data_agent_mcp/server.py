import hashlib
import re
import sqlite3
from pathlib import Path

from fastmcp import FastMCP


mcp = FastMCP("data-agent")
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "data_agent.db"
VALIDATED_SQL: dict[str, str] = {}
LOOKUP_STOPWORDS = {
    "prompt",
    "topn",
    "sql",
    "字段",
    "数据表",
    "需求",
    "相关",
    "信息",
    "一下",
    "哪些",
    "使用",
    "先找",
    "分析",
}


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()

    return [dict(row) for row in rows]


def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, params).fetchone()

    if row is None:
        return None

    return dict(row)


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip())


def validation_id_for(sql: str) -> str:
    return hashlib.sha256(normalize_sql(sql).encode("utf-8")).hexdigest()[:16]


def lookup_tokens(query: str) -> list[str]:
    tokens = [
        token.strip().lower()
        for token in re.split(r"[\s,，。；;:：、/\\|()\[\]{}<>!?！？]+", query)
        if token.strip()
    ]
    filtered = [token for token in tokens if token not in LOOKUP_STOPWORDS]
    return list(dict.fromkeys(filtered or tokens))


def score_text_fields(row: dict, tokens: list[str], weighted_fields: list[tuple[str, int]]) -> int:
    score = 0
    for token in tokens:
        for field, weight in weighted_fields:
            value = str(row.get(field) or "").lower()
            if value == token:
                score += weight * 3
            elif token in value:
                score += weight
    return score


def rank_rows(rows: list[dict], query: str, weighted_fields: list[tuple[str, int]], top_n: int) -> list[dict]:
    tokens = lookup_tokens(query)
    scored = [
        (score_text_fields(row, tokens, weighted_fields), index, row)
        for index, row in enumerate(rows)
    ]
    return [row for score, _, row in sorted(scored, key=lambda item: (-item[0], item[1])) if score > 0][:top_n]


def extract_table_names(sql: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", sql, re.IGNORECASE)))


def validate_read_only(sql: str) -> list[str]:
    normalized = normalize_sql(sql)
    errors = []

    if not re.match(r"^(SELECT|WITH)\b", normalized, re.IGNORECASE):
        errors.append("SQL must start with SELECT or WITH.")

    if ";" in normalized.rstrip(";"):
        errors.append("Only one SQL statement is allowed.")

    forbidden = re.search(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|MERGE|GRANT|REVOKE|CALL|LOAD|EXPORT)\b",
        normalized,
        re.IGNORECASE,
    )
    if forbidden:
        errors.append(f"Forbidden keyword: {forbidden.group(1).upper()}.")

    return errors


def validate_metadata(sql: str) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    table_names = extract_table_names(sql)

    if not table_names:
        errors.append("No table found in SQL.")
        return errors, warnings

    for table_name in table_names:
        table = fetch_one(
            "SELECT table_name, status, partition_field FROM tables WHERE table_name = ?",
            (table_name,),
        )
        if table is None:
            errors.append(f"Unknown table: {table_name}.")
            continue
        if table["status"] != "active":
            errors.append(f"Table is not active: {table_name}.")

        partition_field = table["partition_field"]
        if not re.search(rf"\b{re.escape(partition_field)}\b", sql, re.IGNORECASE):
            errors.append(f"Missing partition condition for {table_name}.{partition_field}.")

        inactive_columns = fetch_all(
            "SELECT column_name FROM columns WHERE table_name = ? AND status != 'active'",
            (table_name,),
        )
        for column in inactive_columns:
            if re.search(rf"\b{re.escape(column['column_name'])}\b", sql, re.IGNORECASE):
                errors.append(f"Column is not active: {table_name}.{column['column_name']}.")

    if len(table_names) > 1:
        warnings.append("Multiple tables detected; join permission is allowed only for active metadata tables.")

    return errors, warnings


@mcp.tool
def search_prompt(query: str, top_n: int = 10) -> dict:
    """全量召回 Prompt / TopN，支持用户自然语言多关键词查询."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT prompt_id, prompt_name, prompt_desc
            FROM prompts
            ORDER BY prompt_id
            """,
        ).fetchall()

    items = rank_rows(
        [dict(row) for row in rows],
        query,
        [
            ("prompt_id", 8),
            ("prompt_name", 6),
            ("prompt_desc", 3),
        ],
        top_n,
    )
    if not query.strip():
        items = [dict(row) for row in rows][:top_n]

    return {"items": items}


@mcp.tool
def get_prompt_detail(prompt_name: str) -> dict:
    """只取命中的 Prompt 流程定义."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT
                prompt_id,
                prompt_name,
                prompt_desc,
                prompt_param,
                prompt_body,
                onwer
            FROM prompts
            WHERE prompt_name = ? OR prompt_id = ?
            LIMIT 1
            """,
            (prompt_name, prompt_name),
        ).fetchone()

    if row is None:
        return {"item": None}

    return {"item": dict(row)}


@mcp.tool
def search_metric(query: str, top_n: int = 10) -> dict:
    """指标全量召回 / 候选召回，支持指标名、别名和自然语言多关键词查询."""
    rows = fetch_all(
        """
        SELECT
            metric_code,
            metric_name_cn,
            metric_name_en,
            aliases,
            biz_domain,
            definition,
            source_table,
            priority
        FROM metrics
        WHERE status = 'active'
        ORDER BY
            CASE priority WHEN 'recommended' THEN 0 ELSE 1 END,
            metric_code
        """,
    )

    items = rank_rows(
        rows,
        query,
        [
            ("metric_code", 10),
            ("metric_name_cn", 9),
            ("metric_name_en", 9),
            ("aliases", 8),
            ("definition", 3),
            ("biz_domain", 1),
        ],
        top_n,
    )
    if not query.strip():
        items = rows[:top_n]

    return {"items": items}


@mcp.tool
def get_metric_detail(metric_name: str) -> dict:
    """只取命中的指标定义."""
    row = fetch_one(
        """
        SELECT
            metric_code,
            metric_name_cn,
            metric_name_en,
            aliases,
            biz_domain,
            definition,
            formula,
            aggregation,
            source_table,
            metric_field,
            date_field,
            time_grain,
            default_filters,
            supported_dimensions,
            status,
            owner,
            priority
        FROM metrics
        WHERE metric_code = ?
           OR metric_name_cn = ?
           OR metric_name_en = ?
           OR aliases LIKE ?
        LIMIT 1
        """,
        (metric_name, metric_name, metric_name, f"%{metric_name}%"),
    )

    return {"item": row}


@mcp.tool
def search_column(query: str, top_n: int = 10) -> dict:
    """召回候选字段，辅助 SQL 字段选择，支持字段名、中文语义、指标名混合查询."""
    rows = fetch_all(
        """
        SELECT
            c.table_name,
            c.column_name,
            c.column_type,
            c.column_comment,
            c.semantic_type,
            c.is_metric,
            c.is_dimension,
            c.is_filterable,
            c.is_groupable,
            c.aggregation_methods,
            c.sample_values,
            c.null_rate,
            COALESCE(m.metric_code, '') AS metric_code,
            COALESCE(m.metric_name_cn, '') AS metric_name_cn,
            COALESCE(m.metric_name_en, '') AS metric_name_en,
            COALESCE(m.aliases, '') AS metric_aliases,
            COALESCE(m.supported_dimensions, '') AS supported_dimensions
        FROM columns c
        LEFT JOIN metrics m
          ON m.source_table = c.table_name
         AND m.status = 'active'
        WHERE c.status = 'active'
        ORDER BY c.table_name, c.column_name, m.metric_code
        """,
    )

    matched = rank_rows(
        rows,
        query,
        [
            ("column_name", 12),
            ("column_comment", 10),
            ("sample_values", 5),
            ("semantic_type", 4),
            ("table_name", 3),
            ("supported_dimensions", 3),
            ("metric_code", 2),
            ("metric_name_cn", 2),
            ("metric_name_en", 2),
            ("metric_aliases", 2),
        ],
        len(rows),
    )
    deduped = []
    seen = set()
    for row in matched:
        key = (row["table_name"], row["column_name"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            {
                key: value
                for key, value in row.items()
                if key
                not in {
                    "metric_code",
                    "metric_name_cn",
                    "metric_name_en",
                    "metric_aliases",
                    "supported_dimensions",
                }
            }
        )

    return {"items": deduped[:top_n]}


@mcp.tool
def search_table(query: str, top_n: int = 10) -> dict:
    """根据指标或业务语义召回候选 Doris 表，支持自然语言多关键词查询."""
    rows = fetch_all(
        """
        SELECT DISTINCT
            t.table_name,
            t.table_comment,
            t.biz_domain,
            t.layer,
            t.table_grain,
            t.partition_field,
            t.time_field,
            t.update_frequency,
            t.data_latency,
            t.recommended_usage,
            t.forbidden_usage,
            COALESCE(m.metric_code, '') AS metric_code,
            COALESCE(m.metric_name_cn, '') AS metric_name_cn,
            COALESCE(m.metric_name_en, '') AS metric_name_en,
            COALESCE(m.aliases, '') AS metric_aliases,
            COALESCE(m.definition, '') AS metric_definition
        FROM tables t
        LEFT JOIN metrics m ON m.source_table = t.table_name
        WHERE t.status = 'active'
        ORDER BY
            CASE t.layer WHEN 'ads' THEN 0 WHEN 'dws' THEN 1 ELSE 2 END,
            t.table_name,
            m.metric_code
        """,
    )

    matched = rank_rows(
        rows,
        query,
        [
            ("table_name", 10),
            ("table_comment", 8),
            ("recommended_usage", 7),
            ("metric_code", 6),
            ("metric_name_cn", 6),
            ("metric_name_en", 6),
            ("metric_aliases", 6),
            ("metric_definition", 3),
            ("biz_domain", 2),
        ],
        len(rows),
    )
    deduped = []
    seen = set()
    for row in matched:
        if row["table_name"] in seen:
            continue
        seen.add(row["table_name"])
        deduped.append(
            {
                key: value
                for key, value in row.items()
                if key
                not in {
                    "metric_code",
                    "metric_name_cn",
                    "metric_name_en",
                    "metric_aliases",
                    "metric_definition",
                }
            }
        )

    return {"items": deduped[:top_n]}


@mcp.tool
def get_table_schema(table_name: str) -> dict:
    """获取表字段、类型、注释、分区字段."""
    table = fetch_one(
        """
        SELECT
            table_name,
            table_comment,
            biz_domain,
            layer,
            table_grain,
            partition_field,
            time_field,
            update_frequency,
            data_latency,
            owner,
            status,
            recommended_usage,
            forbidden_usage
        FROM tables
        WHERE table_name = ?
        LIMIT 1
        """,
        (table_name,),
    )
    if table is None:
        return {"item": None}

    columns = fetch_all(
        """
        SELECT
            column_name,
            column_type,
            column_comment,
            semantic_type,
            is_metric,
            is_dimension,
            is_filterable,
            is_groupable,
            aggregation_methods,
            sample_values,
            null_rate,
            status
        FROM columns
        WHERE table_name = ?
        ORDER BY
            CASE semantic_type
                WHEN 'time' THEN 0
                WHEN 'dimension' THEN 1
                WHEN 'metric' THEN 2
                WHEN 'flag' THEN 3
                ELSE 4
            END,
            column_name
        """,
        (table_name,),
    )

    return {"item": {**table, "columns": columns}}


def _validate_sql(sql: str) -> dict:
    normalized = normalize_sql(sql)
    errors = validate_read_only(normalized)
    metadata_errors, warnings = validate_metadata(normalized)
    errors.extend(metadata_errors)

    explain_rows = []
    if not errors:
        try:
            explain_rows = fetch_all(f"EXPLAIN QUERY PLAN {normalized}")
        except sqlite3.Error as exc:
            errors.append(f"SQLite explain failed: {exc}")

    is_valid = len(errors) == 0
    current_validation_id = validation_id_for(normalized)
    if is_valid:
        VALIDATED_SQL[current_validation_id] = normalized

    return {
        "is_valid": is_valid,
        "validation_id": current_validation_id if is_valid else None,
        "errors": errors,
        "warnings": warnings,
        "explain": explain_rows,
    }


def _execute_query(sql: str, validation_id: str | None = None) -> dict:
    normalized = normalize_sql(sql)
    current_validation_id = validation_id_for(normalized)

    if validation_id is not None and validation_id != current_validation_id:
        return {
            "status": "rejected",
            "error": "validation_id does not match sql.",
        }

    if VALIDATED_SQL.get(current_validation_id) != normalized:
        validation = _validate_sql(normalized)
        if not validation["is_valid"]:
            return {
                "status": "rejected",
                "validation": validation,
            }

    rows = fetch_all(normalized)
    return {
        "status": "success",
        "validation_id": current_validation_id,
        "row_count": len(rows),
        "rows": rows,
    }


@mcp.tool
def validate_sql(sql: str) -> dict:
    """校验 SQL 并返回 explain 后的信息."""
    return _validate_sql(sql)


@mcp.tool
def execute_query(sql: str, validation_id: str | None = None) -> dict:
    """只执行通过校验的 SQL."""
    return _execute_query(sql, validation_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
