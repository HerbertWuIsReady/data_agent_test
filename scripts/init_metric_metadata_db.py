import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "data_agent.db"


METRICS = [
    {
        "metric_code": "dau",
        "metric_name_cn": "日活跃用户数",
        "metric_name_en": "daily_active_users",
        "aliases": "DAU、日活、活跃用户、每日活跃用户",
        "biz_domain": "user_growth",
        "definition": "统计自然日内发生过有效活跃行为的去重用户数，有效活跃行为包括 app_open、page_view、login、click、play 等非后台系统事件。",
        "formula": "COUNT(DISTINCT user_id)",
        "aggregation": "count_distinct",
        "source_table": "ads_user_active_metric_di",
        "metric_field": "user_id",
        "date_field": "dt",
        "time_grain": "day",
        "default_filters": "is_valid_event = 1 AND is_bot = 0",
        "supported_dimensions": "country、platform、channel、app_version、user_type",
        "status": "active",
        "owner": "user_growth_data_team",
        "priority": "recommended",
    },
    {
        "metric_code": "new_user_dau",
        "metric_name_cn": "新用户日活",
        "metric_name_en": "new_user_dau",
        "aliases": "新用户活跃、新客日活、新增用户活跃",
        "biz_domain": "user_growth",
        "definition": "统计自然日内注册当天即发生有效活跃行为的去重用户数，用于观察新增用户当日激活情况。",
        "formula": "COUNT(DISTINCT user_id)",
        "aggregation": "count_distinct",
        "source_table": "ads_user_active_metric_di",
        "metric_field": "user_id",
        "date_field": "dt",
        "time_grain": "day",
        "default_filters": "is_valid_event = 1 AND is_bot = 0 AND user_type = 'new'",
        "supported_dimensions": "country、platform、channel、app_version",
        "status": "active",
        "owner": "user_growth_data_team",
        "priority": "recommended",
    },
    {
        "metric_code": "returning_user_dau",
        "metric_name_cn": "老用户日活",
        "metric_name_en": "returning_user_dau",
        "aliases": "老客日活、回访用户活跃、存量用户活跃",
        "biz_domain": "user_growth",
        "definition": "统计自然日内非注册当天发生有效活跃行为的去重用户数，用于观察存量用户活跃规模。",
        "formula": "COUNT(DISTINCT user_id)",
        "aggregation": "count_distinct",
        "source_table": "ads_user_active_metric_di",
        "metric_field": "user_id",
        "date_field": "dt",
        "time_grain": "day",
        "default_filters": "is_valid_event = 1 AND is_bot = 0 AND user_type = 'returning'",
        "supported_dimensions": "country、platform、channel、app_version",
        "status": "active",
        "owner": "user_growth_data_team",
        "priority": "normal",
    },
    {
        "metric_code": "dau_session_cnt",
        "metric_name_cn": "日活用户会话数",
        "metric_name_en": "dau_session_count",
        "aliases": "活跃会话数、DAU会话、session数",
        "biz_domain": "user_growth",
        "definition": "统计自然日内活跃用户产生的有效会话数量，用于衡量活跃用户访问频次。",
        "formula": "SUM(session_cnt)",
        "aggregation": "sum",
        "source_table": "ads_user_active_metric_di",
        "metric_field": "session_cnt",
        "date_field": "dt",
        "time_grain": "day",
        "default_filters": "is_valid_event = 1 AND is_bot = 0",
        "supported_dimensions": "country、platform、channel、app_version、user_type",
        "status": "active",
        "owner": "user_growth_data_team",
        "priority": "normal",
    },
    {
        "metric_code": "avg_dau_session_duration",
        "metric_name_cn": "日活人均会话时长",
        "metric_name_en": "avg_dau_session_duration",
        "aliases": "人均访问时长、DAU平均会话时长、活跃用户时长",
        "biz_domain": "user_growth",
        "definition": "统计自然日内活跃用户的总会话时长除以活跃用户数，用于衡量活跃用户使用深度。",
        "formula": "SUM(session_duration_sec) / COUNT(DISTINCT user_id)",
        "aggregation": "ratio",
        "source_table": "ads_user_active_metric_di",
        "metric_field": "session_duration_sec",
        "date_field": "dt",
        "time_grain": "day",
        "default_filters": "is_valid_event = 1 AND is_bot = 0",
        "supported_dimensions": "country、platform、channel、app_version、user_type",
        "status": "active",
        "owner": "user_growth_data_team",
        "priority": "normal",
    },
]


