/**
 * Conversiono API Client (CONV-51).
 *
 * Centralized HTTP client for all backend API calls.
 * All requests include the SDK key hash in X-SDK-Key header.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const REQUEST_TIMEOUT = 15_000; // 15s timeout

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

function getSdkKey(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("conversiono_sdk_key") || "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const sdkKey = getSdkKey();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(sdkKey ? { "X-SDK-Key": sdkKey } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(res.status, body.detail || res.statusText);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

// ── Sessions ─────────────────────────────────────────────────

export interface SessionListItem {
  id: string;
  page_url: string;
  started_at: string;
  ended_at: string | null;
  outcome: string;
  abandonment_risk: number | null;
  friction_score: number | null;
  intent_label: string | null;
  country_code: string | null;
  device_type: string | null;
}

export interface SessionListResponse {
  sessions: SessionListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface SessionFeatures {
  hesitation_score: number | null;
  price_dwell_time_s: number | null;
  rage_click_score: number | null;
  scroll_retreat_count: number | null;
  exit_intent_count: number | null;
  checkout_hesitation_s: number | null;
  velocity_variance: number | null;
  session_duration_s: number | null;
  computed_at: string | null;
}

export interface EventOut {
  id: number;
  type: string;
  ts: string;
  x: number | null;
  y: number | null;
  velocity: number | null;
  element_id: string | null;
  metadata: Record<string, unknown> | null;
}

export interface SessionDetail extends SessionListItem {
  events: EventOut[];
  features: SessionFeatures | null;
}

export interface SessionFilters {
  page?: number;
  page_size?: number;
  outcome?: string;
  risk_min?: number;
  risk_max?: number;
  date_from?: string;
  date_to?: string;
  device_type?: string;
}

export function fetchSessions(filters: SessionFilters = {}): Promise<SessionListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== "") params.set(k, String(v));
  });
  return request(`/dashboard/sessions?${params}`);
}

export function fetchSessionDetail(id: string): Promise<SessionDetail> {
  return request(`/dashboard/sessions/${id}`);
}

// ── Analytics ────────────────────────────────────────────────

export interface FunnelStep {
  step: string;
  sessions: number;
  drop_off: number;
  drop_off_rate: number;
  avg_friction_score: number | null;
}

export interface FunnelResponse {
  steps: FunnelStep[];
  total_sessions: number;
  conversion_rate: number;
}

export interface FrictionMapItem {
  element_id: string;
  event_count: number;
  avg_hesitation: number;
  click_count: number;
  rage_click_count: number;
  rage_click_rate: number;
}

export interface FrictionMapResponse {
  elements: FrictionMapItem[];
  total_elements: number;
}

export interface CohortBucket {
  label: string;
  session_count: number;
  purchase_count: number;
  abandon_count: number;
  conversion_rate: number;
  avg_abandonment_risk: number | null;
  avg_friction_score: number | null;
}

export interface CohortResponse {
  dimension: string;
  buckets: CohortBucket[];
  total_sessions: number;
  overall_conversion_rate: number;
}

export interface RiskBucket {
  range_label: string;
  range_min: number;
  range_max: number;
  session_count: number;
  conversion_rate: number;
}

export interface RiskDistributionResponse {
  buckets: RiskBucket[];
  total_sessions: number;
  avg_risk: number | null;
  median_risk: number | null;
}

export function fetchFunnel(dateFrom?: string, dateTo?: string): Promise<FunnelResponse> {
  const params = new URLSearchParams();
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return request(`/dashboard/analytics/funnel?${params}`);
}

export function fetchFrictionMap(limit = 50): Promise<FrictionMapResponse> {
  return request(`/dashboard/analytics/friction-map?limit=${limit}`);
}

export function fetchCohorts(dimension: string): Promise<CohortResponse> {
  return request(`/analytics/cohorts?dimension=${dimension}`);
}

export function fetchRiskDistribution(buckets = 10): Promise<RiskDistributionResponse> {
  return request(`/analytics/risk-distribution?buckets=${buckets}`);
}

// ── Experiments ──────────────────────────────────────────────

export interface Experiment {
  id: string;
  merchant_id: string;
  title: string;
  hypothesis: string | null;
  page_element: string | null;
  friction_type: string | null;
  variant_a: string | null;
  variant_b: string | null;
  result: string | null;
  conversion_delta: number | null;
  sample_size: number | null;
  ran_at: string | null;
  source: string | null;
  created_at: string;
}

export interface ExperimentListResponse {
  experiments: Experiment[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExperimentStats {
  experiment_id: string;
  title: string;
  result: string | null;
  conversion_delta: number | null;
  sample_size: number | null;
  confidence_level: number | null;
  is_significant: boolean;
  p_value: number | null;
  power: number | null;
  recommendation: string;
}

export function fetchExperiments(page = 1): Promise<ExperimentListResponse> {
  return request(`/experiments?page=${page}&page_size=20`);
}

export function fetchExperiment(id: string): Promise<Experiment> {
  return request(`/experiments/${id}`);
}

export function createExperiment(data: {
  title: string;
  hypothesis?: string;
  friction_type?: string;
  variant_a?: string;
  variant_b?: string;
}): Promise<Experiment> {
  return request("/experiments", { method: "POST", body: JSON.stringify(data) });
}

export function deleteExperiment(id: string): Promise<void> {
  return request(`/experiments/${id}`, { method: "DELETE" });
}

export function fetchExperimentStats(id: string): Promise<ExperimentStats> {
  return request(`/experiments/${id}/stats`);
}

// ── Interventions ────────────────────────────────────────────

export interface InterventionRec {
  intervention_id: string;
  name: string;
  description: string;
  trigger: string;
  priority: number;
  psychological_basis: string;
  estimated_lift: number | null;
}

export interface InterventionRecommendations {
  session_id: string;
  abandonment_risk: number | null;
  friction_score: number | null;
  intent_label: string | null;
  recommendations: InterventionRec[];
}

export interface InterventionStats {
  intervention_id: string;
  total_triggers: number;
  converted: number;
  dismissed: number;
  ignored: number;
  bounced: number;
  conversion_rate: number;
  avg_conversion_delta: number | null;
}

export function fetchInterventionRecs(sessionId: string): Promise<InterventionRecommendations> {
  return request(`/interventions/recommend/${sessionId}`);
}

export function fetchInterventionStats(): Promise<InterventionStats[]> {
  return request("/interventions/stats");
}

// ── Merchant ─────────────────────────────────────────────────

export interface MerchantProfile {
  id: string;
  email: string;
  shop_domain: string;
  plan: string;
  is_active: boolean;
  created_at: string;
}

export interface UsageSummary {
  total_sessions: number;
  total_events: number;
  total_experiments: number;
  active_sessions_today: number;
  plan: string;
}

export function fetchMerchantProfile(): Promise<MerchantProfile> {
  return request("/merchants/me");
}

export function fetchUsage(): Promise<UsageSummary> {
  return request("/merchants/usage");
}

export function rotateKey(): Promise<{ new_sdk_key: string; rotated_at: string }> {
  return request("/merchants/rotate-key", { method: "POST" });
}

export { ApiError };
