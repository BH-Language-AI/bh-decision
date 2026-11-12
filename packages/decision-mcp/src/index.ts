// BH-Decision MCP server — stdio transport. Nema javnog endpointa bez autentikacije.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { readFile } from "node:fs/promises";
import { DecisionCore } from "../../decision-core/src/core.ts";
import { ProviderRegistry } from "../../decision-core/src/providers.ts";
import { loadConfig, applyEnv, registryOptsFromEnv } from "../../decision-core/src/config.ts";
import type { DecisionConfig } from "../../decision-core/src/config.ts";
import { registerTools } from "./tools.ts";

async function loadFileConfig(path: string | undefined): Promise<DecisionConfig> {
  if (!path) return loadConfig();
  const raw = await readFile(path, "utf8");
  return loadConfig(JSON.parse(raw) as Partial<DecisionConfig>);
}

async function main(): Promise<void> {
  const cfg = applyEnv(await loadFileConfig(process.env.DECISION_CONFIG), process.env);
  const registry = new ProviderRegistry(registryOptsFromEnv(cfg, process.env));
  const core = new DecisionCore(registry, cfg);
  const server = new McpServer({ name: "bh-decision", version: "0.1.0" });
  registerTools(server, core, cfg);
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((e: unknown) => {
  process.stderr.write(`bh-decision MCP failed: ${(e as Error).message}\n`);
  process.exit(1);
});