TABLES = [
    {
        "table_name": "ads_user_active_metric_di",
        "table_comment": "用户活跃指标日汇总表，按天、国家、平台、渠道、版本和用户类型沉淀 DAU 相关指标。",
        "biz_domain": "user_growth",
        "layer": "ads",
        "table_grain": "dt + country + platform + channel + app_version + user_type",
        "partition_field": "dt",
        "time_field": "dt",
        "update_frequency": "daily",
        "data_latency": "T+1",
        "owner": "user_growth_data_team",
        "status": "active",
        "recommended_usage": "用于 DAU、新用户日活、老用户日活、活跃会话数、人均会话时长等活跃类指标问数。",
        "forbidden_usage": "不用于事件明细追踪、用户级行为路径分析或实时活跃监控。",
    },
    {
        "table_name": "dws_user_behavior_di",
        "table_comment": "用户行为日宽表，按用户和日期聚合登录、访问、点击、播放等行为事实。",
        "biz_domain": "user_growth",
        "layer": "dws",
        "table_grain": "dt + user_id",
        "partition_field": "dt",
        "time_field": "event_date",
        "update_frequency": "daily",
        "data_latency": "T+1",
        "owner": "user_growth_data_team",
        "status": "active",
        "recommended_usage": "用于 DAU 口径追溯、用户行为过滤、用户维度去重和活跃明细抽样。",
        "forbidden_usage": "不用于直接替代 ADS 层指标口径对外出数。",
    },
    {
        "table_name": "dwd_user_event_di",
        "table_comment": "用户事件明细表，保存清洗后的客户端和服务端行为事件。",
        "biz_domain": "user_growth",
        "layer": "dwd",
        "table_grain": "dt + event_id",
        "partition_field": "dt",
        "time_field": "event_time",
        "update_frequency": "daily",
        "data_latency": "T+1",
        "owner": "user_growth_data_team",
        "status": "active",
        "recommended_usage": "用于排查 DAU 异常、核对事件明细、确认行为类型过滤条件。",
        "forbidden_usage": "不建议直接用于高频聚合问数，避免扫描明细成本过高。",
    },
]


