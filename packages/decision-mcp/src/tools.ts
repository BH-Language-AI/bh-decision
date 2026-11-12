// MCP alati / MCP tools — svih 11. Tanki sloj iznad DecisionCore.
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { DecisionCore } from "../../decision-core/src/core.ts";
import type { DecisionConfig } from "../../decision-core/src/config.ts";
import type { DecisionRequest, InternalQuestion } from "../../decision-core/src/types.ts";

const Lang = z.string().optional().describe("Jezik zadatka / task language, npr. bs-ijekavica");
const Session = z.string().optional().describe("ID sesije za dedup i budžet / session ID");

function req(task: string, language: string | undefined, questions: Record<string, InternalQuestion>, tools?: string[]): DecisionRequest {
  return {
    state: { task, ...(language ? { language } : {}), ...(tools ? { available_tools: tools } : {}) },
    questions,
  };
}

function out(result: unknown) {
  return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 1) }] };
}

function cat(id: string, instructions: string, options: Record<string, string>): Record<string, InternalQuestion> {
  return { [id]: { id, type: "categorical", instructions, options } };
}

export function registerTools(server: McpServer, core: DecisionCore, _cfg: DecisionConfig): void {
  server.registerTool("decision_classify", {
    description: "Klasificira namjeru/posao korisnika. / Classifies user intent.",
    inputSchema: {
      task: z.string().describe("Opis zadatka / task description"),
      options: z.record(z.string(), z.string()).describe("Opcija->opis / option->description"),
      language: Lang, session_id: Session,
    },
  }, async ({ task, options, language, session_id }) =>
    out(await core.decide(req(task, language, cat("intent", "Koju kategoriju zadatka opisuje stanje?", options)), session_id ?? "default")));

  server.registerTool("decision_route", {
    description: "Preporučuje najboljeg agenta/model/providera. / Recommends agent/model/provider.",
    inputSchema: {
      task: z.string(), candidates: z.record(z.string(), z.string()).describe("Kandidat->opis"),
      language: Lang, session_id: Session,
    },
  }, async ({ task, candidates, language, session_id }) =>
    out(await core.decide(req(task, language, cat("route", "Koji kandidat je najprikladniji za zadatak?", candidates)), session_id ?? "default")));

  server.registerTool("decision_select_tool", {
    description: "Bira najrelevantniji alat. / Chooses the most relevant tool.",
    inputSchema: {
      task: z.string(), available_tools: z.array(z.string()), language: Lang, session_id: Session,
    },
  }, async ({ task, available_tools, language, session_id }) => {
    const options: Record<string, string> = Object.fromEntries(available_tools.map((t) => [t, `Alat: ${t}`]));
    return out(await core.decide(req(task, language, cat("tool", "Koji alat je najrelevantniji?", options), available_tools), session_id ?? "default"));
  });

  server.registerTool("decision_assess_complexity", {
    description: "Procjenjuje složenost zadatka. / Estimates task complexity.",
    inputSchema: { task: z.string(), language: Lang, session_id: Session },
  }, async ({ task, language, session_id }) =>
    out(await core.decide(req(task, language, {
      complexity: { id: "complexity", type: "categorical", instructions: "Kolika je složenost zadatka?",
        options: { low: "Jednostavno, deterministički rješivo.", medium: "Srednje, treba rasuđivanje.", high: "Složeno, potrebna eskalacija." } },
    }), session_id ?? "default")));

  server.registerTool("decision_assess_risk", {
    description: "Klasificira operativni i sigurnosni rizik. / Classifies risk.",
    inputSchema: { task: z.string(), language: Lang, session_id: Session },
  }, async ({ task, language, session_id }) =>
    out(await core.decide(req(task, language, {
      risk_level: { id: "risk_level", type: "categorical", instructions: "Koliki je rizik izvršenja?",
        options: { low: "Bezopasno.", medium: "Oprez, provjeriti.", high: "Visok rizik, ljudsko odobrenje." } },
      needs_approval: { id: "needs_approval", type: "boolean", instructions: "Treba li ljudsko odobrenje prije izvršenja?" },
    }), session_id ?? "default")));

  server.registerTool("decision_rank", {
    description: "Rangira kandidate po vjerojatnosti. / Ranks candidates.",
    inputSchema: {
      task: z.string(), candidates: z.record(z.string(), z.string()), language: Lang, session_id: Session,
    },
  }, async ({ task, candidates, language, session_id }) => {
    const r = await core.decide(req(task, language, cat("rank", "Koji kandidat je najbolji? Rangiraj po vjerojatnosti.", candidates)), session_id ?? "default");
    const probs = r.decisions.rank.probabilities;
    const ranking = Object.entries(probs).sort((a, b) => b[1] - a[1]).map(([id, p]) => ({ id, probability: p }));
    return out({ ...r, ranking });
  });

  server.registerTool("decision_score", {
    description: "Boduje opcije prema rubrici. / Scores options against a rubric.",
    inputSchema: {
      task: z.string(), options: z.array(z.string()).describe("ID-jevi opcija / option IDs"),
      rubric: z.array(z.string()).describe("Poredana legenda / ordered legend"),
      language: Lang, session_id: Session,
    },
  }, async ({ task, options, rubric, language, session_id }) => {
    const questions: Record<string, InternalQuestion> = {};
    for (const o of options) questions[`score_${o}`] = { id: `score_${o}`, type: "score", instructions: `Ocijeni opciju "${o}" za zadatak.`, options: rubric };
    return out(await core.decide(req(task, language, questions), session_id ?? "default"));
  });

  server.registerTool("decision_confidence", {
    description: "Procjenjuje povjerenje u tvrdnju. / Evaluates confidence in a claim.",
    inputSchema: { task: z.string(), claim: z.string(), language: Lang, session_id: Session },
  }, async ({ task, claim, language, session_id }) =>
    out(await core.decide(req(`${task}\nTvrdnja/Claim: ${claim}`, language, {
      holds: { id: "holds", type: "boolean", instructions: "Je li tvrdnja točna s obzirom na stanje?" },
    }), session_id ?? "default")));

  server.registerTool("decision_should_escalate", {
    description: "Odlučuje treba li eskalacija glavnom LLM-u. / Decides on escalation.",
    inputSchema: { task: z.string(), language: Lang, session_id: Session },
  }, async ({ task, language, session_id }) => {
    const r = await core.decide(req(task, language, {
      escalate: { id: "escalate", type: "boolean", instructions: "Treba li zadatak eskalirati jačem modelu zbog složenosti ili rizika?" },
    }), session_id ?? "default");
    return out({ ...r, escalate: r.decisions.escalate.selected === true || r.requires_escalation });
  });

  server.registerTool("decision_status", {
    description: "Dostupnost providera, aktivni model, latencije. / Provider health and stats.",
    inputSchema: {},
  }, async () => out({ providers: core.status() }));

  server.registerTool("decision_benchmark", {
    description: "Pokreće evaluacijski paket nad uzorcima. / Runs the eval suite.",
    inputSchema: {
      limit: z.number().int().min(1).max(100).optional().describe("Max primjera / max samples (default 10)"),
      session_id: Session,
    },
  }, async ({ limit, session_id }) => out(await runBenchmark(core, limit ?? 10, session_id ?? "bench")));
}

