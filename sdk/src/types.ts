/**
 * Conversiono SDK type definitions.
 *
 * These types mirror the backend database schema (events, sessions)
 * and define the SDK's public configuration API.
 */

// ── Event types (matches ck_events_type constraint) ───────────

export type EventType =
  | "mouse_move"
  | "click"
  | "scroll"
  | "exit_intent"
  | "visibility";

export interface RawEvent {
  type: EventType;
  ts: string; // ISO 8601
  x?: number | null;
  y?: number | null;
  velocity?: number | null;
  element_id?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface BatchPayload {
  session_id: string;
  events: RawEvent[];
}

// ── Session ───────────────────────────────────────────────────

export interface SessionCreatePayload {
  merchant_id: string;
  page_url: string;
  started_at: string;
  country_code?: string | null;
  device_type?: string | null;
}

export interface SessionCreateResponse {
  session_id: string;
}

// ── SDK configuration ─────────────────────────────────────────

export interface ConversionoConfig {
  /** Merchant SDK key (will be SHA-256 hashed before sending). */
  sdkKey: string;

  /** Backend API base URL. Default: window.location.origin */
  apiUrl?: string;

  /** Event flush interval in ms. Default: 2000 */
  flushIntervalMs?: number;

  /** Max events per batch. Default: 50 */
  maxBatchSize?: number;

  /** Throttle ms for mousemove events. Default: 100 */
  mouseMoveThrottleMs?: number;

  /** Enable debug logging. Default: false */
  debug?: boolean;

  /** Disable all tracking (opt-out). Default: false */
  disabled?: boolean;
}

// ── Resolved config (all fields required) ─────────────────────

export interface ResolvedConfig {
  sdkKey: string;
  sdkKeyHash: string;
  apiUrl: string;
  flushIntervalMs: number;
  maxBatchSize: number;
  mouseMoveThrottleMs: number;
  debug: boolean;
  disabled: boolean;
}