COLUMNS = [
    ("ads_user_active_metric_di", "dt", "date", "统计日期，也是分区字段", "time", 0, 1, 1, 1, "", "2026-05-10", 0.0, "active"),
    ("ads_user_active_metric_di", "country", "varchar(64)", "用户注册或访问国家", "dimension", 0, 1, 1, 1, "", "CN、US、SA", 0.01, "active"),
    ("ads_user_active_metric_di", "platform", "varchar(32)", "访问平台", "dimension", 0, 1, 1, 1, "", "iOS、Android、Web", 0.0, "active"),
    ("ads_user_active_metric_di", "channel", "varchar(64)", "获客渠道", "dimension", 0, 1, 1, 1, "", "organic、ads、referral", 0.08, "active"),
    ("ads_user_active_metric_di", "app_version", "varchar(32)", "客户端版本", "dimension", 0, 1, 1, 1, "", "5.1.0、5.2.0", 0.03, "active"),
    ("ads_user_active_metric_di", "user_type", "varchar(32)", "用户类型，新用户或老用户", "dimension", 0, 1, 1, 1, "", "new、returning", 0.0, "active"),
    ("ads_user_active_metric_di", "user_id", "varchar(128)", "用户唯一标识，用于 DAU 去重", "metric", 1, 0, 1, 0, "count_distinct", "u_10001", 0.0, "active"),
    ("ads_user_active_metric_di", "session_cnt", "bigint", "用户有效会话次数", "metric", 1, 0, 1, 0, "sum、avg", "1、3、8", 0.0, "active"),
    ("ads_user_active_metric_di", "session_duration_sec", "bigint", "用户有效会话总时长，单位秒", "metric", 1, 0, 1, 0, "sum、avg", "30、180、900", 0.0, "active"),
    ("ads_user_active_metric_di", "is_valid_event", "tinyint", "是否有效活跃行为标记", "flag", 0, 0, 1, 0, "", "0、1", 0.0, "active"),
    ("ads_user_active_metric_di", "is_bot", "tinyint", "是否疑似机器或爬虫流量", "flag", 0, 0, 1, 0, "", "0、1", 0.0, "active"),
    ("dws_user_behavior_di", "dt", "date", "统计日期，分区字段", "time", 0, 1, 1, 1, "", "2026-05-10", 0.0, "active"),
    ("dws_user_behavior_di", "user_id", "varchar(128)", "用户唯一标识", "dimension", 0, 1, 1, 1, "count_distinct", "u_10001", 0.0, "active"),
    ("dws_user_behavior_di", "active_event_cnt", "bigint", "有效活跃事件次数", "metric", 1, 0, 1, 0, "sum、avg", "1、5、20", 0.0, "active"),
    ("dwd_user_event_di", "event_time", "datetime", "事件发生时间", "time", 0, 1, 1, 0, "", "2026-05-10 12:30:00", 0.0, "active"),
    ("dwd_user_event_di", "event_name", "varchar(128)", "事件名称", "dimension", 0, 1, 1, 1, "", "app_open、page_view、login", 0.0, "active"),
    ("dwd_user_event_di", "event_id", "varchar(128)", "事件唯一标识", "dimension", 0, 0, 1, 0, "count", "evt_90001", 0.0, "active"),
]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                metric_code TEXT PRIMARY KEY,
                metric_name_cn TEXT NOT NULL,
                metric_name_en TEXT NOT NULL,
                aliases TEXT NOT NULL,
                biz_domain TEXT NOT NULL,
                definition TEXT NOT NULL,
                formula TEXT NOT NULL,
                aggregation TEXT NOT NULL,
                source_table TEXT NOT NULL,
                metric_field TEXT NOT NULL,
                date_field TEXT NOT NULL,
                time_grain TEXT NOT NULL,
                default_filters TEXT NOT NULL,
                supported_dimensions TEXT NOT NULL,
                status TEXT NOT NULL,
                owner TEXT NOT NULL,
                priority TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tables (
                table_name TEXT PRIMARY KEY,
                table_comment TEXT NOT NULL,
                biz_domain TEXT NOT NULL,
                layer TEXT NOT NULL,
                table_grain TEXT NOT NULL,
                partition_field TEXT NOT NULL,
                time_field TEXT NOT NULL,
                update_frequency TEXT NOT NULL,
                data_latency TEXT NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL,
                recommended_usage TEXT NOT NULL,
                forbidden_usage TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS columns (
                table_name TEXT NOT NULL,
                column_name TEXT NOT NULL,
                column_type TEXT NOT NULL,
                column_comment TEXT NOT NULL,
                semantic_type TEXT NOT NULL,
                is_metric INTEGER NOT NULL,
                is_dimension INTEGER NOT NULL,
                is_filterable INTEGER NOT NULL,
                is_groupable INTEGER NOT NULL,
                aggregation_methods TEXT NOT NULL,
                sample_values TEXT NOT NULL,
                null_rate REAL NOT NULL,
                status TEXT NOT NULL,
                PRIMARY KEY (table_name, column_name)
            )
            """
        )

        conn.execute("DELETE FROM metrics")
        conn.execute("DELETE FROM tables")
        conn.execute("DELETE FROM columns")

        conn.executemany(
            """
            INSERT INTO metrics (
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
            )
            VALUES (
                :metric_code,
                :metric_name_cn,
                :metric_name_en,
                :aliases,
                :biz_domain,
                :definition,
                :formula,
                :aggregation,
                :source_table,
                :metric_field,
                :date_field,
                :time_grain,
                :default_filters,
                :supported_dimensions,
                :status,
                :owner,
                :priority
            )
            """,
            METRICS,
        )
        conn.executemany(
            """
            INSERT INTO tables (
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
            )
            VALUES (
                :table_name,
                :table_comment,
                :biz_domain,
                :layer,
                :table_grain,
                :partition_field,
                :time_field,
                :update_frequency,
                :data_latency,
                :owner,
                :status,
                :recommended_usage,
                :forbidden_usage
            )
            """,
            TABLES,
        )
        conn.executemany(
            """
            INSERT INTO columns (
                table_name,
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
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            COLUMNS,
        )

        conn.execute("DROP TABLE IF EXISTS ads_user_active_metric_di")
        conn.execute(
            """
            CREATE TABLE ads_user_active_metric_di (
                dt TEXT NOT NULL,
                country TEXT,
                platform TEXT,
                channel TEXT,
                app_version TEXT,
                user_type TEXT,
                user_id TEXT NOT NULL,
                session_cnt INTEGER,
                session_duration_sec INTEGER,
                is_valid_event INTEGER,
                is_bot INTEGER
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO ads_user_active_metric_di (
                dt,
                country,
                platform,
                channel,
                app_version,
                user_type,
                user_id,
                session_cnt,
                session_duration_sec,
                is_valid_event,
                is_bot
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("2026-05-09", "CN", "iOS", "organic", "5.2.0", "new", "u_10001", 2, 360, 1, 0),
                ("2026-05-09", "CN", "Android", "ads", "5.2.0", "returning", "u_10002", 4, 920, 1, 0),
                ("2026-05-09", "US", "iOS", "referral", "5.1.0", "returning", "u_10003", 1, 120, 1, 0),
                ("2026-05-10", "CN", "iOS", "organic", "5.2.0", "returning", "u_10001", 3, 540, 1, 0),
                ("2026-05-10", "CN", "Android", "ads", "5.2.0", "new", "u_10004", 1, 90, 1, 0),
                ("2026-05-10", "SA", "Android", "ads", "5.1.0", "returning", "u_10005", 5, 1500, 1, 0),
                ("2026-05-10", "US", "Web", "organic", "5.1.0", "returning", "u_10006", 1, 60, 1, 0),
                ("2026-05-10", "US", "Web", "organic", "5.1.0", "returning", "u_bot_01", 9, 30, 1, 1),
            ],
        )

        conn.execute("DROP TABLE IF EXISTS dws_user_behavior_di")
        conn.execute(
            """
            CREATE TABLE dws_user_behavior_di (
                dt TEXT NOT NULL,
                event_date TEXT,
                user_id TEXT NOT NULL,
                active_event_cnt INTEGER
            )
            """
        )
        conn.executemany(
            "INSERT INTO dws_user_behavior_di VALUES (?, ?, ?, ?)",
            [
                ("2026-05-09", "2026-05-09", "u_10001", 6),
                ("2026-05-09", "2026-05-09", "u_10002", 12),
                ("2026-05-10", "2026-05-10", "u_10001", 8),
                ("2026-05-10", "2026-05-10", "u_10004", 3),
            ],
        )

        conn.execute("DROP TABLE IF EXISTS dwd_user_event_di")
        conn.execute(
            """
            CREATE TABLE dwd_user_event_di (
                dt TEXT NOT NULL,
                event_time TEXT,
                event_name TEXT,
                event_id TEXT,
                user_id TEXT
            )
            """
        )
        conn.executemany(
            "INSERT INTO dwd_user_event_di VALUES (?, ?, ?, ?, ?)",
            [
                ("2026-05-10", "2026-05-10 09:00:00", "app_open", "evt_90001", "u_10001"),
                ("2026-05-10", "2026-05-10 09:02:00", "page_view", "evt_90002", "u_10001"),
                ("2026-05-10", "2026-05-10 10:10:00", "login", "evt_90003", "u_10004"),
            ],
        )


if __name__ == "__main__":
    init_db()
    print(f"initialized metric metadata in {DB_PATH}")
