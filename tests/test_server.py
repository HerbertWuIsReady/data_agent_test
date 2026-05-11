import shutil
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path


class DummyFastMCP:
    def __init__(self, name: str):
        self.name = name

    def tool(self, func=None):
        if func is None:
            return lambda wrapped: wrapped
        return func

    def run(self):
        return None


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.modules.setdefault("fastmcp", types.SimpleNamespace(FastMCP=DummyFastMCP))

from data_agent_mcp import server  # noqa: E402


class ServerSqlValidationTest(unittest.TestCase):
    def setUp(self):
        server.VALIDATED_SQL.clear()

    def test_normalize_sql_collapses_whitespace(self):
        self.assertEqual(
            server.normalize_sql("  SELECT\n  *\tFROM ads_user_active_metric_di  "),
            "SELECT * FROM ads_user_active_metric_di",
        )

    def test_validation_id_uses_normalized_sql(self):
        compact = "SELECT * FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"
        spaced = " SELECT   *\nFROM ads_user_active_metric_di WHERE dt = '2026-05-10' "

        self.assertEqual(server.validation_id_for(compact), server.validation_id_for(spaced))

    def test_read_only_validation_rejects_write_keyword(self):
        errors = server.validate_read_only("SELECT * FROM ads_user_active_metric_di; DROP TABLE metrics")

        self.assertIn("Only one SQL statement is allowed.", errors)
        self.assertIn("Forbidden keyword: DROP.", errors)

    def test_read_only_validation_requires_select_or_with(self):
        errors = server.validate_read_only("DELETE FROM ads_user_active_metric_di")

        self.assertIn("SQL must start with SELECT or WITH.", errors)
        self.assertIn("Forbidden keyword: DELETE.", errors)

    def test_validate_sql_accepts_partitioned_read_query(self):
        result = server.validate_sql(
            """
            SELECT country, COUNT(DISTINCT user_id) AS dau
            FROM ads_user_active_metric_di
            WHERE dt = '2026-05-10' AND is_valid_event = 1 AND is_bot = 0
            GROUP BY country
            """
        )

        self.assertTrue(result["is_valid"], result)
        self.assertIsNotNone(result["validation_id"])
        self.assertEqual([], result["errors"])
        self.assertTrue(result["explain"])

    def test_validate_sql_rejects_unknown_table(self):
        result = server.validate_sql("SELECT * FROM missing_table WHERE dt = '2026-05-10'")

        self.assertFalse(result["is_valid"])
        self.assertIn("Unknown table: missing_table.", result["errors"])

    def test_validate_sql_rejects_missing_partition_condition(self):
        result = server.validate_sql("SELECT COUNT(*) FROM ads_user_active_metric_di")

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "Missing partition condition for ads_user_active_metric_di.dt.",
            result["errors"],
        )

    def test_execute_query_rejects_mismatched_validation_id(self):
        result = server.execute_query(
            "SELECT * FROM ads_user_active_metric_di WHERE dt = '2026-05-10'",
            validation_id="not-the-current-id",
        )

        self.assertEqual("rejected", result["status"])
        self.assertEqual("validation_id does not match sql.", result["error"])

    def test_execute_query_auto_validates_and_returns_rows(self):
        result = server.execute_query(
            """
            SELECT country, COUNT(DISTINCT user_id) AS dau
            FROM ads_user_active_metric_di
            WHERE dt = '2026-05-10' AND is_valid_event = 1 AND is_bot = 0
            GROUP BY country
            ORDER BY country
            """
        )

        self.assertEqual("success", result["status"], result)
        self.assertEqual(3, result["row_count"])
        self.assertEqual(
            [
                {"country": "CN", "dau": 2},
                {"country": "SA", "dau": 1},
                {"country": "US", "dau": 1},
            ],
            result["rows"],
        )

    def test_execute_query_does_not_call_decorated_validate_tool(self):
        original_validate_sql = server.validate_sql
        try:
            server.validate_sql = object()

            result = server.execute_query(
                "SELECT COUNT(*) AS cnt FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"
            )
        finally:
            server.validate_sql = original_validate_sql

        self.assertEqual("success", result["status"], result)
        self.assertEqual([{"cnt": 5}], result["rows"])

    def test_execute_query_rejects_forbidden_write_without_running_it(self):
        result = server.execute_query(
            "UPDATE ads_user_active_metric_di SET is_bot = 1 WHERE dt = '2026-05-10'"
        )

        self.assertEqual("rejected", result["status"])
        self.assertFalse(result["validation"]["is_valid"])
        self.assertIn("SQL must start with SELECT or WITH.", result["validation"]["errors"])
        self.assertIn("Forbidden keyword: UPDATE.", result["validation"]["errors"])

    def test_validate_sql_rejects_blank_input(self):
        result = server.validate_sql("   ")

        self.assertFalse(result["is_valid"])
        self.assertIn("SQL must start with SELECT or WITH.", result["errors"])
        self.assertIn("No table found in SQL.", result["errors"])

    def test_validate_sql_allows_single_trailing_semicolon(self):
        result = server.validate_sql(
            "SELECT COUNT(*) FROM ads_user_active_metric_di WHERE dt = '2026-05-10';"
        )

        self.assertTrue(result["is_valid"], result)

    def test_validate_sql_rejects_multiple_statements(self):
        result = server.validate_sql(
            "SELECT COUNT(*) FROM ads_user_active_metric_di WHERE dt = '2026-05-10'; "
            "SELECT COUNT(*) FROM metrics"
        )

        self.assertFalse(result["is_valid"])
        self.assertIn("Only one SQL statement is allowed.", result["errors"])

    def test_validate_sql_warns_for_multi_table_query(self):
        result = server.validate_sql(
            """
            SELECT a.country, b.active_event_cnt
            FROM ads_user_active_metric_di a
            JOIN dws_user_behavior_di b ON a.user_id = b.user_id
            WHERE a.dt = '2026-05-10' AND b.dt = '2026-05-10'
            """
        )

        self.assertTrue(result["is_valid"], result)
        self.assertIn(
            "Multiple tables detected; join permission is allowed only for active metadata tables.",
            result["warnings"],
        )

    def test_repeated_validate_sql_returns_same_validation_id(self):
        sql = "SELECT COUNT(*) FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"

        first = server.validate_sql(sql)
        second = server.validate_sql(sql)

        self.assertTrue(first["is_valid"], first)
        self.assertTrue(second["is_valid"], second)
        self.assertEqual(first["validation_id"], second["validation_id"])
        self.assertEqual(sql, server.VALIDATED_SQL[first["validation_id"]])

    def test_repeated_execute_query_with_validation_id_is_stable(self):
        sql = (
            "SELECT country FROM ads_user_active_metric_di "
            "WHERE dt = '2026-05-10' ORDER BY country, user_id LIMIT 2"
        )
        validation = server.validate_sql(sql)

        first = server.execute_query(sql, validation["validation_id"])
        second = server.execute_query(sql, validation["validation_id"])

        self.assertEqual("success", first["status"])
        self.assertEqual(first, second)


