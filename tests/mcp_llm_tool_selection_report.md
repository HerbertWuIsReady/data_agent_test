# MCP LLM Tool Selection Report

Test date: 2026-05-11 13:05:35

Goal: verify that a client can discover MCP tools, ask an LLM to select a tool based on a user need, then execute the selected MCP tool.

LLM selector: local `codex exec --sandbox read-only --json`.

MCP client: `fastmcp.Client` connected to the in-process `data-agent` MCP server.

| Scenario | Expected | LLM selected | Selection | MCP call | Result quality |
| --- | --- | --- | --- | --- | --- |
| `metric_candidate_search` | `search_metric` | `search_metric` | PASS | PASS | PASS |
| `metric_detail_lookup` | `get_metric_detail` | `get_metric_detail` | PASS | PASS | PASS |
| `column_lookup` | `search_column` | `search_column` | PASS | PASS | PASS |
| `table_lookup` | `search_table` | `search_table` | PASS | PASS | PASS |
| `schema_lookup` | `get_table_schema` | `get_table_schema` | PASS | PASS | PASS |
| `sql_validation` | `validate_sql` | `validate_sql` | PASS | PASS | PASS |
| `query_execution` | `execute_query` | `execute_query` | PASS | PASS | PASS |
| `prompt_search` | `search_prompt` | `search_prompt` | PASS | PASS | PASS |

## Details

### metric_candidate_search

User need: 我想找 DAU 这个指标，先帮我召回候选指标。

Selected tool: `search_metric`

Arguments:

```json
{
  "query": "DAU",
  "top_n": 3
}
```

Result summary:

```json
{
  "items": [
    {
      "metric_code": "dau",
      "metric_name_cn": "日活跃用户数",
      "metric_name_en": "daily_active_users",
      "aliases": "DAU、日活、活跃用户、每日活跃用户",
      "biz_domain": "user_growth",
      "definition": "统计自然日内发生过有效活跃行为的去重用户数，有效活跃行为包括 app_open、page_view、login、click、play 等非后台系统事件。",
      "source_table": "ads_user_active_metric_di",
      "priority": "recommended"
    },
    {
      "metric_code": "avg_dau_session_duration",
      "metric_name_cn": "日活人均会话时长",
      "metric_name_en": "avg_dau_session_duration",
      "aliases": "人均访问时长、DAU平均会话时长、活跃用户时长",
      "biz_domain": "user_growth",
      "definition": "统计自然日内活跃用户的总会话时长除以活跃用户数，用于衡量活跃用户使用深度。",
      "source_table": "ads_user_active_metric_di",
      "priority": "normal"
    },
    {
      "metric_code": "dau_session_cnt",
      "metric_name_cn": "日活用户会话数",
      "metric_name_en": "dau_session_count",
      "aliases": "活跃会话数、DAU会话、session数",
      "biz_domain": "user_growth",
      "definition": "统计自然日内活跃用户产生的有效会话数量，用于衡量活跃用户访问频次。",
      "source_table": "ads_user_active_metric_di",
      "priority": "normal"
    }
  ]
}
```

### metric_detail_lookup

User need: 请查看日活跃用户数的完整指标口径、公式和来源表。

Selected tool: `get_metric_detail`

Arguments:

```json
{
  "metric_name": "日活跃用户数"
}
```

Result summary:

```json
{
  "item": {
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
    "priority": "recommended"
  }
}
```

### column_lookup

User need: 我要按国家分组分析 DAU，请先找 country 字段信息。

Selected tool: `search_column`

Arguments:

```json
{
  "query": "country 国家 DAU 按国家分组",
  "top_n": 3
}
```

Result summary:

