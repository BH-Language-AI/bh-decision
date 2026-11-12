// Orkestracija: dedup, keš, timeout, retry, fallback, circuit breaker, metrike.
// Nijedan import iz Node API-ja — radi u Node, Bun, browseru.
import type {
  DecisionRequest, DecisionResult, IProvider, ProviderStatus,
} from "./types.ts";
import { DecisionError } from "./types.ts";
import { fromSystemOne, toSystemOne } from "./systemone.ts";
import { ProviderRegistry } from "./providers.ts";
import type { DecisionConfig } from "./config.ts";

/** FNV-1a: stabilan hash bez ovisnosti. Tajne se nikad ne keširaju kao tekst. */
export function fnv1a(s: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, "0");
}

export function redactSecrets(s: string): string {
  return s
    .replace(/(Bearer\s+)[^\s"']+/gi, "$1[redacted]")
    .replace(/((?:api[_-]?key|token|secret)\s*["']?\s*[:=]\s*["']?)[^"'}\s,;]+/gi, "$1[redacted]");
}

interface CacheEntry { at: number; result: DecisionResult; }
interface Breaker { fails: number; openUntil: number; }

const BREAKER_FAILS = 3;
const BREAKER_COOLDOWN_MS = 60_000;

export class DecisionCore {
  private cache = new Map<string, CacheEntry>();
  private inflight = new Map<string, Promise<DecisionResult>>();
  private breakers = new Map<string, Breaker>();
  private stats = new Map<string, { calls: number; errors: number; fallbacks: number; lat: number[] }>();
  private sessionCounts = new Map<string, number>();

  private registry: ProviderRegistry;
  private cfg: DecisionConfig;

  constructor(registry: ProviderRegistry, cfg: DecisionConfig) {
    this.registry = registry;
    this.cfg = cfg;
  }

  private stat(id: string) {
    let s = this.stats.get(id);
    if (!s) { s = { calls: 0, errors: 0, fallbacks: 0, lat: [] }; this.stats.set(id, s); }
    return s;
  }

  private breakerOpen(id: string): boolean {
    const b = this.breakers.get(id);
    if (!b || b.openUntil === 0) return false;
    if (Date.now() > b.openUntil) { this.breakers.delete(id); return false; }
    return true;
  }

  private recordFail(id: string): void {
    const b = this.breakers.get(id) ?? { fails: 0, openUntil: 0 };
    b.fails += 1;
    if (b.fails >= BREAKER_FAILS) b.openUntil = Date.now() + BREAKER_COOLDOWN_MS;
    this.breakers.set(id, b);
    this.stat(id).errors += 1;
  }

  status(): ProviderStatus[] {
    const ids = new Set([...this.stats.keys(), ...this.registry.ids().filter((i) => !i.startsWith("future_"))]);
    return [...ids].map((id) => {
      const s = this.stats.get(id);
      const lat = s?.lat ?? [];
      return {
        id, enabled: true, healthy: s ? s.errors < s.calls : null,
        calls: s?.calls ?? 0, errors: s?.errors ?? 0, fallbacks_from: s?.fallbacks ?? 0,
        avg_latency_ms: lat.length ? Math.round(lat.reduce((a, b) => a + b, 0) / lat.length) : null,
        breaker_open: this.breakerOpen(id),
      };
    });
  }

  /** Glavni ulaz. sessionID omogućuje dedup i limit po sesiji. */
  async decide(req: DecisionRequest, sessionID = "default"): Promise<DecisionResult> {
    const t = this.cfg.thresholds;
    const used = this.sessionCounts.get(sessionID) ?? 0;
    if (used >= t.max_decisions_per_session)
      throw new DecisionError("budget", `Session decision budget exhausted (${used}/${t.max_decisions_per_session}).`);
    const key = fnv1a(sessionID + "|" + JSON.stringify(req));
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.at < t.cache_ttl_ms) return cached.result;
    const ongoing = this.inflight.get(key);
    if (ongoing) return ongoing;
    const p = this.run(req, sessionID, key).finally(() => this.inflight.delete(key));
    this.inflight.set(key, p);
    return p;
  }

  private async run(req: DecisionRequest, sessionID: string, key: string): Promise<DecisionResult> {
    const t = this.cfg.thresholds;
    const chain = [this.cfg.primary, ...this.cfg.fallback.filter((f) => f !== this.cfg.primary)];
    let lastErr: unknown = null;
    let fallbackUsed = false;
    for (const id of chain) {
      if (this.breakerOpen(id)) { lastErr = new DecisionError("breaker", `Breaker open: ${id}`, id); fallbackUsed = true; continue; }
      let provider: IProvider;
      try {
        provider = this.registry.get(id);
      } catch (e) { lastErr = e; fallbackUsed = true; continue; }
      const sys = toSystemOne(req, provider.caps().model);
      try {
        const out = await provider.decide(sys, { timeout_ms: t.timeout_ms });
        const norm = fromSystemOne(req, out.response, t.abstain);
        const conf = norm.confidence;
        const result: DecisionResult = {
          decision_id: `${Date.now().toString(36)}-${fnv1a(key + out.latency_ms)}`,
          provider: id,
          model: provider.caps().model,
          ...(out.model_version ? { model_version: out.model_version } : {}),
          decisions: norm.decisions,
          confidence: conf,
          latency_ms: out.latency_ms,
          fallback_used: fallbackUsed,
          requires_escalation: conf < t.escalation || norm.abstained.length > 0,
          abstained: norm.abstained,
          ...(out.response.usage ? { usage: out.response.usage as Record<string, unknown> } : {}),
          timestamp: new Date().toISOString(),
        };
        const s = this.stat(id);
        s.calls += 1; s.lat.push(out.latency_ms);
        this.sessionCounts.set(sessionID, (this.sessionCounts.get(sessionID) ?? 0) + 1);
        this.cache.set(key, { at: Date.now(), result });
        return result;
      } catch (e) {
        lastErr = e;
        if ((e as DecisionError).retryable === false && (e as DecisionError).code === "auth") {
          // Auth se ne ponavlja na istom provideru — odmah fallback.
        }
        this.recordFail(id);
        if (id !== this.cfg.primary) this.stat(this.cfg.primary).fallbacks += 1;
        fallbackUsed = true;
      }
    }
    throw lastErr instanceof DecisionError ? lastErr
      : new DecisionError("all_failed", "All providers failed.", undefined, false);
  }
}