class ServerLookupToolsTest(unittest.TestCase):
    def test_search_metric_returns_active_matches_first(self):
        result = server.search_metric("DAU", top_n=2)

        self.assertEqual(2, len(result["items"]))
        self.assertEqual("dau", result["items"][0]["metric_code"])

    def test_get_metric_detail_returns_single_item(self):
        result = server.get_metric_detail("日活跃用户数")

        self.assertEqual("dau", result["item"]["metric_code"])
        self.assertEqual("ads_user_active_metric_di", result["item"]["source_table"])

    def test_search_table_can_find_metric_source_table(self):
        result = server.search_table("DAU", top_n=3)
        table_names = {item["table_name"] for item in result["items"]}

        self.assertIn("ads_user_active_metric_di", table_names)

    def test_search_column_handles_natural_language_multi_token_query(self):
        result = server.search_column("country 字段 国家 DAU 分组", top_n=3)
        columns = {(item["table_name"], item["column_name"]) for item in result["items"]}

        self.assertIn(("ads_user_active_metric_di", "country"), columns)

    def test_search_table_handles_natural_language_metric_query(self):
        result = server.search_table("DAU 日活跃用户 需求 数据表", top_n=3)
        table_names = {item["table_name"] for item in result["items"]}

        self.assertIn("ads_user_active_metric_di", table_names)

    def test_search_prompt_handles_natural_language_prompt_query(self):
        result = server.search_prompt("指标趋势分析 SQL 生成规范 Prompt", top_n=3)
        prompt_names = {item["prompt_name"] for item in result["items"]}

        self.assertIn("指标趋势分析 SQL 生成规范", prompt_names)

    def test_get_table_schema_includes_columns(self):
        result = server.get_table_schema("ads_user_active_metric_di")

        self.assertEqual("ads_user_active_metric_di", result["item"]["table_name"])
        self.assertIn(
            "dt",
            {column["column_name"] for column in result["item"]["columns"]},
        )

    def test_prompt_lookup_returns_detail(self):
        result = server.get_prompt_detail("metric_trend_analysis")

        self.assertEqual("metric_trend_analysis", result["item"]["prompt_id"])

    def test_empty_lookup_query_respects_top_n(self):
        result = server.search_prompt("", top_n=3)

        self.assertEqual(3, len(result["items"]))

    def test_lookup_no_match_returns_empty_items(self):
        result = server.search_column("definitely-not-a-real-column", top_n=5)

        self.assertEqual([], result["items"])

    def test_detail_lookup_unknown_metric_returns_none(self):
        result = server.get_metric_detail("definitely-not-a-real-metric")

        self.assertIsNone(result["item"])

    def test_table_schema_unknown_table_returns_none(self):
        result = server.get_table_schema("definitely_not_a_real_table")

        self.assertIsNone(result["item"])


class ServerDatabaseFailureTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.tempdir.name)

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        server.VALIDATED_SQL.clear()
        self.tempdir.cleanup()

    def use_copied_database(self) -> Path:
        copied_db = self.temp_path / "data_agent.db"
        shutil.copy2(self.original_db_path, copied_db)
        server.DB_PATH = copied_db
        return copied_db

    def test_database_unavailable_raises_operational_error(self):
        server.DB_PATH = self.temp_path / "missing" / "data_agent.db"

        with self.assertRaises(sqlite3.OperationalError):
            server.search_metric("DAU")

    def test_validate_sql_reports_explain_failure_when_metadata_points_to_missing_table(self):
        copied_db = self.use_copied_database()
        with sqlite3.connect(copied_db) as conn:
            conn.execute("DROP TABLE ads_user_active_metric_di")

        result = server.validate_sql(
            "SELECT COUNT(*) FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"
        )

        self.assertFalse(result["is_valid"])
        self.assertTrue(
            any(error.startswith("SQLite explain failed:") for error in result["errors"]),
            result,
        )

    def test_inactive_table_metadata_rejects_query(self):
        copied_db = self.use_copied_database()
        with sqlite3.connect(copied_db) as conn:
            conn.execute(
                "UPDATE tables SET status = 'deprecated' "
                "WHERE table_name = 'ads_user_active_metric_di'"
            )

        result = server.validate_sql(
            "SELECT COUNT(*) FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"
        )

        self.assertFalse(result["is_valid"])
        self.assertIn("Table is not active: ads_user_active_metric_di.", result["errors"])

    def test_inactive_column_metadata_rejects_query(self):
        copied_db = self.use_copied_database()
        with sqlite3.connect(copied_db) as conn:
            conn.execute(
                "UPDATE columns SET status = 'deprecated' "
                "WHERE table_name = 'ads_user_active_metric_di' "
                "AND column_name = 'session_cnt'"
            )

        result = server.validate_sql(
            """
            SELECT SUM(session_cnt)
            FROM ads_user_active_metric_di
            WHERE dt = '2026-05-10'
            """
        )

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "Column is not active: ads_user_active_metric_di.session_cnt.",
            result["errors"],
        )


class DatabaseInitializerIdempotencyTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "data_agent.db"

    def tearDown(self):
        self.tempdir.cleanup()

    def test_metric_metadata_initializer_is_idempotent(self):
        import scripts.init_metric_metadata_db as init_metric_metadata_db

        original_db_path = init_metric_metadata_db.DB_PATH
        init_metric_metadata_db.DB_PATH = self.db_path
        try:
            init_metric_metadata_db.init_db()
            first_count = self.count_rows("metrics")

            init_metric_metadata_db.init_db()
            second_count = self.count_rows("metrics")
        finally:
            init_metric_metadata_db.DB_PATH = original_db_path

        self.assertEqual(first_count, second_count)
        self.assertEqual(len(init_metric_metadata_db.METRICS), second_count)

    def test_prompt_initializer_is_idempotent(self):
        import scripts.init_prompt_db as init_prompt_db

        original_db_path = init_prompt_db.DB_PATH
        init_prompt_db.DB_PATH = self.db_path
        try:
            init_prompt_db.init_db()
            first_count = self.count_rows("prompts")

            init_prompt_db.init_db()
            second_count = self.count_rows("prompts")
        finally:
            init_prompt_db.DB_PATH = original_db_path

        self.assertEqual(first_count, second_count)
        self.assertEqual(len(init_prompt_db.PROMPTS), second_count)

    def count_rows(self, table_name: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


if __name__ == "__main__":
    unittest.main()
