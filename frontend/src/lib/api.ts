/**
 * EmoraTest API Client
 *
 * Centralized HTTP client for all backend API calls.
 * Uses httpOnly cookies for authentication - no localStorage tokens.
 *
 * Environment variables:
 * - NEXT_PUBLIC_API_URL: Backend API URL (optional)
 * - If not set, uses same-origin (works for monolithic deployments)
 */

const REQUEST_TIMEOUT = 10_000; // 10s timeout for production

// Use same-origin for all requests (works for www.emoratest.com/api/v1/*)
// In production, frontend and backend are on the same domain
const API_BASE = "";

// Export for use in components
export { API_BASE };

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    // Build URL: use API_BASE if set, otherwise use relative path (same-origin)
    const url = API_BASE ? `${API_BASE}/api/v1${path}` : `/api/v1${path}`;
    const res = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Send httpOnly cookies
      signal: options.signal ?? controller.signal,
    });

    if (!res.ok) {
      // Don't redirect here - middleware handles it
      const body = await res.json().catch(() => ({ detail: res.statusText }));

      // Handle backend's custom validation error format
      if (body.error === "Validation Error" && Array.isArray(body.detail)) {
        const errors = body.detail.map((e: any) =>
          `${e.field || 'field'}: ${e.message || 'invalid value'}`
        ).join('; ');
        throw new ApiError(res.status, errors);
      }

      // Handle standard Pydantic validation format
      const detail = body.detail;
      let errorMessage: string;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (Array.isArray(detail)) {
        // Check if it's backend format {field, message} or Pydantic format {loc, msg}
        if (detail.length > 0 && 'field' in detail[0]) {
          errorMessage = detail.map((e: any) => `${e.field || 'field'}: ${e.message || 'invalid'}`).join('; ');
        } else if (detail.length > 0 && 'loc' in detail[0]) {
          errorMessage = detail.map((e: any) => `${e.loc?.join('.') || 'field'} - ${e.msg || 'invalid'}`).join(', ');
        } else {
          errorMessage = JSON.stringify(detail);
        }
      } else if (typeof body === 'object' && body !== null) {
        errorMessage = JSON.stringify(body);
      } else {
        errorMessage = res.statusText || `HTTP ${res.status}`;
      }
      throw new ApiError(res.status, errorMessage);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
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
  primary_emotion: string | null;
  emotion_confidence: number | null;
  valence: number | null;
  arousal: number | null;
  ip_address: string | null;
  user_agent: string | null;
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
  label: string | null;
  element_type: string | null;
  section: string | null;
  selector: string | null;
  // Human-readable description from enrichment service (preferred over client-side formatting)
  readable_description: string | null;
}

