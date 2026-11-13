// BH-Decision OpenCode plugin — automatska + ručna decision podrška.
// Pravila: nikad ne autorizira destruktivne akcije; OpenCode dozvole ostaju autoritet;
// pri grešci/timeoutu tihi nastavak bez odluke; bez tajni u logovima.
import { Plugin } from "@opencode/plugin";
import { DecisionCore } from "../../decision-core/src/core.ts";
import { ProviderRegistry } from "../../decision-core/src/providers.ts";
import { loadConfig, applyEnv, registryOptsFromEnv } from "../../decision-core/src/config.ts";

const SKILL_ID = "decision-intelligence";

export interface DecisionPluginOptions {
  enabled?: boolean;
  automatic?: boolean;
}

function mcpEntry(): string | null {
  try {
    const url = new URL("../../decision-mcp/src/index.ts", import.meta.url);
    return url.protocol === "file:" ? url.pathname : null;
  } catch {
    return null;
  }
}

export function buildCore(env: Record<string, string | undefined> = {}): DecisionCore {
  const cfg = applyEnv(loadConfig(), env as Record<string, string>);
  return new DecisionCore(new ProviderRegistry(registryOptsFromEnv(cfg, env as Record<string, string>)), cfg);
}

// provider=<id> prefiks za jednokratni ručni izbor providera / one-off manual select.
function withProvider(text: string): { text: string; env: Record<string, string> } {
  const m = text.match(/^provider=([A-Za-z0-9_.-]+)\s+/);
  if (m) return { text: text.slice(m[0].length).trim(), env: { ...process.env as Record<string, string>, DECISION_PROVIDER: m[1] } };
  return { text, env: process.env as Record<string, string> };
}

function fmt(r: { decisions: Record<string, { selected: unknown }>; confidence: number; provider: string; requires_escalation: boolean }): string {
  const parts = Object.entries(r.decisions).map(([k, v]) => `${k}=${String(v.selected)}`).join(" ");
  return `${parts} confidence=${r.confidence.toFixed(2)} provider=${r.provider}${r.requires_escalation ? " ESCALATE" : ""}`;
}

