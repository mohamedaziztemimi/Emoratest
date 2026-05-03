/**
 * EmoraTest SDK type definitions.
 *
 * These types mirror the backend database schema (events, sessions)
 * and define the SDK's public configuration API.
 */

// ── Event types (matches ck_events_type constraint) ───────────

export type EventType =
  | "mouse_move"
  | "mouse_summary"
  | "click"
  | "scroll"
  | "exit_intent"
  | "visibility";

// ── Event priority for scalability ────────────────────────────────
//
// HIGH_PRIORITY: Always stored, even after MAX_EVENTS_PER_SESSION limit.
// Used for critical behavioral signals (rage clicks, exit intent) and
// aggregated data that preserves analytics quality (mouse summaries).
//
// LOW_PRIORITY: Dropped after MAX_EVENTS_PER_SESSION limit to prevent
// unbounded storage. Raw mousemove/scroll are voluminous but less critical
// when we have aggregated summaries.

export const HIGH_PRIORITY_EVENTS: ReadonlySet<EventType> = new Set([
  "click",           // Rage click detection MUST always work
  "exit_intent",     // Critical for abandonment analysis
  "visibility",      // Tab switching = exit signal
  "mouse_summary",   // Aggregated velocity data (bypasses limit)
]);

export const LOW_PRIORITY_EVENTS: ReadonlySet<EventType> = new Set([
  "mouse_move",      // Raw mousemove (voluminous)
  "scroll",          // Raw scroll (voluminous)
]);

// ── Outcome priority system (higher number = higher priority) ─────

export const OUTCOME_PRIORITY: Readonly<Record<OutcomeType, number>> = {
  purchase: 100,
  checkout_completed: 90,
  signup: 80,
  trial_started: 70,
  lead_generated: 60,
  demo_booked: 50,
  abandon: 0,
} as const;

export type OutcomeWithPriority = OutcomeType & keyof typeof OUTCOME_PRIORITY;

/** Get priority number for an outcome (higher = more important). */
export function getOutcomePriority(outcome: OutcomeType): number {
  return OUTCOME_PRIORITY[outcome] ?? 0;
}

/** Check if outcome A should override outcome B based on priority. */
export function shouldOverrideOutcome(current: OutcomeType, incoming: OutcomeType): boolean {
  return getOutcomePriority(incoming) > getOutcomePriority(current);
}

// ── Micro-survey types ───────────────────────────────────────────────

export type SurveyTrigger = "exit_intent" | "scroll_75" | "time_30s";
export type SurveyPosition = "bottom-right" | "bottom-left";

export interface SurveyConfig {
  /** When to show the survey */
  trigger: SurveyTrigger;
  /** Only show on these page paths (empty = all pages) */
  pageFilter: string[];
  /** What % of sessions see the survey (0-1) */
  sampleRate: number;
  /** Widget position on screen */
  position: SurveyPosition;
}

// ── Auto-detection patterns (strict path matching) ────────────────

export interface OutcomePattern {
  path: string;
  outcome: OutcomeType;
}

export const DEFAULT_OUTCOME_PATTERNS: readonly OutcomePattern[] = [
  { path: "/success", outcome: "purchase" as const },
  { path: "/thank-you", outcome: "purchase" as const },
  { path: "/thankyou", outcome: "purchase" as const },
  { path: "/confirmation", outcome: "purchase" as const },
  { path: "/complete", outcome: "purchase" as const },
  { path: "/checkout/success", outcome: "checkout_completed" as const },
  { path: "/checkout/complete", outcome: "checkout_completed" as const },
  { path: "/order/confirm", outcome: "checkout_completed" as const },
  { path: "/order/confirmed", outcome: "checkout_completed" as const },
  { path: "/payment/success", outcome: "checkout_completed" as const },
  { path: "/signup/success", outcome: "signup" as const },
  { path: "/signup/complete", outcome: "signup" as const },
  { path: "/registered", outcome: "signup" as const },
  { path: "/demo/booked", outcome: "demo_booked" as const },
  { path: "/demo/confirmed", outcome: "demo_booked" as const },
  { path: "/meeting/scheduled", outcome: "demo_booked" as const },
  { path: "/lead/success", outcome: "lead_generated" as const },
  { path: "/trial/started", outcome: "trial_started" as const },
  { path: "/subscribed", outcome: "trial_started" as const },
] as const;

