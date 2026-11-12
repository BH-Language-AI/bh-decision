// AnyJev adapter — Tacit/Decider iza HTTP ugovora (anyjev.serve ili naš bridge).
// AnyJev adapter — Tacit/Decider behind an HTTP contract (anyjev.serve or our bridge).
// Bez novih TS ovisnosti: samo fetch. Mapira SysRequest -> /v1/decide -> SysResponse,
// pa postojeća fromSystemOne normalizacija radi bez promjena.
import type {
  CallOpts, IProvider, ProviderCaps, ProviderResult, SysAnswer, SysRequest, SysResponse,
} from "../types.ts";
import { DecisionError } from "../types.ts";

export interface AnyjevProviderOpts {
  id?: string;
  model: string;
  mode: "decider" | "tacit";
  decisionMode: "l0" | "adaptive";
  url: string;
  tau?: number;
  maxCotShare?: number | null;
  cotWindow?: number | null;
}

export interface AnyjevItem {
  state: unknown;
  question: string;
  options?: string[];
  kind: "choice" | "yes_no" | "score";
}

interface AnyjevOne {
  answer: unknown;
  probs?: Record<string, number>;
  probability?: number;
  value?: number;
  route?: string;
  level?: string;
}

function fail(code: string, msg: string, retryable = false): never {
  throw new DecisionError(code, msg, "anyjev_local", retryable);
}

/** SysRequest -> AnyJev stavke. >26 opcija se eksplicitno odbija (letter readout limit). */
export function toAnyjevItems(sys: SysRequest): AnyjevItem[] {
  const items: AnyjevItem[] = [];
  for (const [id, q] of Object.entries(sys.questions)) {
    const question = q.instructions ?? id;
    if (q.type === "noul") {
      items.push({ state: sys.state, question, kind: "yes_no" });
    } else if (q.type === "score") {
      const levels = q.criteria as string[];
      if (!Array.isArray(levels) || levels.length < 2 || levels.length > 10)
        fail("unsupported", `AnyJev score needs 2-10 levels: ${id}`);
      items.push({ state: sys.state, question, options: levels, kind: "score" });
    } else {
      const opts = Object.keys((q.criteria ?? {}) as Record<string, string>);
      if (opts.length < 2) fail("invalid_request", `choice needs >=2 options: ${id}`);
      if (opts.length > 26)
        fail("unsupported", `AnyJev supports at most 26 options, got ${opts.length}: ${id}`);
      items.push({ state: sys.state, question, options: opts, kind: "choice" });
    }
  }
  if (items.length === 0) fail("invalid_request", "No questions to decide.");
  return items;
}

function checkSum(probs: Record<string, number>, id: string): void {
  const vals = Object.values(probs);
  if (!vals.length) fail("invalid_response", `Empty probabilities: ${id}`);
  for (const v of vals)
    if (typeof v !== "number" || Number.isNaN(v) || v < 0 || v > 1)
      fail("invalid_response", `Bad probability value: ${id}`);
  const sum = vals.reduce((a, b) => a + b, 0);
  if (Math.abs(sum - 1) > 0.02) fail("invalid_response", `Probabilities sum != 1: ${id}`);
}

/** Jedan AnyJev odgovor -> SysAnswer. Nepoznat oblik se odbija, ne simulira. */
export function toSysAnswer(id: string, kind: string, options: string[], r: AnyjevOne): SysAnswer {
  if (!r || typeof r !== "object") fail("invalid_response", `Missing answer: ${id}`);
  if (kind === "yes_no") {
    let p: number | undefined;
    if (typeof r.probability === "number") p = r.probability;
    else if (r.probs && typeof r.probs.Yes === "number" && typeof r.probs.No === "number") {
      checkSum({ Yes: r.probs.Yes, No: r.probs.No }, id);
      p = r.probs.Yes;
    }
    if (p === undefined || p < 0 || p > 1)
      fail("invalid_response", `Bad yes_no answer (need probability or Yes/No probs): ${id}`);
    return { noul: p as number };
  }
  if (kind === "score") {
    if (!r.probs) fail("invalid_response", `Bad score answer (need probs): ${id}`);
    checkSum(r.probs, id);
    const idx = options.indexOf(String(r.answer));
    const value = typeof r.value === "number" ? r.value : idx >= 0 ? idx : fail("invalid_response", `Bad score answer: ${id}`) as never;
    return { score: value, probabilities: r.probs };
  }
  // choice
  if (!r.probs || typeof r.answer !== "string" || !options.includes(r.answer))
    fail("invalid_response", `Bad choice answer: ${id}`);
  checkSum(r.probs as Record<string, number>, id);
  const probs = r.probs as Record<string, number>;
  const conf = Math.max(...Object.values(probs));
  return { choice: r.answer as string, probabilities: probs, confidence: conf };
}

async function postJson(url: string, body: unknown, timeoutMs: number): Promise<{ status: number; json: unknown }> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const text = await res.text();
    let json: unknown = null;
    try { json = text ? JSON.parse(text) : null; } catch { json = null; }
    return { status: res.status, json };
  } catch (e) {
    if ((e as Error).name === "AbortError") throw new DecisionError("timeout", `AnyJev timeout after ${timeoutMs}ms.`, "anyjev_local", true);
    throw new DecisionError("network", `AnyJev network error: ${(e as Error).message}`, "anyjev_local", true);
  } finally {
    clearTimeout(timer);
  }
}

