import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "data_agent.db"


PROMPTS = [
    {
        "prompt_id": "metric_trend_analysis",
        "prompt_name": "指标趋势分析 SQL 生成规范",
        "prompt_desc": "用于用户询问某个业务指标在日、周、月等时间粒度上的变化趋势时，指导模型识别指标口径、时间范围、分区过滤、聚合粒度和排序方式，生成可解释且符合只读规范的查询 SQL。",
        "prompt_param": "metric_name: 指标名称; time_range: 时间范围; time_grain: 时间粒度; dimensions: 可选分组维度; auto_load_metric: 否",
        "prompt_body": "先召回指标定义，再召回候选表和字段，确认时间字段与分区字段，生成 SELECT 聚合查询；必须包含时间范围条件和必要分区条件；结果按时间升序返回。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_compare_analysis",
        "prompt_name": "指标对比分析 SQL 生成规范",
        "prompt_desc": "用于对比两个时间段、两个业务对象或多个维度下同一指标差异的场景，帮助模型生成包含基准值、对比值、差值和变化率的 SQL。",
        "prompt_param": "metric_name: 指标名称; compare_type: 时间对比或维度对比; base_range: 基准范围; compare_range: 对比范围; auto_load_metric: 否",
        "prompt_body": "分别构造基准集合和对比集合，使用公共维度关联，输出 base_value、compare_value、diff_value、diff_rate；除数为零时需要安全处理。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_rank_analysis",
        "prompt_name": "指标排行分析 SQL 生成规范",
        "prompt_desc": "用于生成按城市、门店、商品、渠道、用户分层等维度统计指标排名的 SQL，适合 TopN、BottomN、榜单和贡献排序问题。",
        "prompt_param": "metric_name: 指标名称; rank_dimension: 排名维度; top_n: 返回条数; order_type: asc 或 desc; auto_load_metric: 否",
        "prompt_body": "确认指标聚合表达式和排名维度字段，生成 GROUP BY 查询，按指标值排序并限制条数；必须校验维度字段属于目标表。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_drilldown_analysis",
        "prompt_name": "指标下钻分析 SQL 生成规范",
        "prompt_desc": "用于用户发现指标异常后，希望按业务维度继续拆解原因的场景，指导模型从总量指标下钻到区域、渠道、品类、人群等候选维度。",
        "prompt_param": "metric_name: 指标名称; drill_dimensions: 下钻维度列表; time_range: 时间范围; auto_load_metric: 否",
        "prompt_body": "先计算整体指标，再按候选维度分组计算指标和占比；优先选择指标定义中推荐的维度字段；返回维度值、指标值、占比和排序。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_anomaly_check",
        "prompt_name": "指标异常排查 SQL 生成规范",
        "prompt_desc": "用于用户询问指标为何突然升高、降低、波动或异常时，指导模型生成对比历史均值、环比、同比、分维度贡献的 SQL。",
        "prompt_param": "metric_name: 指标名称; abnormal_date: 异常日期; baseline_days: 基线天数; dimensions: 可选排查维度; auto_load_metric: 否",
        "prompt_body": "生成异常日指标与历史基线指标的对比查询，必要时按维度拆解贡献；避免写入操作；必须显式过滤异常日期和基线日期范围。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_funnel_analysis",
        "prompt_name": "漏斗指标 SQL 生成规范",
        "prompt_desc": "用于注册、访问、下单、支付、留存等多步骤业务流程的转化率分析，指导模型按步骤生成去重人数、转化率和步骤流失率 SQL。",
        "prompt_param": "funnel_steps: 漏斗步骤; user_key: 用户标识字段; time_range: 时间范围; group_dimension: 可选分组维度; auto_load_metric: 否",
        "prompt_body": "每个步骤生成独立子查询或条件聚合，统一用户口径，输出 step_user_count、conversion_rate、drop_rate；必须检查步骤事件字段和时间字段合法。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_retention_analysis",
        "prompt_name": "留存指标 SQL 生成规范",
        "prompt_desc": "用于分析新增用户、活跃用户、付费用户等群体在次日、7日、30日等周期的留存情况，指导模型生成 cohort 留存 SQL。",
        "prompt_param": "base_event: 起始事件; return_event: 回访事件; cohort_range: cohort 时间范围; retention_days: 留存天数列表; auto_load_metric: 否",
        "prompt_body": "构造 cohort 用户集合和回访用户集合，按 cohort_date 聚合，输出 base_users、retained_users、retention_rate；日期差计算必须使用统一时间字段。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_dimension_distribution",
        "prompt_name": "指标维度分布 SQL 生成规范",
        "prompt_desc": "用于用户询问指标在不同维度取值上的分布、占比、结构变化时，指导模型生成分组统计、占比计算和累计占比 SQL。",
        "prompt_param": "metric_name: 指标名称; dimension: 分布维度; time_range: 时间范围; include_ratio: 是否计算占比; auto_load_metric: 否",
        "prompt_body": "按目标维度聚合指标值，并使用窗口函数计算总量占比；维度为空值时需要归类为 unknown 或按规范过滤。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_detail_sample",
        "prompt_name": "指标明细样本 SQL 生成规范",
        "prompt_desc": "用于用户需要查看指标背后的明细记录、抽样数据或异常样本时，指导模型生成受限字段、受限条数、只读的明细查询 SQL。",
        "prompt_param": "metric_name: 指标名称; filters: 过滤条件; sample_limit: 样本条数; selected_columns: 明细字段; auto_load_metric: 否",
        "prompt_body": "只选择必要字段，必须包含 LIMIT，禁止 SELECT *，禁止返回敏感字段；过滤条件必须来自已校验字段。",
        "onwer": "wuxuan",
    },
    {
        "prompt_id": "metric_sql_validation_repair",
        "prompt_name": "指标 SQL 校验修复规范",
        "prompt_desc": "用于 validate_sql 返回字段不存在、表不存在、权限不足、缺少分区条件或非只读 SQL 时，指导模型根据错误信息修复 SQL。",
        "prompt_param": "sql: 待修复 SQL; validation_errors: 校验错误列表; available_schema: 可用表结构; auto_load_metric: 否",
        "prompt_body": "逐项读取校验错误，优先修正表名、字段名和分区条件；不得绕过权限校验；修复后必须再次调用 validate_sql。",
        "onwer": "wuxuan",
    },
]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prompts (
                prompt_id TEXT PRIMARY KEY,
                prompt_name TEXT NOT NULL,
                prompt_desc TEXT NOT NULL,
                prompt_param TEXT NOT NULL,
                prompt_body TEXT NOT NULL,
                onwer TEXT NOT NULL
            )
            """
        )
        conn.execute("DELETE FROM prompts")
        conn.executemany(
            """
            INSERT INTO prompts (
                prompt_id,
                prompt_name,
                prompt_desc,
                prompt_param,
                prompt_body,
                onwer
            )
            VALUES (
                :prompt_id,
                :prompt_name,
                :prompt_desc,
                :prompt_param,
                :prompt_body,
                :onwer
            )
            """,
            PROMPTS,
        )


if __name__ == "__main__":
    init_db()
    print(f"initialized {DB_PATH}")