export interface SessionDetail extends SessionListItem {
  events: EventOut[];
  features: SessionFeatures | null;
  emotion_scores?: Record<string, number>;
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
  emotion?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
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
  return request(`/analytics/funnel?${params}`);
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

export interface ElementEmotionItem {
  element_id: string;
  label: string | null;
  element_type: string | null;
  section: string | null;
  event_count: number;
  click_count: number;
  rage_click_count: number;
  rage_click_rate: number;
  avg_hesitation: number;
  dominant_emotion: string | null;
  emotion_confidence: number | null;
  emotion_breakdown: Record<string, number> | null;
  session_count: number;
}

export interface ElementEmotionResponse {
  elements: ElementEmotionItem[];
  total_elements: number;
  page_url: string | null;
}

// ── Why-Analysis ────────────────────────────────────────────────

export interface EmotionConversionItem {
  emotion: string;
  total_sessions: number;
  converted: number;
  abandoned: number;
  conversion_rate: number;
  avg_friction: number | null;
  avg_abandonment_risk: number | null;
}

export interface EmotionConversionResponse {
  items: EmotionConversionItem[];
  total_sessions: number;
  overall_conversion_rate: number;
}

export interface DropOffReasonItem {
  page_url: string;
  emotion: string;
  sessions: number;
  drop_off_rate: number;
  avg_friction: number | null;
  avg_abandonment_risk: number | null;
}

export interface DropOffReasonsResponse {
  reasons: DropOffReasonItem[];
  total_patterns: number;
}

export interface WhyAnalysisSummary {
  total_sessions: number;
  sessions_with_emotion: number;
  overall_conversion_rate: number;
  top_drop_off_emotion: string | null;
  top_drop_off_emotion_rate: number | null;
  top_converting_emotion: string | null;
  top_converting_emotion_rate: number | null;
  avg_friction_abandoned: number | null;
  avg_friction_converted: number | null;
}

export interface EmotionTrendDay {
  date: string;
  emotions: Record<string, number>;
  total: number;
  conversion_rate: number | null;
}

export interface EmotionTrendResponse {
  days: EmotionTrendDay[];
  emotions_seen: string[];
}

export function fetchElementEmotions(pageUrl?: string): Promise<ElementEmotionResponse> {
  const params = new URLSearchParams();
  if (pageUrl) params.set("page_url", pageUrl);
  const qs = params.toString();
  return request(`/dashboard/analytics/element-emotions${qs ? `?${qs}` : ""}`);
}

export async function fetchWhyAnalysisSummary(dateFrom?: string, dateTo?: string): Promise<WhyAnalysisSummary> {
  const params = new URLSearchParams();
  if (dateFrom) params.append("date_from", dateFrom);
  if (dateTo) params.append("date_to", dateTo);
  const qs = params.toString();
  return request<WhyAnalysisSummary>(`/dashboard/analytics/why-analysis/summary${qs ? `?${qs}` : ""}`);
}

export async function fetchEmotionConversion(dateFrom?: string, dateTo?: string): Promise<EmotionConversionResponse> {
  const params = new URLSearchParams();
  if (dateFrom) params.append("date_from", dateFrom);
  if (dateTo) params.append("date_to", dateTo);
  const qs = params.toString();
  return request<EmotionConversionResponse>(`/dashboard/analytics/why-analysis/emotion-conversion${qs ? `?${qs}` : ""}`);
}

export async function fetchDropOffReasons(dateFrom?: string, dateTo?: string): Promise<DropOffReasonsResponse> {
  const params = new URLSearchParams();
  if (dateFrom) params.append("date_from", dateFrom);
  if (dateTo) params.append("date_to", dateTo);
  const qs = params.toString();
  return request<DropOffReasonsResponse>(`/dashboard/analytics/why-analysis/drop-off-reasons${qs ? `?${qs}` : ""}`);
}

export async function fetchEmotionTrend(dateFrom?: string, dateTo?: string): Promise<EmotionTrendResponse> {
  const params = new URLSearchParams();
  if (dateFrom) params.append("date_from", dateFrom);
  if (dateTo) params.append("date_to", dateTo);
  const qs = params.toString();
  return request<EmotionTrendResponse>(`/dashboard/analytics/why-analysis/emotion-trend${qs ? `?${qs}` : ""}`);
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
  experiment_type: string | null;
  n_variants: number | null;
  flicker_free: boolean | null;
  is_active: boolean | null;
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
  friction_type?: "hesitation" | "rage_click" | "scroll_retreat" | "exit_intent" | "checkout_delay";
  variant_a?: string;
  variant_b?: string;
}): Promise<Experiment> {
  const cleanData = Object.fromEntries(
    Object.entries(data).filter(([_, v]) => v !== undefined)
  );
  return request("/experiments", { method: "POST", body: JSON.stringify(cleanData) });
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

// ── Auth ────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string;
  token_type: string;
  merchant_id: string;
  email: string;
  shop_domain: string;
  plan: string;
  sdk_key?: string;
  onboarding_completed: boolean;
}

export interface AuthMeResponse {
  id: string;
  email: string;
  shop_domain: string;
  plan: string;
  is_active: boolean;
  gdpr_consent: boolean;
  onboarding_completed: boolean;
  created_at: string;
}

export function authRegister(data: {
  email: string;
  password: string;
  shop_domain: string;
  plan?: string;
  gdpr_consent?: boolean;
}): Promise<AuthResponse> {
  return request("/auth/register", { method: "POST", body: JSON.stringify(data) });
}

export function authLogin(data: { email: string; password: string }): Promise<AuthResponse> {
  return request("/auth/login", { method: "POST", body: JSON.stringify(data) });
}

export function authMe(): Promise<AuthMeResponse> {
  return request("/auth/me");
}

export function authCompleteOnboarding(): Promise<{ status: string }> {
  return request("/auth/onboarding-complete", { method: "POST" });
}

export function gdprConsent(): Promise<{ status: string; consented_at: string }> {
  return request("/auth/gdpr/consent", { method: "POST" });
}

export function gdprExport(): Promise<unknown> {
  return request("/auth/gdpr/export");
}

export function gdprDelete(): Promise<{ status: string; message: string }> {
  return request("/auth/gdpr/delete", { method: "DELETE" });
}

// ── Feature Flags ────────────────────────────────────────────────

export interface FeatureFlag {
  id: string;
  key: string;
  name: string;
  description: string | null;
  status: "active" | "inactive" | "archived";
  rollout_percentage: number;
  targeting_rules: any[] | null;
  variants: any[] | null;
  kill_switch: boolean;
  environments: Record<string, any> | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeatureFlagListResponse {
  flags: FeatureFlag[];
  total: number;
  page: number;
  page_size: number;
}

export function fetchFlags(page = 1, statusFilter?: string): Promise<FeatureFlagListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: "50" });
  if (statusFilter) params.set("status_filter", statusFilter);
  return request(`/flags?${params}`);
}