async function runBenchmark(core: DecisionCore, limit: number, session: string) {
  const { readFile, readdir } = await import("node:fs/promises");
  const { join, dirname } = await import("node:path");
  const { fileURLToPath } = await import("node:url");
  const dir = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "datasets", "samples");
  let files: string[] = [];
  try { files = (await readdir(dir)).filter((f) => f.endsWith(".jsonl")); } catch { /* nema dataseta */ }
  const results: Array<Record<string, unknown>> = [];
  let correct = 0, total = 0, abst = 0, lat: number[] = [];
  for (const f of files) {
    const lines = (await readFile(join(dir, f), "utf8")).split("\n").filter(Boolean);
    for (const line of lines) {
      if (total >= limit) break;
      const s = JSON.parse(line) as { state: string; lang?: string; options: Array<{ id: string; text: string }>; reference?: { decision?: string } };
      if (!s.reference?.decision) continue;
      const options: Record<string, string> = Object.fromEntries(s.options.map((o) => [o.id, o.text]));
      const t0 = Date.now();
      try {
        const r = await core.decide(
          { state: { task: s.state, language: s.lang }, questions: { answer: { id: "answer", type: "categorical", options } } },
          `${session}-${total}`,
        );
        lat.push(Date.now() - t0);
        const sel = String(r.decisions.answer.selected);
        total += 1;
        if (sel === s.reference.decision) correct += 1;
        if (r.abstained.length) abst += 1;
        results.push({ file: f, expected: s.reference.decision, selected: sel, provider: r.provider, abstained: r.abstained });
      } catch (e) {
        total += 1;
        results.push({ file: f, error: (e as Error).message });
      }
    }
  }
  lat.sort((a, b) => a - b);
  return {
    total, correct, accuracy: total ? correct / total : null, abstentions: abst,
    latency_ms: { p50: lat.length ? lat[Math.floor(lat.length / 2)] : null, max: lat.length ? lat[lat.length - 1] : null },
    providers: core.status(), results,
  };
}
