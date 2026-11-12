// Faza 2: registar, denylist, fallback, breaker, keš, pragovi, privatnost.
import { describe, it, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { DecisionCore, fnv1a, redactSecrets } from "../../packages/decision-core/src/core.ts";
import { ProviderRegistry, SystemOneHttpProvider } from "../../packages/decision-core/src/providers.ts";
import { loadConfig, applyEnv } from "../../packages/decision-core/src/config.ts";
import type { CallOpts, IProvider, ProviderResult, SysRequest } from "../../packages/decision-core/src/types.ts";
import { DecisionError } from "../../packages/decision-core/src/types.ts";

const REQ = {
  state: { task: "tajni-token-abc zadatak", language: "bs-ijekavica" },
  questions: { go: { id: "go", type: "boolean" as const, instructions: "Krenuti?" } },
};

function mockProvider(id: string, p: number, opts: { fail?: DecisionError; calls?: { n: number }; delay?: number } = {}): IProvider {
  return {
    caps: () => ({ id, model: id === "jev" ? "jev-1.13-free" : "Cloudflare/clef-flash", paid: false, local: id !== "jev", enabled: true }),
    async decide(_req: SysRequest, _o: CallOpts): Promise<ProviderResult> {
      if (opts.calls) opts.calls.n += 1;
      if (opts.delay) await new Promise((r) => setTimeout(r, opts.delay));
      if (opts.fail) throw opts.fail;
      return { response: { model: "mock", answers: { go: { noul: p } } }, latency_ms: 1 };
    },
    async health() { return { ok: !opts.fail }; },
  };
}

function registryWith(primary: IProvider, fallback?: IProvider): ProviderRegistry {
  const r = new ProviderRegistry({ allowPaid: false });
  (r as unknown as { providers: Map<string, IProvider> }).providers.clear();
  (r as unknown as { providers: Map<string, IProvider> }).providers.set(primary.caps().id, primary);
  if (fallback) (r as unknown as { providers: Map<string, IProvider> }).providers.set(fallback.caps().id, fallback);
  return r;
}

describe("registry", () => {
  it("slučaj 3/4: primary se koristi; env mijenja provider bez koda", () => {
    const cfg = applyEnv(loadConfig({ primary: "jev", fallback: ["clef_local"] }), { DECISION_PROVIDER: "clef_local" });
    assert.equal(cfg.primary, "clef_local");
  });
  it("slučaj 7: plaćeni provider se nikad ne registrira niti poziva", () => {
    assert.throws(() => new ProviderRegistry({ allowPaid: false }).register(
      new SystemOneHttpProvider({ id: "x", model: "jev-1.13", url: "http://x", paid: true, local: false }),
    ), (e: unknown) => (e as DecisionError).code === "paid_blocked");
    const r = new ProviderRegistry({ allowPaid: false });
    assert.throws(() => r.get("future_bh_decision_2b"), (e: unknown) => (e as DecisionError).code === "not_available");
    assert.throws(() => r.get("nepostojeci"), (e: unknown) => (e as DecisionError).code === "unknown_provider");
  });
  it("slučaj 6: clef_hosted_free ne postoji bez verificiranog free tiera", () => {
    const r = new ProviderRegistry({ allowPaid: false });
    assert.throws(() => r.get("clef_hosted_free"));
    assert.ok(!r.ids().includes("clef_hosted_free"));
  });
});

describe("core decide", () => {
  let calls: { n: number };
  beforeEach(() => { calls = { n: 0 }; });

  it("slučaj 5: Jev pad -> clef_local fallback, fallback_used=true", async () => {
    const r = registryWith(
      mockProvider("jev", 0.9, { fail: new DecisionError("provider", "down", "jev", true), calls }),
      mockProvider("clef_local", 0.8),
    );
    const core = new DecisionCore(r, loadConfig({ primary: "jev", fallback: ["clef_local"] }));
    const res = await core.decide(structuredClone(REQ), "s1");
    assert.equal(res.provider, "clef_local");
    assert.equal(res.fallback_used, true);
    assert.equal(res.model_version, undefined);
  });
  it("slučaj 12: visoko povjerenje -> bez eskalacije; nisko -> eskalacija", async () => {
    const r = registryWith(mockProvider("jev", 0.95));
    const core = new DecisionCore(r, loadConfig({ primary: "jev", fallback: [] }));
    const hi = await core.decide(structuredClone(REQ), "s-high");
    assert.equal(hi.requires_escalation, false);
    assert.ok(hi.confidence >= 0.8);
    const r2 = registryWith(mockProvider("jev", 0.5));
    const core2 = new DecisionCore(r2, loadConfig({ primary: "jev", fallback: [] }));
    const lo = await core2.decide(structuredClone(REQ), "s-low");
    assert.equal(lo.requires_escalation, true);
  });
  it("dedup: istodobni pozivi -> jedan provider poziv; keš vraća bez poziva", async () => {
    const r = registryWith(mockProvider("jev", 0.9, { calls, delay: 20 }));
    const core = new DecisionCore(r, loadConfig({ primary: "jev", fallback: [] }));
    const [a, b] = await Promise.all([core.decide(structuredClone(REQ), "s2"), core.decide(structuredClone(REQ), "s2")]);
    assert.equal(a.decision_id, b.decision_id);
    assert.equal(calls.n, 1);
  });
  it("budget: limit po sesiji se provodi", async () => {
    const r = registryWith(mockProvider("jev", 0.9));
    const core = new DecisionCore(r, loadConfig({ primary: "jev", fallback: [], thresholds: { ...loadConfig().thresholds, max_decisions_per_session: 1 } }));
    await core.decide(structuredClone(REQ), "s3");
    await assert.rejects(core.decide({ state: { task: "drugi" }, questions: REQ.questions }, "s3"),
      (e: unknown) => (e as DecisionError).code === "budget");
  });
  it("breaker: nakon 3 greške provider se preskače", async () => {
    const r = registryWith(mockProvider("jev", 0.9, { fail: new DecisionError("provider", "x", "jev", true) }));
    const core = new DecisionCore(r, loadConfig({ primary: "jev", fallback: [] }));
    for (let i = 0; i < 3; i++) await assert.rejects(core.decide({ state: { task: `t${i}` }, questions: REQ.questions }, `sb${i}`));
    await assert.rejects(core.decide({ state: { task: "t9" }, questions: REQ.questions }, "sb9"),
      (e: unknown) => (e as DecisionError).code === "breaker");
  });
  it("slučaj 20: rezultat ne sadrži tekst zadatka; tajne se redigiraju", async () => {
    const r = registryWith(mockProvider("jev", 0.9));
    const core = new DecisionCore(r, loadConfig({ primary: "jev", fallback: [] }));
    const res = await core.decide(structuredClone(REQ), "s4");
    assert.ok(!JSON.stringify(res).includes("tajni-token-abc"));
    assert.equal(redactSecrets("Authorization: Bearer sk-live-123"), "Authorization: Bearer [redacted]");
    assert.equal(redactSecrets('{"api_key":"abc123"}'), '{"api_key":"[redacted]"}');
  });
  it("status() vraća metriku po provideru", async () => {
    const r = registryWith(mockProvider("jev", 0.9));
    const core = new DecisionCore(r, loadConfig({ primary: "jev", fallback: [] }));
    await core.decide(structuredClone(REQ), "s5");
    const st = core.status().find((s) => s.id === "jev");
    assert.equal(st?.calls, 1);
    assert.equal(typeof st?.avg_latency_ms, "number");
  });
});

describe("timeout (slučaj 8)", () => {
  it("spori provider -> timeout greška", async () => {
    const { createServer } = await import("node:http");
    const server = createServer((_req, res) => { setTimeout(() => res.end("{}"), 300); });
    await new Promise<void>((r) => server.listen(0, r));
    const port = (server.address() as { port: number }).port;
    try {
      const p = new SystemOneHttpProvider({ id: "slow", model: "m", url: `http://127.0.0.1:${port}`, paid: false, local: true });
      await assert.rejects(p.decide({ model: "m", state: "x", questions: {} }, { timeout_ms: 50 }),
        (e: unknown) => (e as DecisionError).code === "timeout");
    } finally {
      server.close();
    }
  });
});

describe("fnv1a", () => {
  it("stabilan hash", () => {
    assert.equal(fnv1a("abc"), fnv1a("abc"));
    assert.notEqual(fnv1a("abc"), fnv1a("abd"));
  });
});
