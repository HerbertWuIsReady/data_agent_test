#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const DEFAULT_AGENT_FILE = "agent.md";
const DEFAULT_CONFIG_FILE = ".mcp.json";
const DEFAULT_SERVER_NAME = "data-agent";

function parseArgs(argv) {
  const options = {
    cwd: process.cwd(),
    agentFile: DEFAULT_AGENT_FILE,
    configFile: DEFAULT_CONFIG_FILE,
    serverName: DEFAULT_SERVER_NAME,
    mcpUrl: "",
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

Initialize the current directory with an agent.md file and remote MCP config.

Usage:
  npx ./node-init --mcp-url https://example.com/mcp
  npx data-agent-mcp-init --mcp-url https://example.com/mcp

Options:
  --mcp-url <url>          Remote MCP server URL. Required.
  --server-name <name>     MCP server name. Default: data-agent
  --cwd <path>             Directory to initialize. Default: current directory
  --agent-file <path>      Agent instruction file. Default: agent.md
  --config-file <path>     MCP config file. Default: .mcp.json
  --force                  Overwrite existing generated files.
  -h, --help               Show help.
`.trim());
}

function renderAgent({ serverName, mcpUrl }) {
  return `# Data Agent

You are working in a local workspace initialized for the data-agent MCP server.

## MCP Server

- Server name: ${serverName}
- Remote URL: ${mcpUrl}

## Workflow

1. Use MCP lookup tools before writing SQL:
   - search_prompt
   - search_metric
   - search_table
   - search_column
   - get_table_schema
2. Validate generated SQL with validate_sql before execution.
3. Execute only read-only SQL with execute_query.
4. Prefer metadata-backed table, column, metric, and prompt choices over guesses.

## Guardrails

- Do not run write SQL.
- Always include partition conditions for partitioned tables.
- Use metric definitions and default filters exactly as returned by MCP.
- If lookup results are empty, refine the query before guessing.
`;
}

function renderMcpConfig({ serverName, mcpUrl }) {
  return `${JSON.stringify(
    {
      mcpServers: {
        [serverName]: {
          type: "http",
          url: mcpUrl,
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
