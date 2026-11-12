// AnyJev adapter: mapiranje, gateway protokol, registar, config, MCP/plugin integracija.
// Sve s mock mrežom — bez modela, bez ključeva, bez GPU.
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { AnyjevProvider, toAnyjevItems, toSysAnswer } from "../../packages/decision-core/src/providers/anyjev.ts";
import { ProviderRegistry } from "../../packages/decision-core/src/providers.ts";
import { DecisionCore } from "../../packages/decision-core/src/core.ts";
import { applyEnv, loadConfig } from "../../packages/decision-core/src/config.ts";
import type { SysRequest } from "../../packages/decision-core/src/types.ts";

function sysReq(): SysRequest {
  return {
    model: "x",
    state: { task: "Paket nije stigao." },
    questions: {
      c: { type: "choice", instructions: "Kategorija?", criteria: { a: "Prva.", b: "Druga." } },
      b: { type: "noul", instructions: "Hitno?" },
      s: { type: "score", instructions: "Ozbiljnost?", criteria: ["Niska", "Srednja", "Visoka"] },
    },
  };
}

function canned(handler: (body: unknown) => { status: number; json: unknown }): Promise<{ url: string; close: () => void; seen: Array<{ headers: unknown; body: unknown }> }> {
  const seen: Array<{ headers: unknown; body: unknown }> = [];
  return new Promise((resolve) => {
    const server = createServer((req, res) => {
      let data = "";
      req.on("data", (c) => { data += c; });
      req.on("end", () => {
        if (req.url === "/health" || req.url === "/v1/stats") {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ ok: true }));
          return;
        }
        const body = data ? JSON.parse(data) : {};
        seen.push({ headers: req.headers, body });
        const { status, json } = handler(body);
        res.statusCode = status;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify(json));
      });
    });
    server.listen(0, "127.0.0.1", () => {
      const a = server.address() as { port: number };
      resolve({ url: `http://127.0.0.1:${a.port}`, close: () => server.close(), seen });
    });
  });
}

function okGateway() {
  return canned((body) => {
    const items = (body as { items?: AnyjevItemShape[] }).items ?? [body as AnyjevItemShape];
    return {
      status: 200,
      json: {
        decisions: items.map((it) => {
          if (it.kind === "yes_no") return { answer: true, probability: 0.7, route: "one_forward" };
          if (it.kind === "score") {
            const lv = it.options ?? ["Niska", "Srednja", "Visoka"];
            const probs: Record<string, number> = {};
            lv.forEach((l, i) => { probs[l] = i === 1 ? 0.6 : 0.4 / Math.max(1, lv.length - 1); });
            return { answer: lv[Math.min(1, lv.length - 1)], probs, value: 1.1, route: "cot" };
          }
          const opts = it.options ?? ["a", "b"];
          const probs: Record<string, number> = {};
          opts.forEach((o, i) => { probs[o] = i === 0 ? 0.8 : 0.2 / Math.max(1, opts.length - 1); });
          return { answer: opts[0], probs, route: "one_forward", level: "L0" };
        }),
      },
    };
  });
}

interface AnyjevItemShape {
  kind?: string;
  options?: string[];
}

describe("anyjev mapiranje", () => {
  it("choice/yes_no/score stavke + 64-question limit iz Corea", () => {
    const items = toAnyjevItems(sysReq());
    assert.deepEqual(items.map((i) => i.kind), ["choice", "yes_no", "score"]);
    assert.equal(items[1].options, undefined);
    assert.deepEqual(items[2].options, ["Niska", "Srednja", "Visoka"]);
  });
  it(">26 opcija se eksplicitno odbija (unsupported, ne simulira se)", () => {
    const opts: Record<string, string> = {};
    for (let i = 0; i < 27; i++) opts[`o${i}`] = `Opcija ${i}`;
    const req: SysRequest = { model: "x", state: { task: "t" }, questions: { c: { type: "choice", criteria: opts } } };
    assert.throws(() => toAnyjevItems(req), (e: unknown) => (e as { code: string }).code === "unsupported");
  });
  it("score s >10 nivoa se odbija", () => {
    const req: SysRequest = { model: "x", state: { task: "t" }, questions: { s: { type: "score", criteria: Array.from({ length: 11 }, (_, i) => `L${i}`) } } };
    assert.throws(() => toAnyjevItems(req), (e: unknown) => (e as { code: string }).code === "unsupported");
  });
  it("konstruktor odbija loš mode/decisionMode/prazan model", () => {
    assert.throws(() => new AnyjevProvider({ model: "", mode: "tacit", decisionMode: "l0", url: "http://x" }));
    assert.throws(() => new AnyjevProvider({ model: "m", mode: "x" as never, decisionMode: "l0", url: "http://x" }));
    assert.throws(() => new AnyjevProvider({ model: "m", mode: "tacit", decisionMode: "z" as never, url: "http://x" }));
  });
  it("configure: allowlist + validacija, ostalo se odbija", () => {
    const p = new AnyjevProvider({ model: "m", mode: "tacit", decisionMode: "l0", url: "http://127.0.0.1:9" });
    assert.throws(() => p.configure({ url: "ftp://x" } as never));
    assert.throws(() => p.configure({ bogus: 1 } as never));
    const eff = p.configure({ mode: "decider", decisionMode: "adaptive", tau: 0.7 } as never);
    assert.equal(eff.mode, "decider");
    assert.deepEqual(p.effective().decisionMode, "adaptive");
  });
});

