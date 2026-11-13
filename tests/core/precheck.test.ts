// Nezavisna analiza, tačke 1/4/7: deterministička pravila, metrike, normaliziran keš.
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DecisionCore, normalizeKey } from "../../packages/decision-core/src/core.ts";
import { matchDestructive, precheckedRiskResult } from "../../packages/decision-core/src/precheck.ts";
import { ProviderRegistry } from "../../packages/decision-core/src/providers.ts";
import { loadConfig } from "../../packages/decision-core/src/config.ts";
import type { CallOpts, IProvider, ProviderResult, SysRequest } from "../../packages/decision-core/src/types.ts";

const REQ = {
  state: { task: "Pročitaj datoteku i reci šta piše." },
  questions: { go: { id: "go", type: "boolean" as const, instructions: "Krenuti?" } },
};

function mockProvider(p: number, calls?: { n: number }): IProvider {
  return {
    caps: () => ({ id: "jev", model: "jev-1.13-free", paid: false, local: false, enabled: true }),
    async decide(_req: SysRequest, _o: CallOpts): Promise<ProviderResult> {
      if (calls) calls.n += 1;
      return { response: { model: "mock", answers: { go: { noul: p } } }, latency_ms: 5 };
    },
    async health() { return { ok: true }; },
  };
}

function coreWith(calls?: { n: number }): DecisionCore {
  const r = new ProviderRegistry({ allowPaid: false });
  (r as unknown as { providers: Map<string, IProvider> }).providers.clear();
  (r as unknown as { providers: Map<string, IProvider> }).providers.set("jev", mockProvider(0.9, calls));
  return new DecisionCore(r, loadConfig({ primary: "jev", fallback: [] }));
}

describe("precheck pravila", () => {
  it("hvata očito destruktivno (en + bs)", () => {
    for (const t of ["rm -rf /tmp/x", "DROP TABLE users", "git push --force origin main",
      "delete the database", "obriši bazu podataka", "izbrisati podatke iz baze", "mkfs /dev/sda"]) {
      assert.ok(matchDestructive(t), t);
    }
  });
  it("ne hvata benigno (nulta lažna pozitiva na uzorku)", () => {
    for (const t of ["pročitaj datoteku", "rm file.txt", "git push origin main",
      "obriši privremene fajlove", "SELECT * FROM users", "formatiraj tekst"]) {
      assert.equal(matchDestructive(t), null, t);
    }
  });
  it("prechecked rezultat: high + approval + eskalacija, 0 ms", () => {
    const r = precheckedRiskResult("rm -rf /");
    assert.equal(r.provider, "precheck");
    assert.equal(r.decisions.risk_level.selected, "high");
    assert.equal(r.decisions.needs_approval.selected, true);
    assert.equal(r.requires_escalation, true);
    assert.equal(r.latency_ms, 0);
  });
});

describe("keš normalizacija + metrike", () => {
  it("case/whitespace varijante dijele keš (1 poziv providera)", async () => {
    const calls = { n: 0 };
    const core = coreWith(calls);
    const a = { ...REQ };
    const b = { state: { task: "PROČITAJ  datoteku i  RECI šta piše." }, questions: REQ.questions };
    assert.equal(normalizeKey(JSON.stringify(a)), normalizeKey(JSON.stringify(b)));
    await core.decide(a, "s1");
    await core.decide(b, "s1");
    assert.equal(calls.n, 1);
    assert.equal(core.status().find((s) => s.id === "jev")?.cache_hits, 1);
  });
  it("status nosi p50/p95, eskalacije i precheck pokrivenost", async () => {
    const core = coreWith();
    await core.decide(REQ, "s1"); // noul 0.9 -> bez eskalacije
    core.notePrecheck(true);
    core.notePrecheck(false);
    const s = core.status().find((x) => x.id === "jev");
    assert.ok(s);
    assert.equal(typeof s.p50_latency_ms, "number");
    assert.equal(typeof s.p95_latency_ms, "number");
    assert.equal(s.escalations, 0);
    assert.deepEqual(s.precheck, { hits: 1, misses: 1, coverage: 0.5 });
  });
});
