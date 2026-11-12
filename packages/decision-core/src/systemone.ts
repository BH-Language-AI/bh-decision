// Normalizacija: interni koncept <-> stvarni SystemOne format.
// Normalization: internal concept <-> actual SystemOne wire format.
import type {
  DecisionRequest, InternalQuestion, QuestionDecision, SysQuestion, SysRequest, SysResponse,
} from "./types.ts";
import { DecisionError } from "./types.ts";

const ID_RE = /^[A-Za-z0-9_.-]{1,100}$/;

export function validateRequest(req: DecisionRequest): void {
  if (!req || typeof req !== "object") throw new DecisionError("invalid_request", "Request must be an object.");
  const task = req.state?.task;
  if (typeof task !== "string" || task.trim().length === 0)
    throw new DecisionError("invalid_request", "state.task must be a non-empty string.");
  if (task.length > 8000)
    throw new DecisionError("invalid_request", "state.task too long (max 8000 chars).");
  const ids = Object.keys(req.questions ?? {});
  if (ids.length === 0 || ids.length > 64)
    throw new DecisionError("invalid_request", "1-64 questions required.");
  for (const q of Object.values(req.questions)) validateQuestion(q);
}

function validateQuestion(q: InternalQuestion): void {
  if (!ID_RE.test(q.id)) throw new DecisionError("invalid_request", `Bad question id: ${q.id}`);
  if (q.type === "categorical") {
    const opts = q.options ? Object.keys(q.options) : [];
    if (opts.length < 2 || opts.length > 64)
      throw new DecisionError("invalid_request", `categorical needs 2-64 options: ${q.id}`);
  } else if (q.type === "score") {
    const levels = Array.isArray(q.options) ? q.options : [];
    if (levels.length < 2 || levels.length > 16)
      throw new DecisionError("invalid_request", `score needs 2-16 levels: ${q.id}`);
  } else if (q.type !== "boolean") {
    throw new DecisionError("invalid_request", `Unknown question type: ${(q as { type: string }).type}`);
  }
}

/** Interni zahtjev -> SystemOne. Nikad ne šalje images/videos. */
export function toSystemOne(req: DecisionRequest, model: string): SysRequest {
  validateRequest(req);
  const questions: Record<string, SysQuestion> = {};
  for (const [id, q] of Object.entries(req.questions)) {
    if (q.type === "boolean") {
      questions[id] = { type: "noul", ...(q.instructions ? { instructions: q.instructions } : {}) };
    } else if (q.type === "score") {
      questions[id] = {
        type: "score",
        ...(q.instructions ? { instructions: q.instructions } : {}),
        criteria: q.options as string[],
      };
    } else {
      questions[id] = {
        type: "choice",
        ...(q.instructions ? { instructions: q.instructions } : {}),
        criteria: q.options as Record<string, string>,
      };
    }
  }
  // Minimalni state: task + jezik + alati; context samo ako je eksplicitno dozvoljen.
  const state: Record<string, unknown> = { task: req.state.task };
  if (req.state.language) state.language = req.state.language;
  if (req.state.available_tools) state.available_tools = req.state.available_tools;
  if (req.state.context) state.context = req.state.context;
  return { model, state, questions };
}

function checkProbs(probs: Record<string, number>, id: string): void {
  const vals = Object.values(probs);
  if (vals.length === 0) throw new DecisionError("invalid_response", `Empty probabilities: ${id}`);
  for (const v of vals) {
    if (typeof v !== "number" || Number.isNaN(v) || v < 0 || v > 1)
      throw new DecisionError("invalid_response", `Bad probability value: ${id}`);
  }
  const sum = vals.reduce((a, b) => a + b, 0);
  if (Math.abs(sum - 1) > 0.02) throw new DecisionError("invalid_response", `Probabilities sum != 1: ${id}`);
}

function normalizeAnswer(id: string, q: InternalQuestion, a: SysAnswer | undefined): QuestionDecision {
  if (!a || typeof a !== "object") throw new DecisionError("invalid_response", `Missing answer: ${id}`);
  if (q.type === "boolean") {
    const p = a.noul;
    if (typeof p !== "number" || p < 0 || p > 1)
      throw new DecisionError("invalid_response", `Bad noul answer: ${id}`);
    return { selected: p >= 0.5, probabilities: { true: p, false: 1 - p } };
  }
  if (q.type === "score") {
    const levels = q.options as string[];
    if (!a.probabilities || typeof a.score !== "number")
      throw new DecisionError("invalid_response", `Bad score answer: ${id}`);
    checkProbs(a.probabilities, id);
    const idx = Math.max(0, Math.min(levels.length - 1, Math.round(a.score)));
    return { selected: idx, probabilities: a.probabilities, ...(a.confidence !== undefined ? { confidence: a.confidence } : {}) };
  }
  const opts = Object.keys(q.options as Record<string, string>);
  if (!a.probabilities || typeof a.choice !== "string" || !opts.includes(a.choice))
    throw new DecisionError("invalid_response", `Bad choice answer: ${id}`);
  checkProbs(a.probabilities, id);
  return { selected: a.choice, probabilities: a.probabilities, ...(a.confidence !== undefined ? { confidence: a.confidence } : {}) };
}

/** SystemOne odgovor -> interna shema. Apstinencija kad max prob < prag. */
export function fromSystemOne(
  req: DecisionRequest, res: SysResponse, abstainThreshold: number,
): { decisions: Record<string, QuestionDecision>; confidence: number; abstained: string[] } {
  if (!res || typeof res !== "object" || !res.answers)
    throw new DecisionError("invalid_response", "Response has no answers.");
  const decisions: Record<string, QuestionDecision> = {};
  const abstained: string[] = [];
  let minMax = 1;
  for (const [id, q] of Object.entries(req.questions)) {
    const d = normalizeAnswer(id, q, res.answers[id]);
    const max = Math.max(...Object.values(d.probabilities));
    minMax = Math.min(minMax, max);
    if (max < abstainThreshold) abstained.push(id);
    decisions[id] = d;
  }
  return { decisions, confidence: abstained.length > 0 ? Math.min(minMax, 0.5) : minMax, abstained };
}