describe("anyjev gateway protokol (mock)", () => {
  it("batch odluka -> SysResponse; route/level u usage; bez Authorization headera", async () => {
    const gw = await okGateway();
    try {
      const p = new AnyjevProvider({ model: "morriszjm/Tacit-4B", mode: "tacit", decisionMode: "adaptive", url: gw.url });
      const out = await p.decide(sysReq(), { timeout_ms: 5000 });
      assert.equal(out.response.answers?.c.choice, "a");
      assert.equal(out.response.answers?.b.noul, 0.7);
      assert.equal(out.response.answers?.s.score, 1.1);
      assert.equal((out.response.usage as Record<string, unknown>).route_s, "cot");
      assert.equal((out.response.usage as Record<string, unknown>).anyjev_mode, "tacit");
      assert.ok(!JSON.stringify(gw.seen).toLowerCase().includes("authorization"));
    } finally {
      gw.close();
    }
  });
  it("broj odgovora != broj pitanja -> invalid_response", async () => {
    const gw = await canned(() => ({ status: 200, json: { decisions: [{ answer: "a", probs: { a: 1 } }] } }));
    try {
      const p = new AnyjevProvider({ model: "m", mode: "tacit", decisionMode: "l0", url: gw.url });
      await assert.rejects(() => p.decide(sysReq(), { timeout_ms: 5000 }), (e: unknown) => (e as { code: string }).code === "invalid_response");
    } finally {
      gw.close();
    }
  });
  it("502 -> retryable provider greška; timeout -> timeout greška", async () => {
    const bad = await canned(() => ({ status: 502, json: { error: "upstream" } }));
    try {
      const p = new AnyjevProvider({ model: "m", mode: "tacit", decisionMode: "l0", url: bad.url });
      await assert.rejects(() => p.decide(sysReq(), { timeout_ms: 5000 }), (e: unknown) => (e as { code: string }).code === "provider" && (e as { retryable: boolean }).retryable === true);
    } finally {
      bad.close();
    }
    const slow = await canned(() => { const s = Date.now(); while (Date.now() - s < 300); return { status: 200, json: {} }; });
    try {
      const p = new AnyjevProvider({ model: "m", mode: "tacit", decisionMode: "l0", url: slow.url });
      const single: SysRequest = { model: "x", state: { task: "t" }, questions: { c: { type: "choice", criteria: { a: "A.", b: "B." } } } };
      await assert.rejects(() => p.decide(single, { timeout_ms: 50 }), (e: unknown) => (e as { code: string }).code === "timeout");
    } finally {
      slow.close();
    }
  });
  it("health: ok kad gateway živ, false kad mrtav", async () => {
    const gw = await okGateway();
    const p = new AnyjevProvider({ model: "m", mode: "tacit", decisionMode: "l0", url: gw.url });
    assert.equal((await p.health()).ok, true);
    gw.close();
    const dead = new AnyjevProvider({ model: "m", mode: "tacit", decisionMode: "l0", url: "http://127.0.0.1:9" });
    assert.equal((await dead.health()).ok, false);
  });
});

