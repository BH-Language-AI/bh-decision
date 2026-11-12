// Konfiguracija: defaulti + env override. Tajne nikad u YAML-u.
import type { Thresholds } from "./types.ts";

export interface DecisionConfig {
  primary: string;
  fallback: string[];
  allow_paid: boolean;
  thresholds: Thresholds;
  privacy: { send_repository_content: boolean; log_prompts: boolean; telemetry: boolean };
  jevEndpoint?: string;
  clefLocalUrl?: string;
  clefHostedVerifiedFree?: boolean;
}

export const DEFAULTS: DecisionConfig = {
  primary: "jev",
  fallback: ["clef_local"],
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
  return out;
}

export function registryOptsFromEnv(cfg: DecisionConfig, env: Record<string, string | undefined> = {}): {
  allowPaid: boolean; jevApiKey?: string; jevEndpoint?: string; clefLocalUrl?: string;
  clefHostedVerifiedFree?: boolean; clefAccountId?: string; clefToken?: string;
} {
  return {
    allowPaid: cfg.allow_paid,
    ...(env.OPENCODE_API_KEY ? { jevApiKey: env.OPENCODE_API_KEY } : {}),
    ...(cfg.jevEndpoint ? { jevEndpoint: cfg.jevEndpoint } : {}),
    ...(cfg.clefLocalUrl ? { clefLocalUrl: cfg.clefLocalUrl } : {}),
    clefHostedVerifiedFree: cfg.clefHostedVerifiedFree === true,
    ...(env.CLOUDFLARE_ACCOUNT_ID ? { clefAccountId: env.CLOUDFLARE_ACCOUNT_ID } : {}),
    ...(env.CLOUDFLARE_AUTH_TOKEN ? { clefToken: env.CLOUDFLARE_AUTH_TOKEN } : {}),
  };
}
