#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const DEFAULT_AGENT_FILE = "CLAUDE.md";
const DEFAULT_CONFIG_FILE = ".mcp.json";
const DEFAULT_SERVER_NAME = "data-agent";
const DEFAULT_MCP_URL = "https://voiceless-olive-giraffe.fastmcp.app/mcp";
const DEFAULT_TOKEN_ENV_VAR = "DATA_AGENT_MCP_TOKEN";

function parseArgs(argv) {
  const options = {
    cwd: process.cwd(),
    agentFile: DEFAULT_AGENT_FILE,
    configFile: DEFAULT_CONFIG_FILE,
    serverName: DEFAULT_SERVER_NAME,
    mcpUrl: DEFAULT_MCP_URL,
    tokenEnvVar: DEFAULT_TOKEN_ENV_VAR,
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
    } else if (arg === "--token-env-var") {
      options.tokenEnvVar = next();
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
data-agent-claude-init

Initialize the current directory with CLAUDE.md and Claude Code project MCP config.

Usage:
  npx ./node-init-claude
  npx ./node-init-claude --mcp-url https://example.com/mcp
  npx data-agent-claude-init

Options:
  --mcp-url <url>          Remote MCP server URL. Default: ${DEFAULT_MCP_URL}
  --token-env-var <name>   Env var expanded by Claude Code for bearer token. Default: ${DEFAULT_TOKEN_ENV_VAR}
  --server-name <name>     MCP server name. Default: data-agent
  --cwd <path>             Directory to initialize. Default: current directory
  --agent-file <path>      Claude instruction file. Default: CLAUDE.md
  --config-file <path>     Claude Code MCP config file. Default: .mcp.json
  --force                  Overwrite existing generated files.
  -h, --help               Show help.
`.trim());
}

function renderClaudeInstructions() {
  return `# 数据分析师说明书

你是一名严谨、可复核的数据分析师。你的任务是帮助用户把业务问题转化为可靠的数据分析过程，并在 Claude Code 中优先使用项目已配置的 MCP 服务完成元数据查询、SQL 校验和数据查询。

## 工作原则

1. 先理解问题，再选择工具。不要在没有确认口径、时间范围、维度和过滤条件前直接写 SQL。
2. 先查元数据，再写 SQL。指标、表、字段、Prompt、权限和查询规范都应以当前可用 MCP 服务返回的信息为准。
3. 不要假设固定 MCP 名称、服务器地址或工具清单。每次工作时根据当前环境中实际可用的 MCP server 和 tools 选择能力。
4. 如果配置了多个 MCP 服务，优先选择与当前任务最匹配、数据口径最权威的服务；必要时交叉验证。
5. 对用户不明确的问题，先说明你的合理假设；如果假设会明显影响结论，应先向用户确认。

## MCP 使用方式

1. 先通过 Claude Code 的 MCP 能力发现当前可用工具，再决定调用顺序。
2. 查指标时，应获取指标名称、业务定义、计算公式、默认过滤条件、来源表和支持维度。
3. 查表和字段时，应确认表粒度、分区字段、时间字段、字段类型、字段语义、是否可过滤、是否可分组。
4. 生成 SQL 后，如果环境提供 SQL 校验工具，必须先校验再执行。
5. 如果 MCP 召回为空，不要编造结果；应换关键词、换语言、缩小或扩大查询范围后重试。
6. 如果某个 MCP 工具失败，说明失败原因，并尝试使用同一服务中的其他工具或降级方案。

## SQL 规范

- 只允许只读查询。
- 禁止 INSERT、UPDATE、DELETE、DROP、ALTER、CREATE 等写操作。
- 查询分区表时必须包含分区条件。
- 不要直接 SELECT *，只选择分析所需字段。
- 聚合去重指标、比率指标或派生指标时，必须遵循 MCP 返回的指标定义、字段和默认过滤条件。
- 结果需要可解释，字段别名要清晰。
- 如果 SQL 校验失败，应逐条阅读错误信息，修复后再次校验。

## 输出风格

- 先给结论，再给依据。
- 明确说明分析口径、时间范围、维度、过滤条件和数据限制。
- 给出关键 SQL 或查询逻辑，方便复核。
- 对异常值、空结果、样本不足或口径不确定的情况，要主动提示风险。
- 不把工具输出原样堆给用户；要整理成业务可读的分析结论。
`;
}

function renderMcpJson({ serverName, mcpUrl, tokenEnvVar }) {
  return `${JSON.stringify(
    {
      mcpServers: {
        [serverName]: {
          type: "http",
          url: mcpUrl,
          headers: {
            Authorization: `Bearer \${${tokenEnvVar}}`,
          },
        },
      },
    },
    null,
    2,
  )}\n`;
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

  const agentPath = path.resolve(options.cwd, options.agentFile);
  const configPath = path.resolve(options.cwd, options.configFile);

  const results = [
    await writeGeneratedFile(agentPath, renderClaudeInstructions(), options.force),
    await writeGeneratedFile(configPath, renderMcpJson(options), options.force),
  ];

  for (const result of results) {
    console.log(`${result.status}: ${path.relative(options.cwd, result.path)}`);
  }

  console.log(`initialized: ${options.cwd}`);
  console.log(`before running Claude Code, export ${options.tokenEnvVar}=<token>`);
}

main().catch((error) => {
  console.error(`data-agent-claude-init: ${error.message}`);
  process.exitCode = 1;
});
