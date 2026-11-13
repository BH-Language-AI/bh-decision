// Deterministička pravila prije modela: 0 ms, 0 tokena kad pogode.
// Proširivati samo obrascima s nultom stopom lažnih pozitiva; sve ostalo ide modelu.
import type { DecisionResult } from "./types.ts";
import { fnv1a } from "./core.ts";

const DESTRUCTIVE: Array<{ re: RegExp; id: string }> = [
  { re: /\brm\s+[^;|&]*-[a-z]*r/i, id: "rm-recursive" },
  { re: /\bdrop\s+(table|database|schema)\b/i, id: "sql-drop" },
  { re: /\bgit\s+push\b[^;|&]*--force\b/i, id: "git-push-force" },
  { re: /\b(delete|drop)\b[^;|&]*\b(database|bazu|podataka)\b/i, id: "delete-database" },
  { re: /\b(obriši|izbriši|obrisati|izbrisati)\b[^;|&]*\b(bazu|podatke|podataka|baze)\b/i, id: "obrisi-bazu" },
  { re: /\b(format\s+[a-z]:|mkfs\b)/i, id: "format-disk" },
];

/** Vraća id pravila ili null. Samo očito destruktivno; sumnjivo → model. */
export function matchDestructive(task: string): string | null {
  for (const { re, id } of DESTRUCTIVE) {
    re.lastIndex = 0;
    if (re.test(task)) return id;
  }
  return null;
}

/** Gotov rezultat bez poziva providera: visok rizik + obavezna eskalacija. */
export function precheckedRiskResult(task: string): DecisionResult {
  return {
    decision_id: `pre-${fnv1a(task)}`,
    provider: "precheck",
    model: "deterministic-rules-v1",
    decisions: {
      risk_level: { selected: "high", probabilities: { low: 0, medium: 0, high: 1 } },
      needs_approval: { selected: true, probabilities: { true: 1, false: 0 } },
    },
    confidence: 1,
    latency_ms: 0,
    fallback_used: false,
    requires_escalation: true,
    abstained: [],
    timestamp: new Date().toISOString(),
  };
}