```json
{
  "items": [
    {
      "table_name": "ads_user_active_metric_di",
      "column_name": "country",
      "column_type": "varchar(64)",
      "column_comment": "用户注册或访问国家",
      "semantic_type": "dimension",
      "is_metric": 0,
      "is_dimension": 1,
      "is_filterable": 1,
      "is_groupable": 1,
      "aggregation_methods": "",
      "sample_values": "CN、US、SA",
      "null_rate": 0.01
    },
    {
      "table_name": "ads_user_active_metric_di",
      "column_name": "user_id",
      "column_type": "varchar(128)",
      "column_comment": "用户唯一标识，用于 DAU 去重",
      "semantic_type": "metric",
      "is_metric": 1,
      "is_dimension": 0,
      "is_filterable": 1,
      "is_groupable": 0,
      "aggregation_methods": "count_distinct",
      "sample_values": "u_10001",
      "null_rate": 0.0
    },
    {
      "table_name": "ads_user_active_metric_di",
      "column_name": "app_version",
      "column_type": "varchar(32)",
      "column_comment": "客户端版本",
      "semantic_type": "dimension",
      "is_metric": 0,
      "is_dimension": 1,
      "is_filterable": 1,
      "is_groupable": 1,
      "aggregation_methods": "",
      "sample_values": "5.1.0、5.2.0",
      "null_rate": 0.03
    }
  ]
}
```

### table_lookup

User need: 根据 DAU 需求找一下应该使用哪些数据表。

Selected tool: `search_table`

Arguments:

```json
{
  "query": "DAU 日活跃用户 需求 数据表",
  "top_n": 3
}
```

Result summary:

```json
{
  "items": [
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
      "recommended_usage": "用于 DAU、新用户日活、老用户日活、活跃会话数、人均会话时长等活跃类指标问数。",
      "forbidden_usage": "不用于事件明细追踪、用户级行为路径分析或实时活跃监控。"
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
      "recommended_usage": "用于 DAU 口径追溯、用户行为过滤、用户维度去重和活跃明细抽样。",
      "forbidden_usage": "不用于直接替代 ADS 层指标口径对外出数。"
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
      "recommended_usage": "用于排查 DAU 异常、核对事件明细、确认行为类型过滤条件。",
      "forbidden_usage": "不建议直接用于高频聚合问数，避免扫描明细成本过高。"
    }
  ]
}
```

### schema_lookup

User need: 请查看 ads_user_active_metric_di 这张表的字段结构。

Selected tool: `get_table_schema`

Arguments:

```json
{
  "table_name": "ads_user_active_metric_di"
}
```

Result summary:

```json
{
  "item": {
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
    "columns": [
      {
        "column_name": "dt",
        "column_type": "date",
        "column_comment": "统计日期，也是分区字段",
        "semantic_type": "time",
        "is_metric": 0,
        "is_dimension": 1,
        "is_filterable": 1,
        "is_groupable": 1,
        "aggregation_methods": "",
        "sample_values": "2026-05-10",
        "null_rate": 0.0,
        "status": "active"
      },
      {
        "column_name": "app_version",
        "column_type": "varchar(32)",
        "column_comment": "客户端版本",
        "semantic_type": "dimension",
        "is_metric": 0,
        "is_dimension": 1,
        "is_filterable": 1,
        "is_groupable": 1,
        "aggregation_methods": "",
        "sample_values": "5.1.0、5.2.0",
        "null_rate": 0.03,
        "status": "active"
      },
      {
        "column_name": "channel",
        "column_type": "varchar(64)",
        "column_comment": "获客渠道",
        "semantic_type": "dimension",
        "is_metric": 0,
        "is_dimension": 1,
        "is_filterable": 1,
        "is_groupable": 1,
        "aggregation_methods": "",
        "sample_values": "organic、ads、referral",
        "null_rate": 0.08,
        "status": "active"
      },
      {
        "column_name": "country",
        "column_type": "varchar(64)",
        "column_comment": "用户注册或访问国家",
        "semantic_type": "dimension",
        "is_metric": 0,
        "is_dimension": 1,
        "is_filterable": 1,
        "is_groupable": 1,
        "aggregation_methods": "",
        "sample_values": "CN、US、SA",
        "null_rate": 0.01,
        "status": "active"
      },
      {
        "column_name": "platform",
        "column_type": "varchar(32)",
        "column_comment": "访问平台",
        "semantic_type": "dimension",
        "is_metric": 0,
        "is_dimension": 1,
        "is_filterable": 1,
        "is_groupable": 1,
        "aggregation_methods": "",
        "sample_values": "iOS、Android、Web",
        "null_rate": 0.0,
        "status": "active"
      },
      {
        "column_name": "user_type",
        "column_type": "varchar(32)",
        "column_comment": "用户类型，新用户或老用户",
        "semantic_type": "dimension",
        "is_metric": 0,
        "is_dimension": 1,
        "is_filterable": 1,
        "is_groupable": 1,
        "aggregation_methods": "",
        "sample_values": "new、returning",
        "null_rate": 0.0,
        "status": "active"
      },
      {
        "column_name": "session_cnt",
        "column_type": "bigint",
        "column_comment": "用户有效会话次数",
        "semantic_type": "metric",
        "is_metric": 1,
        "is_dimension": 0,
        "is_filterable": 1,
        "is_groupable": 0,
        "aggregation_methods": "sum、avg",
        "sample_values": "1、3、8",
        "null_rate": 0.0,
        "status": "active"
      },
      {
        "column_name": "session_duration_sec",
        "column_type": "bigint",
        "column_comment": "用户有效会话总时长，单位秒",
        "semantic_type": "metric",
        "is_metric": 1,
        "is_dimension": 0,
        "is_filterable": 1,
        "is_groupable": 0,
        "aggregation_methods": "sum、avg",
        "sample_values": "30、180、900",
        "null_rate": 0.0,
        "status": "active"
      },
      {
        "column_name": "user_id",
        "column_type": "varchar(128)",
        "column_comment": "用户唯一标识，用于 DAU 去重",
        "semantic_type": "metric",
        "is_metric": 1,
        "is_dimension": 0,
   
```