export default Plugin.define({
  id: "bh-decision",
  async setup(ctx) {
    const opts = (ctx.options ?? {}) as DecisionPluginOptions;
    if (opts.enabled === false) return;

    // 1. Skill: registriraj ako postoji u ovom paketu/repozitoriju.
    try {
      const skillPath = new URL("../../skills/decision-intelligence/SKILL.md", import.meta.url).pathname;
      await ctx.skill.transform((editor) => {
        if (!editor.get(SKILL_ID)) {
          editor.add({
            id: SKILL_ID as never, name: "Decision Intelligence" as never,
            description: "Structured decision support via decision_* MCP tools.",
            path: skillPath as never,
            content: "See SKILL.md. Minimal state, budgets, escalation rules.",
          } as never);
        }
      });
    } catch { /* skill ostaje dostupan iz repozitorija / skill stays available from repo */ }

    // 2. MCP server: auto-registracija lokalnog stdio servera.
    const entry = mcpEntry();
    if (entry) {
      await ctx.mcp.transform((editor) => {
        if (!editor.get("bh-decision")) {
          editor.set("bh-decision", {
            type: "local",
            command: ["node", "--experimental-strip-types", entry],
            enabled: true,
          } as never);
        }
      });
    }

    // 3. Ručne komande: /decision, /decision-risk, /decision-rank, /decision-status.
    await ctx.command.transform((editor) => {
      editor.add({
        name: "decision",
        description: "Classify a task via BH-Decision (intent + complexity). Prefix 'provider=<id>' for a one-off provider.",
        execute: async ({ sessionID, prompt }: { sessionID: string; prompt: { text: string } }) => {
          const parsed = withProvider(prompt.text.trim());
          if (!parsed.text) return;
          try {
            const core = buildCore(parsed.env);
            const r = await core.decide({
              state: { task: parsed.text },
              questions: {
                intent: { id: "intent", type: "categorical", instructions: "Koju kategoriju zadatka opisuje tekst?",
                  options: { research: "Istraživanje.", coding: "Pisanje koda.", debugging: "Otklanjanje greške.", planning: "Planiranje.", testing: "Testiranje.", deployment: "Isporuka.", other: "Ostalo." } },
                complexity: { id: "complexity", type: "categorical", instructions: "Složenost?",
                  options: { low: "Niska.", medium: "Srednja.", high: "Visoka." } },
              },
            }, `plugin:${sessionID}`);
            await ctx.session.synthetic({ sessionID, text: `decision: ${fmt(r)}` });
          } catch {
            await ctx.session.synthetic({ sessionID, text: "decision: unavailable, continuing normally." });
          }
        },
      } as never);
      editor.add({
        name: "decision-risk",
        description: "Assess risk via BH-Decision (risk_level + needs_approval). Usage: /decision-risk [provider=<id>] <task>.",
        execute: async ({ sessionID, prompt }: { sessionID: string; prompt: { text: string } }) => {
          const parsed = withProvider(prompt.text.trim());
          if (!parsed.text) return;
          try {
            const core = buildCore(parsed.env);
            const r = await core.decide({
              state: { task: parsed.text },
              questions: {
                risk_level: { id: "risk_level", type: "categorical", instructions: "Koliki je rizik izvršenja?",
                  options: { low: "Bezopasno.", medium: "Oprez, provjeriti.", high: "Visok rizik, ljudsko odobrenje." } },
                needs_approval: { id: "needs_approval", type: "boolean", instructions: "Treba li ljudsko odobrenje prije izvršenja?" },
              },
            }, `plugin:${sessionID}`);
            await ctx.session.synthetic({ sessionID, text: `decision-risk: ${fmt(r)}` });
          } catch {
            await ctx.session.synthetic({ sessionID, text: "decision-risk: unavailable, continuing normally." });
          }
        },
      } as never);
      editor.add({
        name: "decision-rank",
        description: "Rank options via BH-Decision. Usage: /decision-rank [provider=<id>] <task> | opt1, opt2, opt3.",
        execute: async ({ sessionID, prompt }: { sessionID: string; prompt: { text: string } }) => {
          const parsed = withProvider(prompt.text.trim());
          if (!parsed.text) return;
          const parts = parsed.text.split("|").map((s) => s.trim());
          if (parts.length < 2 || !parts[0] || !parts[1]) {
            await ctx.session.synthetic({ sessionID, text: "decision-rank: usage: /decision-rank <task> | opt1, opt2, opt3" });
            return;
          }
          const options: Record<string, string> = Object.fromEntries(
            parts[1].split(",").map((s) => s.trim()).filter(Boolean).map((o) => [o, `Opcija: ${o}`]),
          );
          if (Object.keys(options).length < 2) {
            await ctx.session.synthetic({ sessionID, text: "decision-rank: need at least 2 options." });
            return;
          }
          try {
            const core = buildCore(parsed.env);
            const r = await core.decide({
              state: { task: parts[0] },
              questions: { rank: { id: "rank", type: "categorical", instructions: "Koji kandidat je najbolji?", options } },
            }, `plugin:${sessionID}`);
            await ctx.session.synthetic({ sessionID, text: `decision-rank: ${fmt(r)}` });
          } catch {
            await ctx.session.synthetic({ sessionID, text: "decision-rank: unavailable, continuing normally." });
          }
        },
      } as never);
      editor.add({
        name: "decision-status",
        description: "Show BH-Decision provider health and stats.",
        execute: async ({ sessionID }: { sessionID: string }) => {
          const core = buildCore(process.env as Record<string, string>);
          const rows = core.status().map((s) => `${s.id}: calls=${s.calls} err=${s.errors} avg=${s.avg_latency_ms ?? "-"}ms${s.breaker_open ? " BREAKER" : ""}`).join("\n");
          await ctx.session.synthetic({ sessionID, text: `decision providers:\n${rows}` });
        },
      } as never);
    });

    // 4. Automatske odluke: namjerno konzervativno u v0.1 — agent ih poziva kroz
    // skill + MCP alate. Prompt/context hook bi dodao latenciju svakom zahtjevu,
    // što specifikacija izričito zabranjuje. Hook integracija nakon verifikacije.
    void opts.automatic;
  },
});