// ── Scalability constants ────────────────────────────────────────────

export const DEFAULT_SAMPLING_RATE = 0.2; // Track 20% of sessions
export const MAX_EVENTS_PER_SESSION = 1000;
export const MAX_SESSION_DURATION_MS = 30 * 60 * 1000; // 30 minutes
export const DEFAULT_FLUSH_INTERVAL_MS = 5000; // 5 seconds
export const DEFAULT_THROTTLE_MS = 300; // 300ms for mousemove/scroll

// ── Events ───────────────────────────────────────────────────────────

export interface RawEvent {
  type: EventType;
  ts: string; // ISO 8601
  x?: number | null;
  y?: number | null;
  velocity?: number | null;

  // Backward compatibility: original element identifier
  element_id?: string | null;

  // Semantic enrichment (NEW)
  /** Human-readable label from element (innerText, aria-label, alt, etc.) */
  label?: string | null;
  /** Type of element (button, link, input, image, container) */
  element_type?: "button" | "link" | "input" | "image" | "container" | null;
  /** Section where element is located (hero, navbar, footer, etc.) */
  section?: string | null;
  /** Full CSS selector for backward compatibility */
  selector?: string | null;

  metadata?: Record<string, unknown> | null;
}

export interface BatchPayload {
  session_id: string;
  events: RawEvent[];
  page_url?: string;  // Current page URL (for session tracking)
}

// ── Session ───────────────────────────────────────────────────────

export type OutcomeType =
  | "purchase"
  | "abandon"
  | "signup"
  | "checkout_completed"
  | "demo_booked"
  | "lead_generated"
  | "trial_started";

export interface SessionCreatePayload {
  page_url: string;
  started_at: string;
  country_code?: string | null;
  device_type?: string | null;
}

export interface SessionCreateResponse {
  session_id: string;
  survey?: {
    enabled: boolean;
    trigger?: "exit_intent" | "scroll_75" | "time_30s";
    sample_rate?: number;
    pages?: string[];
  } | null;
}

// ── SDK configuration ───────────────────────────────────────────────

export interface EmoraTestConfig {
  /** Merchant SDK key (sent raw, hashed server-side for auth). */
  sdkKey: string;

  /** Backend API base URL. Default: https://emoratest.com */
  apiUrl?: string;

  /** Event flush interval in ms. Default: 5000 (5 seconds) */
  flushIntervalMs?: number;

  /** Max events per batch. Default: 50 */
  maxBatchSize?: number;

  /** Throttle ms for mousemove/scroll events. Default: 300 */
  mouseMoveThrottleMs?: number;

  /** Enable debug logging. Default: false */
  debug?: boolean;

  /** Disable all tracking (opt-out). Default: false */
  disabled?: boolean;

  /** Sampling rate (0-1). Default: 0.2 (20% of sessions tracked) */
  samplingRate?: number;

  /** Max events per session before dropping low-priority events. Default: 1000 */
  maxEventsPerSession?: number;

  /** Max session duration in ms before stopping tracking. Default: 30 minutes */
  maxSessionDurationMs?: number;

  /** Custom outcome detection patterns (strict path matching) */
  outcomePatterns?: OutcomePattern[];

  /** Micro-survey configuration (optional) */
  survey?: SurveyConfig;

  /** Require user consent before tracking (GDPR mode). Default: false */
  requireConsent?: boolean;
}

// ── Feature Flags ─────────────────────────────────────────────────

export interface FlagEvaluationRequest {
  user_context: {
    visitor_id: string;
    session_id?: string;
    [key: string]: unknown;
  };
  environment?: string;
}

export interface FlagEvaluationResponse {
  flag_key: string;
  enabled: boolean;
  variant: string | null;
  reason: string;
}

export interface FlagEvaluationResult {
  assigned: boolean;
  variant: string | null;
}
