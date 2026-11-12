// Faza 3: MCP startup/shutdown, sheme alata, pozivi (pozitivni + greške).
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { createServer, type Server } from "node:http";
import { writeFile, mkdtemp } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { Client } from "../../packages/decision-mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js";
import { StdioClientTransport } from "../../packages/decision-mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js";

const MCP_DIR = "/home/sha/BH-Decision/packages/decision-mcp";

function cannedSystemOne(): Promise<{ server: Server; url: string }> {
  return new Promise((resolve) => {
    const server = createServer((req, res) => {
      let body = "";
      req.on("data", (c) => { body += c; });
      req.on("end", () => {
        const q = JSON.parse(body).questions as Record<string, { type: string; criteria?: Record<string, string> }>;
        const answers: Record<string, unknown> = {};
        for (const [id, qq] of Object.entries(q)) {
          if (qq.type === "noul") answers[id] = { noul: 0.9 };
          else if (qq.type === "choice") {
            const first = Object.keys(qq.criteria ?? { a: "", b: "" })[0];
            const probs: Record<string, number> = {};
            for (const k of Object.keys(qq.criteria ?? { a: "", b: "" })) probs[k] = k === first ? 0.8 : 0.2 / Math.max(1, Object.keys(qq.criteria ?? {}).length - 1);
            answers[id] = { choice: first, probabilities: probs, confidence: 0.8 };
          } else {
            answers[id] = { score: 0, probabilities: { low: 0.8, medium: 0.1, high: 0.1 }, legend: ["low", "medium", "high"] };
          }
        }
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ model: "mock-flash", answers, usage: {} }));
      });
    });
    server.listen(0, "127.0.0.1", () => {
      const a = server.address() as { port: number };
      resolve({ server, url: `http://127.0.0.1:${a.port}` });
    });
  });
}

describe("MCP server", () => {
  it("slučaj 14: startup + 11 alata sa shemama", async () => {
    const { server: canned, url } = await cannedSystemOne();
    const dir = await mkdtemp(join(tmpdir(), "bh-dec-"));
    const cfgPath = join(dir, "decision.json");
    await writeFile(cfgPath, JSON.stringify({ primary: "clef_local", fallback: [], clefLocalUrl: url }));
    const transport = new StdioClientTransport({ command: "node", args: ["--experimental-strip-types", "src/index.ts"], cwd: MCP_DIR, env: { ...process.env, DECISION_CONFIG: cfgPath } });
    const client = new Client({ name: "test", version: "0.0.0" });
    try {
      await client.connect(transport);
      const { tools } = await client.listTools();
      assert.equal(tools.length, 11);
      const names = tools.map((t) => t.name).sort();
      assert.ok(names.includes("decision_classify") && names.includes("decision_benchmark") && names.includes("decision_status"));
      for (const t of tools) assert.ok(t.inputSchema, `schema: ${t.name}`);

      const cls = await client.callTool({ name: "decision_classify", arguments: { task: "Napiši funkciju", options: { coding: "Kod.", research: "Istraživanje." } } });
      const text = (cls.content as Array<{ text: string }>)[0].text;
      const parsed = JSON.parse(text) as { provider: string; decisions: { intent: { selected: string } } };
      assert.equal(parsed.provider, "clef_local");
      assert.equal(parsed.decisions.intent.selected, "coding");

      const st = await client.callTool({ name: "decision_status", arguments: {} });
      const status = JSON.parse((st.content as Array<{ text: string }>)[0].text) as { providers: Array<{ id: string }> };
      assert.ok(status.providers.some((p) => p.id === "clef_local"));
    } finally {
      await client.close();
      canned.close();
    }
  });

  it("slučaj 14/15: shutdown čist; greška providera se vraća kao MCP greška, ne ruši server", async () => {
    const transport = new StdioClientTransport({ command: "node", args: ["--experimental-strip-types", "src/index.ts"], cwd: MCP_DIR, env: { ...process.env, DECISION_PROVIDER: "jev", DECISION_FALLBACK: "" } });
    const client = new Client({ name: "test", version: "0.0.0" });
    try {
      await client.connect(transport);
      const res = await client.callTool({ name: "decision_status", arguments: {} });
      assert.ok(!(res as { isError?: boolean }).isError);
      const bad = await client.callTool({ name: "decision_classify", arguments: { task: "x", options: { a: "A.", b: "B." } } });
      assert.equal((bad as { isError?: boolean }).isError, true); // nema ključa/mreže -> uredna greška
    } finally {
      await client.close();
    }
  });
});
