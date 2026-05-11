#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const DEFAULT_AGENT_FILE = "AGENTS.md";
const DEFAULT_CONFIG_FILE = ".codex/config.toml";
const DEFAULT_SERVER_NAME = "data-agent";
const DEFAULT_MCP_URL = "https://voiceless-olive-giraffe.fastmcp.app/mcp";

function parseArgs(argv) {
  const options = {
    cwd: process.cwd(),
    agentFile: DEFAULT_AGENT_FILE,
    configFile: DEFAULT_CONFIG_FILE,
    serverName: DEFAULT_SERVER_NAME,
    mcpUrl: DEFAULT_MCP_URL,
    auth: process.env.DATA_AGENT_MCP_AUTH || "",
    force: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => {
      index += 1;
      if (index >= argv.length) {
        throw new Error(`Missing value for ${arg}`);
      }
      return argv[index];
    };

    if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else if (arg === "--cwd") {
      options.cwd = path.resolve(next());
    } else if (arg === "--agent-file") {
      options.agentFile = next();
    } else if (arg === "--config-file") {
      options.configFile = next();
    } else if (arg === "--server-name") {
      options.serverName = next();
    } else if (arg === "--mcp-url") {
      options.mcpUrl = next();
    } else if (arg === "--auth") {
      options.auth = next();
    } else if (arg === "--force") {
      options.force = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return options;
}

function printHelp() {
  console.log(`
data-agent-mcp-init

Initialize the current directory with AGENTS.md and Codex MCP config.

Usage:
  DATA_AGENT_MCP_AUTH=... npx ./node-init
  npx ./node-init --auth ... --mcp-url https://example.com/mcp
  npx data-agent-mcp-init --auth ...

Options:
  --mcp-url <url>          Remote MCP server URL. Default: ${DEFAULT_MCP_URL}
  --auth <token>           FastMCP auth token. Can also use DATA_AGENT_MCP_AUTH.
  --server-name <name>     MCP server name. Default: data-agent
  --cwd <path>             Directory to initialize. Default: current directory
  --agent-file <path>      Agent instruction file. Default: AGENTS.md
  --config-file <path>     MCP config file. Default: .codex/config.toml
  --force                  Overwrite existing generated files.
  -h, --help               Show help.
`.trim());
}

function renderAgent({ serverName, mcpUrl }) {
  return `# 数据分析师说明书

你是一名严谨的数据分析师，当前工作区已接入远程 data-agent MCP 服务。

## MCP 服务器

- 服务名称：${serverName}
- 远程地址：${mcpUrl}

## 分析原则

1. 先查元数据，再写 SQL。不要凭记忆猜指标、表名或字段名。
2. 指标口径以 MCP 返回的定义、公式、默认过滤条件和来源表为准。
3. 生成 SQL 前优先确认：
   - 指标：使用 search_metric / get_metric_detail
   - 表：使用 search_table / get_table_schema
   - 字段：使用 search_column / get_table_schema
   - Prompt 规范：使用 search_prompt / get_prompt_detail
4. SQL 必须先调用 validate_sql 校验，通过后再调用 execute_query。
5. 分析结论要说明口径、时间范围、维度、过滤条件和潜在数据限制。

## SQL 规范

- 只允许只读查询。
- 禁止 INSERT、UPDATE、DELETE、DROP、ALTER、CREATE 等写操作。
- 查询分区表时必须包含分区条件。
- 不要直接 SELECT *，只选择分析所需字段。
- 聚合 DAU 等去重指标时，必须使用指标定义里的字段和默认过滤条件。
- 结果需要可解释，字段别名要清晰。

## 输出风格

- 先给结论，再给依据。
- 对用户不明确的问题，先列出你采用的合理假设。
- 如果 MCP 召回为空，换关键词继续召回，不要直接编造。
- 如果 SQL 校验失败，根据 validate_sql 的错误逐项修复后再执行。
`;
}

function tomlString(value) {
  return JSON.stringify(value);
}

function tomlKey(key) {
  if (/^[A-Za-z0-9_-]+$/.test(key)) {
    return key;
  }

  return tomlString(key);
}

function tomlTablePath(parts) {
  return parts.map((part) => tomlKey(part)).join(".");
}

function renderMcpConfig({ serverName, mcpUrl, auth }) {
  const serverPath = tomlTablePath(["mcp_servers", serverName]);
  const lines = [
    `[${serverPath}]`,
    'type = "http"',
    `url = ${tomlString(mcpUrl)}`,
  ];

  if (auth) {
    lines.push("", `[${serverPath}.headers]`, `Authorization = ${tomlString(`Bearer ${auth}`)}`);
  }

  return `${lines.join("\n")}\n`;
}

async function exists(filePath) {
  try {
    await readFile(filePath, "utf8");
    return true;
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

async function writeGeneratedFile(filePath, content, force) {
  if (!force && (await exists(filePath))) {
    return { path: filePath, status: "skipped" };
  }

  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, content, "utf8");
  return { path: filePath, status: "written" };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    printHelp();
    return;
  }

  if (!options.mcpUrl) {
    throw new Error("--mcp-url is required.");
  }

  if (!options.auth) {
    console.warn("warning: no auth token provided; config.toml will not include Authorization headers.");
  }

  const agentPath = path.resolve(options.cwd, options.agentFile);
  const configPath = path.resolve(options.cwd, options.configFile);

  const results = [
    await writeGeneratedFile(agentPath, renderAgent(options), options.force),
    await writeGeneratedFile(configPath, renderMcpConfig(options), options.force),
  ];

  for (const result of results) {
    console.log(`${result.status}: ${path.relative(options.cwd, result.path)}`);
  }

  console.log(`initialized: ${options.cwd}`);
}

main().catch((error) => {
  console.error(`data-agent-mcp-init: ${error.message}`);
  process.exitCode = 1;
});
