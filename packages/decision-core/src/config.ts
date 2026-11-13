// Konfiguracija: defaulti + env override. Tajne nikad u YAML-u.
import type { Thresholds } from "./types.ts";

export interface AnyjevConfig {
  enabled: boolean;
  mode: "decider" | "tacit";
  decisionMode: "l0" | "adaptive";
  model: string;
  backend: string;
  url: string;
  tau: number;
  maxCotShare: number | null;
  cotWindow: number | null;
}

export interface DecisionConfig {
  primary: string;
  fallback: string[];
  allow_paid: boolean;
  thresholds: Thresholds;
  privacy: { send_repository_content: boolean; log_prompts: boolean; telemetry: boolean };
  jevEndpoint?: string;
  clefLocalUrl?: string;
  clefHostedVerifiedFree?: boolean;
  anyjev?: AnyjevConfig;
}

export const DEFAULTS: DecisionConfig = {
  primary: "jev",
  fallback: [], // samo Jev Free; ništa drugo se ne poziva automatski
  allow_paid: false,
  thresholds: {
    confidence: 0.8,
    escalation: 0.65,
    abstain: 0.4,
    timeout_ms: 1500,
    max_decisions_per_session: 20,
    cache_ttl_ms: 300_000,
  },
  privacy: { send_repository_content: false, log_prompts: false, telemetry: false },
};

export function loadConfig(partial: Partial<DecisionConfig> = {}): DecisionConfig {
  return {
    ...DEFAULTS,
    ...partial,
    thresholds: { ...DEFAULTS.thresholds, ...(partial.thresholds ?? {}) },
    privacy: { ...DEFAULTS.privacy, ...(partial.privacy ?? {}) },
  };
}

/** Env nadjačava datoteku. DECISION_ALLOW_PAID=true samo eksplicitno. */
export function applyEnv(cfg: DecisionConfig, env: Record<string, string | undefined> = {}): DecisionConfig {
  const out = { ...cfg, thresholds: { ...cfg.thresholds }, privacy: { ...cfg.privacy } };
  if (env.DECISION_PROVIDER) out.primary = env.DECISION_PROVIDER;
  if (env.DECISION_FALLBACK) out.fallback = env.DECISION_FALLBACK.split(",").map((s) => s.trim()).filter(Boolean);
  if (env.DECISION_ALLOW_PAID !== undefined) out.allow_paid = env.DECISION_ALLOW_PAID === "true";
  if (env.DECISION_TIMEOUT_MS) out.thresholds.timeout_ms = Number(env.DECISION_TIMEOUT_MS);
  const aj = { ...(out.anyjev ?? DEFAULT_ANYJEV) };
  if (env.ANYJEV_ENABLED !== undefined) aj.enabled = env.ANYJEV_ENABLED === "true";
  if (env.ANYJEV_MODE === "decider" || env.ANYJEV_MODE === "tacit") aj.mode = env.ANYJEV_MODE;
  if (env.ANYJEV_DECISION_MODE === "l0" || env.ANYJEV_DECISION_MODE === "adaptive") aj.decisionMode = env.ANYJEV_DECISION_MODE;
  if (env.ANYJEV_MODEL !== undefined) aj.model = env.ANYJEV_MODEL;
  if (env.ANYJEV_BACKEND !== undefined) aj.backend = env.ANYJEV_BACKEND;
  if (env.ANYJEV_URL !== undefined) aj.url = env.ANYJEV_URL;
  if (env.ANYJEV_TAU !== undefined) aj.tau = Number(env.ANYJEV_TAU);
  out.anyjev = aj;
  return out;
}

export const DEFAULT_ANYJEV: AnyjevConfig = {
  enabled: false, // opt-in: treba lokalni AnyJev (bridge ili gateway)
  mode: "tacit",
  decisionMode: "l0",
  model: "",
  backend: "transformers",
  url: "http://127.0.0.1:8101",
  tau: 0.5,
  maxCotShare: 0.2,
  cotWindow: 1000,
};

export function registryOptsFromEnv(cfg: DecisionConfig, env: Record<string, string | undefined> = {}): {
  allowPaid: boolean; jevApiKey?: string; jevEndpoint?: string; clefLocalUrl?: string;
  clefHostedVerifiedFree?: boolean; clefAccountId?: string; clefToken?: string;
  anyjev?: AnyjevConfig;
} {
  return {
    allowPaid: cfg.allow_paid,
    ...(env.OPENCODE_API_KEY ? { jevApiKey: env.OPENCODE_API_KEY } : {}),
    ...(cfg.jevEndpoint ? { jevEndpoint: cfg.jevEndpoint } : {}),
    ...(cfg.clefLocalUrl ? { clefLocalUrl: cfg.clefLocalUrl } : {}),
    clefHostedVerifiedFree: cfg.clefHostedVerifiedFree === true,
    ...(env.CLOUDFLARE_ACCOUNT_ID ? { clefAccountId: env.CLOUDFLARE_ACCOUNT_ID } : {}),
    ...(env.CLOUDFLARE_AUTH_TOKEN ? { clefToken: env.CLOUDFLARE_AUTH_TOKEN } : {}),
    ...(cfg.anyjev ? { anyjev: cfg.anyjev } : {}),
  };
}