export function createFlag(data: {
  key: string;
  name: string;
  description?: string;
  status?: string;
  rollout_percentage?: number;
}): Promise<FeatureFlag> {
  return request("/flags", { method: "POST", body: JSON.stringify(data) });
}

export function updateFlag(key: string, data: Partial<{
  name: string;
  description: string;
  status: string;
  rollout_percentage: number;
  kill_switch: boolean;
}>): Promise<FeatureFlag> {
  return request(`/flags/${key}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteFlag(key: string): Promise<void> {
  return request(`/flags/${key}/archive`, { method: "POST" });
}

export function toggleKillSwitch(key: string, enabled: boolean): Promise<FeatureFlag> {
  return request(`/flags/${key}/kill`, { method: "POST", body: JSON.stringify({ enabled }) });
}

export function updateRollout(key: string, percentage: number): Promise<FeatureFlag> {
  return request(`/flags/${key}/rollout`, { method: "POST", body: JSON.stringify({ percentage }) });
}

export interface VariantResult {
  variant: string;
  exposures: number;
  conversions: number;
  conversion_rate: number;
}

export interface FlagResultsResponse {
  flag_key: string;
  flag_id: string;
  days: number;
  variants: VariantResult[];
  winning_variant: string | null;
  total_exposures: number;
  total_conversions: number;
  overall_conversion_rate: number;
}

export function fetchFlagResults(key: string, days = 30): Promise<FlagResultsResponse> {
  return request(`/flags/${key}/results?days=${days}`);
}

export interface FlagExposureStats {
  flag_key: string;
  days: number;
  total_users: number;
  exposed_users: number;
  exposure_percentage: number;
  variant_breakdown: Record<string, number>;
}

export function fetchFlagStats(key: string, days = 30): Promise<FlagExposureStats> {
  return request(`/flags/${key}/stats?days=${days}`);
}

// ── Segments ────────────────────────────────────────────────

export interface Segment {
  id: string;
  merchant_id: string;
  name: string;
  description: string | null;
  conditions: Record<string, any>;
  segment_type: "static" | "dynamic" | "emotional";
  estimated_size: number | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface SegmentListResponse {
  segments: Segment[];
  total: number;
  page: number;
  page_size: number;
}

export function fetchSegments(page = 1, typeFilter?: string): Promise<SegmentListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: "50" });
  if (typeFilter) params.set("type_filter", typeFilter);
  return request(`/segments?${params}`);
}

export function createSegment(data: {
  name: string;
  description?: string;
  segment_type?: string;
}): Promise<Segment> {
  return request("/segments", { method: "POST", body: JSON.stringify(data) });
}

export function updateSegment(id: string, data: Partial<{
  name: string;
  description: string;
  is_active: boolean;
}>): Promise<Segment> {
  return request(`/segments/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteSegment(id: string): Promise<void> {
  return request(`/segments/${id}`, { method: "DELETE" });
}

// ── Integrations ────────────────────────────────────────────────

export interface Integration {
  id: string;
  name: string;
  integration_type: string;
  config: Record<string, any>;
  events: string[];
  is_active: boolean;
  created_at: string | null;
}

export interface IntegrationListResponse {
  integrations: Integration[];
  total: number;
}

export function fetchIntegrations(typeFilter?: string): Promise<IntegrationListResponse> {
  const params = new URLSearchParams();
  if (typeFilter) params.set("type_filter", typeFilter);
  const qs = params.toString();
  return request(`/integrations${qs ? `?${qs}` : ""}`);
}

export function createIntegration(data: {
  name: string;
  integration_type: string;
  config: Record<string, any>;
  events?: string[];
}): Promise<Integration> {
  return request("/integrations", { method: "POST", body: JSON.stringify(data) });
}

export function deleteIntegration(id: string): Promise<void> {
  return request(`/integrations/${id}`, { method: "DELETE" });
}

// ── Multi-Armed Bandits ────────────────────────────────────────────────

export type BanditAlgorithm = "thompson_sampling" | "ucb1" | "epsilon_greedy";
export type BanditStatus = "active" | "paused" | "completed";

export interface BanditVariant {
  name: string;
  variant_id: string;
  successes: number;
  trials: number;
  conversion_rate: number;
  allocation_percentage: number;
}

export interface Bandit {
  id: string;
  merchant_id: string;
  name: string;
  description: string | null;
  algorithm: BanditAlgorithm;
  epsilon: number;
  exploration_factor: number;
  min_samples_per_arm: number;
  variants: BanditVariant[];
  status: BanditStatus;
  total_trials: number;
  converged: boolean;
  winner_variant_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface BanditListResponse {
  bandits: Bandit[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateBanditPayload {
  name: string;
  description?: string;
  algorithm?: BanditAlgorithm;
  epsilon?: number;
  exploration_factor?: number;
  min_samples_per_arm?: number;
  variants: Array<{
    name: string;
    variant_id: string;
    successes?: number;
    trials?: number;
  }>;
}

export interface UpdateBanditPayload {
  name?: string;
  description?: string;
  status?: BanditStatus;
  epsilon?: number;
  exploration_factor?: number;
  min_samples_per_arm?: number;
}

export function fetchBandits(page = 1, statusFilter?: string): Promise<BanditListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: "50" });
  if (statusFilter) params.set("status_filter", statusFilter);
  return request(`/bandits?${params}`);
}

export function fetchBandit(id: string): Promise<Bandit> {
  return request(`/bandits/${id}`);
}

export function createBandit(data: CreateBanditPayload): Promise<Bandit> {
  return request("/bandits", { method: "POST", body: JSON.stringify(data) });
}

export function updateBandit(id: string, data: UpdateBanditPayload): Promise<Bandit> {
  return request(`/bandits/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteBandit(id: string): Promise<void> {
  return request(`/bandits/${id}`, { method: "DELETE" });
}

// ── Diagnosis .  Behavioral Signal to Actionable Insight ──────

export interface EvidenceItem {
  type: string;
  value: number | string;
  label: string;
  element: string | null;
  session_ids: string[];
}

export interface RootCause {
  primary_cause: string;
  explanation: string;
  contributing_factors: string[];
}

export interface ActionItem {
  title: string;
  description: string;
  type: string;
  link: string | null;
}

export interface ProblemSummary {
  title: string;
  page_url: string;
  page_name: string;
  affected_users_pct: number;
  severity: string;
  estimated_lost_revenue: string | null;
}

export interface DiagnosisResponse {
  summary: ProblemSummary;
  evidence: EvidenceItem[];
  root_cause: RootCause;
  actions: ActionItem[];
  supporting_charts: Record<string, unknown>;
  generated_at: string;
}

export interface IssueListItem {
  id: string;
  title: string;
  page_url: string;
  affected_users: number;
  severity: string;
}

export interface IssuesListResponse {
  issues: IssueListItem[];
  total_issues: number;
  high_severity_count: number;
}

export async function fetchPrimaryDiagnosis(
  merchantId: string,
  hours = 24
): Promise<DiagnosisResponse> {
  // merchant_id is extracted from JWT token by backend
  return request<DiagnosisResponse>(`/dashboard/diagnosis/primary?hours=${hours}`);
}

export async function fetchIssuesList(
  merchantId: string,
  hours = 24
): Promise<IssuesListResponse> {
  // merchant_id is extracted from JWT token by backend
  return request<IssuesListResponse>(`/dashboard/diagnosis/issues?hours=${hours}`);
}

// ── New Diagnosis API (pages with issues) ────────────────────────

export interface DiagnosisIssueItem {
  type: string;
  severity: "critical" | "warning" | "info";
  title: string;
  description: string;
  affected_sessions: number;
  affected_percentage: number;
  recommendation: string;
}

export interface DiagnosisPageItem {
  page_url: string;
  page_name: string;
  total_sessions: number;
  issue_count: number;
  critical_count: number;
  warning_count: number;
  issues: DiagnosisIssueItem[];
}

export interface PagesDiagnosisResponse {
  pages: DiagnosisPageItem[];
  total_pages: number;
  critical_issues: number;
  warning_issues: number;
  info_issues: number;
}

export async function fetchPagesDiagnosis(
  days = 7,
  limit = 20
): Promise<PagesDiagnosisResponse> {
  return request<PagesDiagnosisResponse>(`/dashboard/diagnosis?days=${days}&limit=${limit}`);
}

// ── User Feedback ─────────────────────────────────────────────────

export interface FeedbackPageItem {
  page_url: string;
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
}

export interface MLComparisonItem {
  predicted_emotion: string;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  total: number;
}

export interface FeedbackSummaryResponse {
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  by_page: FeedbackPageItem[];
  ml_comparison: MLComparisonItem[];
}

export async function fetchFeedbackSummary(
  days?: number
): Promise<FeedbackSummaryResponse> {
  const query = days ? `?days=${days}` : "";
  return request<FeedbackSummaryResponse>(`/dashboard/feedback${query}`);
}

export { ApiError };