describe("anyjev registar + config", () => {
  it("enabled+model -> registriran; disabled/prazan model -> odsutan; paid denylist netaknut", () => {
    const on = new ProviderRegistry({ allowPaid: false, anyjev: { enabled: true, mode: "tacit", decisionMode: "l0", model: "morriszjm/Tacit-4B", backend: "transformers", url: "http://127.0.0.1:8101", tau: 0.5, maxCotShare: 0.2, cotWindow: 1000 } });
    assert.equal(on.get("anyjev_local").caps().model, "morriszjm/Tacit-4B");
    assert.ok(on.ids().includes("anyjev_local"));
    const off = new ProviderRegistry({ allowPaid: false });
    assert.throws(() => off.get("anyjev_local"), (e: unknown) => (e as { code: string }).code === "unknown_provider");
    const empty = new ProviderRegistry({ allowPaid: false, anyjev: { enabled: true, mode: "tacit", decisionMode: "l0", model: "", backend: "transformers", url: "http://x", tau: 0.5, maxCotShare: 0.2, cotWindow: 1000 } });
    assert.throws(() => empty.get("anyjev_local"));
    assert.throws(() => on.get("jev-1.13" as never));
  });
  it("applyEnv čita ANYJEV_* varijable", () => {
    const cfg = applyEnv(loadConfig(), {
      ANYJEV_ENABLED: "true", ANYJEV_MODE: "decider", ANYJEV_DECISION_MODE: "adaptive",
      ANYJEV_MODEL: "Qwen/Qwen3-4B", ANYJEV_BACKEND: "transformers", ANYJEV_URL: "http://127.0.0.1:8102", ANYJEV_TAU: "0.4",
    });
    assert.equal(cfg.anyjev?.enabled, true);
    assert.equal(cfg.anyjev?.mode, "decider");
    assert.equal(cfg.anyjev?.model, "Qwen/Qwen3-4B");
    assert.equal(cfg.anyjev?.tau, 0.4);
  });
});

describe("anyjev kroz Core (fallback lanac)", () => {
  it("anyjev_local radi kao fallback kad je jev bez ključa; inače normalan fallback", async () => {
    const gw = await okGateway();
    try {
      const cfg = applyEnv(loadConfig({ primary: "jev", fallback: ["anyjev_local"] }), {
        ANYJEV_ENABLED: "true", ANYJEV_MODEL: "morriszjm/Tacit-4B", ANYJEV_URL: gw.url,
      });
      const { registryOptsFromEnv } = await import("../../packages/decision-core/src/config.ts");
      const core = new DecisionCore(new ProviderRegistry(registryOptsFromEnv(cfg, process.env)), cfg);
      const r = await core.decide({
        state: { task: "Paket nije stigao." },
        questions: { intent: { id: "intent", type: "categorical", instructions: "Kategorija?", options: { a: "Prva.", b: "Druga." } } },
      }, "anyjev-chain");
      assert.equal(r.provider, "anyjev_local");
      assert.equal(r.fallback_used, true);
      assert.equal(r.decisions.intent.selected, "a");
    } finally {
      gw.close();
    }
  });
});

describe("anyjev MCP (14 alata) + plugin provider= prefiks", () => {
  it("registerTools registrira 11 + 3 anyjev alata", async () => {
    const { McpServer } = await import("../../packages/decision-mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/server/mcp.js");
    const { registerTools } = await import("../../packages/decision-mcp/src/tools.ts");
    const core = new DecisionCore(new ProviderRegistry({ allowPaid: false }), loadConfig());
    const server = new McpServer({ name: "t", version: "0.0.0" });
    registerTools(server, core, loadConfig());
    const tools = (server as unknown as { _registeredTools: Record<string, unknown> })._registeredTools;
    for (const n of ["decision_anyjev_status", "decision_anyjev_config", "decision_anyjev_test"]) assert.ok(n in tools, n);
    assert.equal(Object.keys(tools).length, 14);
  });
  it("plugin /decision prihvaća provider= prefiks i pada graciozno", async () => {
    const plugin = (await import("../../packages/opencode-plugin/src/index.ts")).default as { setup: (c: unknown) => Promise<void> };
    const rec: { synthetic: string[] } = { synthetic: [] };
    const added: Array<{ name: string; execute: (i: unknown) => Promise<void> }> = [];
    const ctx = {
      options: {},
      skill: { transform: async (cb: (e: unknown) => void) => { cb({ get: () => undefined, add: () => { } }); } },
      mcp: { transform: async (cb: (e: unknown) => void) => { cb({ get: () => undefined, set: () => { } }); } },
      command: { transform: async (cb: (e: unknown) => void) => { cb({ add: (d: never) => { added.push(d); } }); } },
      session: { synthetic: async ({ text }: { text: string }) => { rec.synthetic.push(text); } },
    };
    await plugin.setup(ctx);
    const cmd = added.find((c) => c.name === "decision");
    assert.ok(cmd);
    await cmd.execute({ sessionID: "s1", prompt: { text: "provider=__nope__ test" } });
    assert.ok(rec.synthetic.some((t) => t.includes("unavailable")));
  });
});