### sql_validation

User need: 请校验这段 SQL 是否安全可执行：SELECT COUNT(*) AS dau FROM ads_user_active_metric_di WHERE dt = '2026-05-10'

Selected tool: `validate_sql`

Arguments:

```json
{
  "sql": "SELECT COUNT(*) AS dau FROM ads_user_active_metric_di WHERE dt = '2026-05-10'"
}
```

Result summary:

```json
{
  "is_valid": true,
  "validation_id": "5560702c6e102a15",
  "errors": [],
  "warnings": [],
  "explain": [
    {
      "id": 3,
      "parent": 0,
      "notused": 216,
      "detail": "SCAN ads_user_active_metric_di"
    }
  ]
}
```

### query_execution

User need: 请执行这个已经带分区条件的只读查询：SELECT country, COUNT(DISTINCT user_id) AS dau FROM ads_user_active_metric_di WHERE dt = '2026-05-10' AND is_valid_event = 1 AND is_bot = 0 GROUP BY country ORDER BY country

Selected tool: `execute_query`

Arguments:

```json
{
  "sql": "SELECT country, COUNT(DISTINCT user_id) AS dau FROM ads_user_active_metric_di WHERE dt = '2026-05-10' AND is_valid_event = 1 AND is_bot = 0 GROUP BY country ORDER BY country",
  "validation_id": null
}
```

Result summary:

```json
{
  "status": "success",
  "validation_id": "b7fdcb8d612c3924",
  "row_count": 3,
  "rows": [
    {
      "country": "CN",
      "dau": 2
    },
    {
      "country": "SA",
      "dau": 1
    },
    {
      "country": "US",
      "dau": 1
    }
  ]
}
```

### prompt_search

User need: 用户想做指标趋势分析，请先找相关 SQL 生成规范 Prompt。

Selected tool: `search_prompt`

Arguments:

```json
{
  "query": "指标趋势分析 SQL 生成规范 Prompt",
  "top_n": 3
}
```

Result summary:

```json
{
  "items": [
    {
      "prompt_id": "metric_trend_analysis",
      "prompt_name": "指标趋势分析 SQL 生成规范",
      "prompt_desc": "用于用户询问某个业务指标在日、周、月等时间粒度上的变化趋势时，指导模型识别指标口径、时间范围、分区过滤、聚合粒度和排序方式，生成可解释且符合只读规范的查询 SQL。"
    },
    {
      "prompt_id": "metric_anomaly_check",
      "prompt_name": "指标异常排查 SQL 生成规范",
      "prompt_desc": "用于用户询问指标为何突然升高、降低、波动或异常时，指导模型生成对比历史均值、环比、同比、分维度贡献的 SQL。"
    },
    {
      "prompt_id": "metric_compare_analysis",
      "prompt_name": "指标对比分析 SQL 生成规范",
      "prompt_desc": "用于对比两个时间段、两个业务对象或多个维度下同一指标差异的场景，帮助模型生成包含基准值、对比值、差值和变化率的 SQL。"
    }
  ]
}
```
