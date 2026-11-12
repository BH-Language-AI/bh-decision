// Interni tipovi / Internal types — ne ovise o provideru / provider-independent.
// Ne generirati chain-of-thought; kratka objašnjenja dovoljna.

export type InternalQuestionType = "categorical" | "boolean" | "score";

export interface InternalQuestion {
  id: string;
  type: InternalQuestionType;
  /** Opis zadatka za model / what to decide. */
  instructions?: string;
  /** Za categorical: mapiranje opcija; za score: poredana legenda. */
  options?: Record<string, string> | string[];
}

export interface DecisionState {
  task: string;
  language?: string;
  available_tools?: string[];
  context?: Record<string, unknown>;
}

export interface DecisionRequest {
  state: DecisionState;
  questions: InternalQuestion[];
}

export interface QuestionDecision {
  selected: string | boolean | number;
  probabilities: Record<string, number>;
  confidence?: number;
}

export interface DecisionResult {
  decision_id: string;
  provider: string;
  model: string;
  model_version?: string;
  decisions: Record<string, QuestionDecision>;
  confidence: number;
  latency_ms: number;
  fallback_used: boolean;
  requires_escalation: boolean;
  abstained: string[];
  usage?: Record<string, unknown>;
  timestamp: string;
}

// SystemOne (stvarni format / actual wire format): noul | choice | score.
export type SysQuestionType = "noul" | "choice" | "score";
export interface SysQuestion {
  type: SysQuestionType;
  instructions?: string;
  criteria?: Record<string, string> | string[];
}
export interface SysRequest {
  model: string;
  state: unknown;
  questions: Record<string, SysQuestion>;
}
export interface SysAnswer {
  choice?: string;
  noul?: number;
  score?: number;
  probabilities?: Record<string, number>;
  confidence?: number;
  legend?: string[];
}
export interface SysResponse {
  model?: string;
  answers?: Record<string, SysAnswer>;
  usage?: Record<string, unknown>;
}

export interface ProviderResult {
  response: SysResponse;
  model_version?: string;
  latency_ms: number;
}

export interface ProviderCaps {
  id: string;
  model: string;
  paid: boolean;
  local: boolean;
  enabled: boolean;
}

export interface IProvider {
  caps(): ProviderCaps;
  decide(req: SysRequest, opts: CallOpts): Promise<ProviderResult>;
  health(): Promise<{ ok: boolean; latency_ms?: number; reason?: string }>;
}

export interface CallOpts {
  timeout_ms: number;
  signal?: AbortSignal;
}

export interface Thresholds {
  confidence: number;
  escalation: number;
  abstain: number;
  timeout_ms: number;
  max_decisions_per_session: number;
  cache_ttl_ms: number;
}

export interface ProviderStatus {
  id: string;
  enabled: boolean;
  healthy: boolean | null;
  calls: number;
  errors: number;
  fallbacks_from: number;
  avg_latency_ms: number | null;
  breaker_open: boolean;
}

export class DecisionError extends Error {
  code: string;
  provider?: string;
  retryable: boolean;
  constructor(code: string, message: string, provider?: string, retryable = false) {
    super(message);
    this.code = code;
    this.provider = provider;
    this.retryable = retryable;
  }
}