export class AnyjevProvider implements IProvider {
  private o: Required<Pick<AnyjevProviderOpts, "model" | "mode" | "decisionMode" | "url">> &
    Partial<AnyjevProviderOpts> & { id: string };
  constructor(o: AnyjevProviderOpts) {
    if (!o.model) fail("invalid_config", "AnyJev model must be set (ANYJEV_MODEL).");
    if (!["decider", "tacit"].includes(o.mode)) fail("invalid_config", `AnyJev mode must be decider|tacit.`);
    if (!["l0", "adaptive"].includes(o.decisionMode)) fail("invalid_config", `AnyJev decision_mode must be l0|adaptive.`);
    this.o = { id: "anyjev_local", ...o };
  }
  caps(): ProviderCaps {
    return { id: this.o.id, model: this.o.model, paid: false, local: true, enabled: true };
  }
  /** Validirana promjena dozvoljenih polja (samo lokalni poziv, ne remote). */
  configure(patch: Partial<AnyjevProviderOpts>): { id: string; model: string; mode: string; decisionMode: string; url: string } {
    const allowed = ["mode", "decisionMode", "model", "url", "tau", "maxCotShare", "cotWindow"] as const;
    for (const k of Object.keys(patch)) {
      if (!(allowed as readonly string[]).includes(k))
        throw new DecisionError("invalid_config", `AnyJev: field not configurable: ${k}`, "anyjev_local", false);
    }
    if (patch.mode !== undefined && !["decider", "tacit"].includes(patch.mode))
      throw new DecisionError("invalid_config", "mode must be decider|tacit.", "anyjev_local", false);
    if (patch.decisionMode !== undefined && !["l0", "adaptive"].includes(patch.decisionMode))
      throw new DecisionError("invalid_config", "decisionMode must be l0|adaptive.", "anyjev_local", false);
    if (patch.model !== undefined && !patch.model.trim())
      throw new DecisionError("invalid_config", "model must be non-empty.", "anyjev_local", false);
    if (patch.url !== undefined && !/^https?:\/\/.+/.test(patch.url))
      throw new DecisionError("invalid_config", "url must be http(s).", "anyjev_local", false);
    Object.assign(this.o, patch);
    return { id: this.o.id, model: this.o.model, mode: this.o.mode, decisionMode: this.o.decisionMode, url: this.o.url };
  }
  effective(): { id: string; model: string; mode: string; decisionMode: string; url: string; tau?: number } {
    return {
      id: this.o.id, model: this.o.model, mode: this.o.mode,
      decisionMode: this.o.decisionMode, url: this.o.url,
      ...(this.o.tau !== undefined ? { tau: this.o.tau } : {}),
    };
  }
  async decide(sys: SysRequest, opts: CallOpts): Promise<ProviderResult> {
    const t0 = Date.now();
    const items = toAnyjevItems(sys);
    const kinds = items.map((i) => i.kind);
    const { status, json } = await postJson(
      `${this.o.url.replace(/\/$/, "")}/v1/decide`,
      items.length === 1 ? items[0] : { items }, opts.timeout_ms);
    if (status === 400 || status === 404)
      throw new DecisionError("invalid_response", `AnyJev rejected request (${status}).`, "anyjev_local", false);
    if (status === 502 || status >= 500)
      throw new DecisionError("provider", `AnyJev upstream error ${status}.`, "anyjev_local", true);
    if (status < 200 || status >= 300)
      throw new DecisionError("provider", `AnyJev unexpected status ${status}.`, "anyjev_local", true);
    const raw = (json ?? {}) as { answer?: unknown } & AnyjevOne & { decisions?: AnyjevOne[] };
    const list: AnyjevOne[] = Array.isArray(raw.decisions) ? raw.decisions : [raw as AnyjevOne];
    if (list.length !== items.length)
      throw new DecisionError("invalid_response", "AnyJev answer count mismatch.", "anyjev_local", false);
    const ids = Object.keys(sys.questions);
    const answers: Record<string, SysAnswer> = {};
    const usage: Record<string, unknown> = { anyjev_mode: this.o.mode, anyjev_decision_mode: this.o.decisionMode };
    list.forEach((r, i) => {
      answers[ids[i]] = toSysAnswer(ids[i], kinds[i], items[i].options ?? [], r);
      if (r.route) usage[`route_${ids[i]}`] = r.route;
      if (r.level) usage[`level_${ids[i]}`] = r.level;
    });
    return {
      response: { model: this.o.model, answers, usage },
      model_version: this.o.model,
      latency_ms: Date.now() - t0,
    };
  }
  async health(): Promise<{ ok: boolean; latency_ms?: number; reason?: string }> {
    const t0 = Date.now();
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 5000);
      try {
        const res = await fetch(`${this.o.url.replace(/\/$/, "")}/health`, { signal: ctrl.signal });
        return { ok: res.status === 200, latency_ms: Date.now() - t0 };
      } finally {
        clearTimeout(timer);
      }
    } catch (e) {
      return { ok: false, reason: (e as Error).message };
    }
  }
}
