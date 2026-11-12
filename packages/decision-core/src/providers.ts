// Provideri / Providers: apstrakcija, registar, denylist plaćenih modela.
import type { CallOpts, IProvider, ProviderCaps, ProviderResult, SysRequest } from "./types.ts";
import { DecisionError } from "./types.ts";
import { AnyjevProvider } from "./providers/anyjev.ts";
import type { AnyjevConfig } from "./config.ts";

/** Nikad se ne pozivaju automatski dok je allow_paid=false. */
export const PAID_DENYLIST = [
  "jev-1.13", // plaćeni pandan Free modela / paid counterpart of Free
  "@cf/cloudflare/clef",
  "@cf/cloudflare/clef-flash", // Workers AI: $0.038/1M
];

async function postJson(url: string, body: unknown, opts: CallOpts, headers: Record<string, string>): Promise<{ status: number; json: unknown }> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeout_ms);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(body),
      signal: opts.signal ? AbortSignal.any([opts.signal, ctrl.signal]) : ctrl.signal,
    });
    const text = await res.text();
    let json: unknown = null;
    try { json = text ? JSON.parse(text) : null; } catch { json = null; }
    return { status: res.status, json };
  } catch (e) {
    if ((e as Error).name === "AbortError") throw new DecisionError("timeout", `Timeout after ${opts.timeout_ms}ms.`, undefined, true);
    throw new DecisionError("network", `Network error: ${(e as Error).message}`, undefined, true);
  } finally {
    clearTimeout(timer);
  }
}

function checkStatus(status: number, provider: string): void {
  if (status === 401 || status === 403)
    throw new DecisionError("auth", "Authentication failed (401/403).", provider, false);
  if (status === 429)
    throw new DecisionError("rate_limit", "Rate limited (429).", provider, true);
  if (status >= 500) throw new DecisionError("provider", `Provider error ${status}.`, provider, true);
  if (status < 200 || status >= 300)
    throw new DecisionError("provider", `Unexpected status ${status}.`, provider, false);
}

export interface HttpProviderOpts {
  id: string;
  model: string;
  url: string;
  paid: boolean;
  local: boolean;
  headers?: () => Record<string, string>;
}

/** Generički SystemOne HTTP provider (Jev, Clef lokalno/hosted). */
export class SystemOneHttpProvider implements IProvider {
  private o: HttpProviderOpts;
  constructor(o: HttpProviderOpts) { this.o = o; }
  caps(): ProviderCaps {
    return { id: this.o.id, model: this.o.model, paid: this.o.paid, local: this.o.local, enabled: true };
  }
  async decide(req: SysRequest, opts: CallOpts): Promise<ProviderResult> {
    const t0 = Date.now();
    const { status, json } = await postJson(this.o.url, req, opts, this.o.headers?.() ?? {});
    checkStatus(status, this.o.id);
    const r = (json ?? {}) as { model?: string; answers?: unknown; usage?: unknown };
    if (!r.answers || typeof r.answers !== "object")
      throw new DecisionError("invalid_response", "No answers in provider response.", this.o.id, false);
    return {
      response: { model: r.model, answers: r.answers as never, usage: r.usage as never },
      ...(typeof r.model === "string" ? { model_version: r.model } : {}),
      latency_ms: Date.now() - t0,
    };
  }
  async health(): Promise<{ ok: boolean; latency_ms?: number; reason?: string }> {
    const t0 = Date.now();
    try {
      const { status } = await postJson(
        this.o.url,
        { model: this.o.model, state: "health check", questions: { ok: { type: "noul" as const } } },
        { timeout_ms: 5000 }, this.o.headers?.() ?? {},
      );
      if (status === 401 || status === 403) return { ok: false, reason: "auth" };
      return { ok: status >= 200 && status < 300, latency_ms: Date.now() - t0 };
    } catch (e) {
      return { ok: false, reason: (e as Error).message };
    }
  }
}

export interface RegistryOpts {
  allowPaid: boolean;
  jevApiKey?: string;
  jevEndpoint?: string;
  clefLocalUrl?: string;
  clefHostedVerifiedFree?: boolean;
  clefAccountId?: string;
  clefToken?: string;
  anyjev?: AnyjevConfig;
}

/** Registar: redoslijed, denylist, future_bh_* utori (bez lažnih implementacija). */
export class ProviderRegistry {
  private providers = new Map<string, IProvider>();
  private opts: RegistryOpts;
  constructor(opts: RegistryOpts) {
    this.opts = opts;
    this.register(new SystemOneHttpProvider({
      id: "jev",
      model: "jev-1.13-free",
      url: opts.jevEndpoint ?? "https://opencode.ai/inference/systemone/v1/systemone",
      paid: false, local: false,
      headers: () => {
        if (!opts.jevApiKey) throw new DecisionError("auth", "Missing OPENCODE_API_KEY.", "jev", false);
        return { Authorization: `Bearer ${opts.jevApiKey}` };
      },
    }));
    this.register(new SystemOneHttpProvider({
      id: "clef_local",
      model: "Cloudflare/clef-flash",
      url: (opts.clefLocalUrl ?? "http://127.0.0.1:30000") + "/v1/systemone",
      paid: false, local: true,
    }));
    if (opts.clefHostedVerifiedFree) {
      // Samo uz dokazan free tier + eksplicitno odobrenje.
      this.register(new SystemOneHttpProvider({
        id: "clef_hosted_free",
        model: "clef-flash",
        url: `https://api.cloudflare.com/client/v4/accounts/${opts.clefAccountId}/ai/run/@cf/cloudflare/clef-flash`,
        paid: false, local: false,
        headers: () => {
          if (!opts.clefToken) throw new DecisionError("auth", "Missing CLOUDFLARE_AUTH_TOKEN.", "clef_hosted_free", false);
          return { Authorization: `Bearer ${opts.clefToken}` };
        },
      }));
    }
    if (opts.anyjev?.enabled && opts.anyjev.model) {
      // Opt-in lokalni AnyJev (bridge ili gateway). Bez modela se ne registrira.
      this.register(new AnyjevProvider({
        model: opts.anyjev.model,
        mode: opts.anyjev.mode,
        decisionMode: opts.anyjev.decisionMode,
        url: opts.anyjev.url,
        tau: opts.anyjev.tau,
        maxCotShare: opts.anyjev.maxCotShare,
        cotWindow: opts.anyjev.cotWindow,
      }));
    }
  }
  register(p: IProvider): void {
    const c = p.caps();
    if (!this.opts.allowPaid && (c.paid || PAID_DENYLIST.includes(c.model)))
      throw new DecisionError("paid_blocked", `Paid provider blocked: ${c.id}/${c.model}.`);
    this.providers.set(c.id, p);
  }
  get(id: string): IProvider {
    if (id.startsWith("future_bh_decision_"))
      throw new DecisionError("not_available", `${id} not trained yet — config slot only.`);
    const p = this.providers.get(id);
    if (!p) throw new DecisionError("unknown_provider", `Unknown provider: ${id}.`);
    const c = p.caps();
    if (!this.opts.allowPaid && (c.paid || PAID_DENYLIST.includes(c.model)))
      throw new DecisionError("paid_blocked", `Paid provider blocked: ${c.id}/${c.model}.`);
    return p;
  }
  ids(): string[] {
    return [...this.providers.keys(), "future_bh_decision_2b", "future_bh_decision_4b", "future_bh_decision_9b"];
  }
}
