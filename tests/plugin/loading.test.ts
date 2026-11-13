// Faza 5: plugin se učitava, registrira skill+MCP+komande, nikad ne zaobilazi dozvole.
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import plugin from "../../packages/opencode-plugin/src/index.ts";

function mockCtx() {
  const rec = { skills: [] as unknown[], mcp: [] as unknown[], commands: [] as { name: string; execute: (i: unknown) => Promise<void> }[], synthetic: [] as string[], touched: [] as string[] };
  const ctx = {
    options: {},
    skill: { transform: async (cb: (e: unknown) => void) => { cb({ get: () => undefined, add: (s: unknown) => { rec.skills.push(s); } }); } },
    mcp: { transform: async (cb: (e: unknown) => void) => { cb({ get: () => undefined, set: (n: string, c: unknown) => { rec.mcp.push({ n, c }); } }); } },
    command: { transform: async (cb: (e: unknown) => void) => { cb({ add: (d: { name: string; execute: (i: unknown) => Promise<void> }) => { rec.commands.push(d); } }); } },
    session: { synthetic: async ({ text }: { text: string }) => { rec.synthetic.push(text); } },
  };
  const proxy = new Proxy(ctx, { get(t, p) { if (typeof p === "string" && !["options", "skill", "mcp", "command", "session", "then"].includes(p)) rec.touched.push(p); return (t as Record<string | symbol, unknown>)[p]; } });
  return { ctx: proxy, rec };
}

describe("plugin (slučajevi 15-19)", () => {
  it("učitava se i registrira skill, MCP i komande", async () => {
    const { ctx, rec } = mockCtx();
    await (plugin as { setup: (c: unknown) => Promise<void> }).setup(ctx);
    assert.equal(rec.skills.length, 1);
    assert.equal(rec.mcp.length, 1);
    assert.deepEqual(rec.commands.map((c) => c.name).sort(), ["decision", "decision-rank", "decision-risk", "decision-status"]);
    const mcp = rec.mcp[0] as { n: string; c: { enabled: boolean } };
    assert.equal(mcp.n, "bh-decision");
    assert.equal(mcp.c.enabled, true);
  });

  it("nikad ne dira permission/hooks/tool sustav niti šalje promptove (slučaj 16/19)", async () => {
    const { ctx, rec } = mockCtx();
    await (plugin as { setup: (c: unknown) => Promise<void> }).setup(ctx);
    assert.deepEqual(rec.touched, []);
    assert.deepEqual(rec.synthetic, []);
  });

  it("graceful fallback: nedostupan provider -> synthetic poruka, bez iznimke", async () => {
    const { ctx, rec } = mockCtx();
    await (plugin as { setup: (c: unknown) => Promise<void> }).setup(ctx);
    const cmd = rec.commands.find((c) => c.name === "decision");
    assert.ok(cmd);
    const prev = { ...process.env };
    process.env.DECISION_PROVIDER = "__nope__";
    process.env.DECISION_FALLBACK = "";
    try {
      await cmd.execute({ sessionID: "s1", prompt: { text: "napravi izvještaj" } });
    } finally {
      process.env = prev;
    }
    assert.ok(rec.synthetic.some((t) => t.includes("unavailable")));
  });

  it("decision-rank traži sintaksu '<task> | opt1, opt2' bez poziva providera", async () => {
    const { ctx, rec } = mockCtx();
    await (plugin as { setup: (c: unknown) => Promise<void> }).setup(ctx);
    const cmd = rec.commands.find((c) => c.name === "decision-rank");
    assert.ok(cmd);
    await cmd.execute({ sessionID: "s1", prompt: { text: "samo zadatak bez opcija" } });
    assert.ok(rec.synthetic.some((t) => t.includes("usage: /decision-rank")));
  });

  it("decision-risk graceful fallback bez iznimke", async () => {
    const { ctx, rec } = mockCtx();
    await (plugin as { setup: (c: unknown) => Promise<void> }).setup(ctx);
    const cmd = rec.commands.find((c) => c.name === "decision-risk");
    assert.ok(cmd);
    const prev = { ...process.env };
    process.env.DECISION_PROVIDER = "__nope__";
    process.env.DECISION_FALLBACK = "";
    try {
      await cmd.execute({ sessionID: "s1", prompt: { text: "obriši bazu" } });
    } finally {
      process.env = prev;
    }
    assert.ok(rec.synthetic.some((t) => t.includes("unavailable")));
  });

  it("enabled=false -> ništa se ne registrira", async () => {
    const { ctx, rec } = mockCtx();
    (ctx as { options: unknown }).options = { enabled: false };
    await (plugin as { setup: (c: unknown) => Promise<void> }).setup(ctx);
    assert.deepEqual([...rec.skills, ...rec.mcp, ...rec.commands], []);
  });
});
