"use client";

import { useCallback, memo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@/lib/hooks";
import { fetchSessionDetail, fetchInterventionRecs } from "@/lib/api";
import {
  formatDate, formatRisk, formatDuration, formatPercent,
  riskVariant, outcomeVariant,
} from "@/lib/format";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";

const EMOTION_COLORS: Record<string, string> = {
  confusion: "#F59E0B",
  frustration: "#EF4444",
  delight: "#10B981",
  focus: "#3B82F6",
  anxiety: "#F97316",
  boredom: "#6B7280",
  hesitation: "#8B5CF6",
  satisfaction: "#059669",
};

const OUTCOME_LABELS = {
  purchase: "Converted",
  abandon: "Abandoned",
  browse: "Active",
  unknown: "Unknown",
} as const;

const INTENT_LABELS = {
  browsing: "Low Intent",
  comparing: "Comparing",
  deciding: "Medium Intent",
  buying: "High Intent",
  exiting: "Leaving",
  returning: "Returning",
} as const;

const DEVICE_LABELS = {
  desktop: "Desktop",
  mobile: "Mobile",
  tablet: "Tablet",
} as const;

const FEATURE_LABELS: Record<string, { label: string; tip: string }> = {
  hesitation_score: { label: "Hesitation Score", tip: "How much this visitor paused before acting" },
  price_dwell_time_s: { label: "Dwell Time", tip: "How long they looked at pricing information" },
  rage_click_score: { label: "Friction Level", tip: "Repeated clicks suggesting confusion or frustration" },
  scroll_retreat_count: { label: "Scroll Retreats", tip: "Scrolled down then back up, indicating uncertainty" },
  exit_intent_count: { label: "Exit Intents", tip: "Moved cursor toward closing the page" },
  checkout_hesitation_s: { label: "Hesitation Score", tip: "Time spent pausing during checkout" },
  velocity_variance: { label: "Velocity Variance", tip: "How erratic their navigation pattern was" },
  session_duration_s: { label: "Session Duration", tip: "Total time spent on site" },
};

function formatVelocityVariance(value: number | null | undefined): string {
  if (value == null) return "--";
  if (value < 500000) return "Low";
  if (value <= 2000000) return "Medium";
  return "High";
}

// Format event description based on type and metadata
function formatEventDescription(e: { type: string; label: string | null; element_type: string | null; section: string | null; metadata: Record<string, unknown> | null }): string {
  const metadata = e.metadata as Record<string, unknown> | null;

  switch (e.type) {
    case "click":
      if (metadata?.rage_click) return `Rage click: ${metadata.click_count || 3}+ rapid clicks`;
      if (e.label) return `Clicked: "${e.label}"`;
      if (e.element_type) return `Clicked ${e.element_type}`;
      return "Click detected";

    case "scroll":
      if (metadata?.is_retreat) return "⚠️ Scrolled back up (retreat - indicates uncertainty)";
      if (metadata?.direction) {
        const direction = metadata.direction === "up" ? "↑ Scrolled up" : "↓ Scrolled down";
        const pct = metadata.viewport_pct ? ` to ${Math.round(Number(metadata.viewport_pct))}%` : "";
        return `${direction}${pct}`;
      }
      return "Page scroll";

    case "exit_intent":
      if (metadata?.trigger === "mouse_leave") return "Mouse left viewport (exit intent)";
      if (metadata?.trigger === "back_button") return "Browser back button pressed";
      if (metadata?.trigger === "tab_switch") return "User switched tabs";
      return "Exit intent detected";

    case "visibility":
      if (metadata?.state === "hidden") return "Tab hidden / minimized";
      if (metadata?.state === "visible") return "Tab visible / focused";
      return "Visibility changed";

    case "mouse_move":
      if (e.section && e.label) return `Moved over "${e.label}" in ${e.section}`;
      if (e.label) return `Moved over "${e.label}"`;
      return "Mouse movement";

    case "mouse_summary":
      if (metadata?.movement_pattern) {
        const pattern = metadata.movement_pattern as string;
        const avgVel = metadata.avg_velocity ? ` (${Math.round(Number(metadata.avg_velocity))}px/s avg)` : "";
        return `Mouse pattern: ${pattern}${avgVel}`;
      }
      return "Mouse activity summary";

    default:
      if (e.label) return e.label;
      return `${e.type} event`;
  }
}

// Format additional event details
function formatEventDetails(e: { type: string; x: number | null; y: number | null; velocity: number | null; metadata: Record<string, unknown> | null; section: string | null }): string {
  const parts: string[] = [];

  // Position for click events
  if (e.type === "click" && e.x != null && e.y != null) {
    parts.push(`Position: (${e.x}, ${e.y})`);
  }

  // Velocity for mouse events
  if (e.velocity != null && e.velocity > 0) {
    parts.push(`Velocity: ${Math.round(e.velocity)}px/s`);
  }

  // Section info
  if (e.section) {
    parts.push(`Section: ${e.section}`);
  }

  // Scroll-specific details
  if (e.type === "scroll" && e.metadata) {
    const metadata = e.metadata as Record<string, unknown>;
    if (metadata.delta) {
      parts.push(`Distance: ${Math.round(Number(metadata.delta))}px`);
    }
    if (metadata.is_retreat) {
      parts.push("⚠️ Retreat detected");
    }
  }

  // Rage click details
  if (e.metadata?.rage_click) {
    parts.push("🔥 Rage pattern");
  }

  return parts.length > 0 ? parts.join(" • ") : "--";
}

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const sessionFetcher = useCallback(() => fetchSessionDetail(id), [id]);
  const interventionFetcher = useCallback(() => fetchInterventionRecs(id), [id]);
  const session = useQuery(sessionFetcher, [id], `session-${id}`);
  const interventions = useQuery(interventionFetcher, [id], `interventions-${id}`);

  if (session.loading) return <Spinner />;
  if (session.error) return <ErrorBox message={session.error} onRetry={session.refetch} />;
  if (!session.data) return <EmptyState title="Session not found" />;

  const s = session.data;
  const f = s.features;

  return (
    <div className="space-y-6 animate-slide-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-[13px] text-[hsl(var(--muted-foreground))]">
        <Link href="/dashboard/sessions" className="transition-colors hover:text-[hsl(var(--primary))]">
          Sessions
        </Link>
        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
        <span className="font-medium text-[hsl(var(--foreground))]">{s.id.slice(0, 12)}...</span>
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">
            Session
          </h1>
          <p className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">{s.page_url}</p>
        </div>
        <Badge variant={outcomeVariant(s.outcome)}>{OUTCOME_LABELS[s.outcome as keyof typeof OUTCOME_LABELS] || s.outcome}</Badge>
      </div>

      {/* Metric boxes */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricBox label="Abandonment Risk" value={formatRisk(s.abandonment_risk)} variant={riskVariant(s.abandonment_risk)} />
        <MetricBox label="Friction Score" value={formatPercent(s.friction_score)} />
        <MetricBox label="User Intent" value={INTENT_LABELS[s.intent_label as keyof typeof INTENT_LABELS] || s.intent_label || "--"} />
        <MetricBox label="Device" value={DEVICE_LABELS[s.device_type as keyof typeof DEVICE_LABELS] || s.device_type || "--"} />
      </div>

      {s.primary_emotion && (
        <Card>
          <CardHeader>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">
              Emotion Analysis
            </h2>
            <p className="mt-0.5 text-[12px] text-[hsl(var(--muted-foreground))]">
              Emotional state detected from behavior patterns
            </p>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* Primary emotion */}
              <div className="flex flex-col items-center justify-center rounded-xl border border-[hsl(var(--border))] p-5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Primary Emotion</span>
                <span
                  className="mt-2 text-[28px] font-bold capitalize"
                  style={{ color: EMOTION_COLORS[s.primary_emotion] || 'hsl(var(--foreground))' }}
                >
                  {s.primary_emotion}
                </span>
                <span className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">
                  {((s.emotion_confidence ?? 0) * 100).toFixed(1)}% confidence
                </span>
                <div className="mt-4 flex gap-6">
                  <div className="text-center">
                    <span className="block text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Valence</span>
                    <span className="text-[15px] font-bold text-[hsl(var(--foreground))]">{s.valence?.toFixed(1) ?? "--"}</span>
                  </div>
                  <div className="text-center">
                    <span className="block text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Arousal</span>
                    <span className="text-[15px] font-bold text-[hsl(var(--foreground))]">{s.arousal?.toFixed(1) ?? "--"}</span>
                  </div>
                </div>
              </div>

              {/* Emotion scores bar chart */}
              <div className="lg:col-span-2">
                <div className="space-y-3">
                  {s.emotion_scores && Object.entries(s.emotion_scores)
                    .sort(([,a], [,b]) => (b as number) - (a as number))
                    .map(([emotion, score]) => (
                      <div key={emotion} className="flex items-center gap-3">
                        <span className="w-24 text-[12px] font-medium capitalize text-[hsl(var(--foreground))]">{emotion}</span>
                        <div className="flex-1 h-6 rounded-full bg-[hsl(var(--secondary))] overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${((score as number) * 100).toFixed(1)}%`,
                              backgroundColor: EMOTION_COLORS[emotion] || '#6B7280',
                            }}
                          />
                        </div>
                        <span className="w-14 text-right text-[12px] font-semibold text-[hsl(var(--muted-foreground))]">
                          {((score as number) * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Features */}
        <Card>
          <CardHeader>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">
              Behavior Signals
            </h2>
            <p className="mt-0.5 text-[12px] text-[hsl(var(--muted-foreground))]">
              Behavioral signals detected during this session
            </p>
          </CardHeader>
          <CardBody>
            {f ? (
              <dl className="grid grid-cols-2 gap-x-6 gap-y-4 text-[13px]">
                <Feature label={FEATURE_LABELS.hesitation_score.label} value={formatPercent(f.hesitation_score)} tip={FEATURE_LABELS.hesitation_score.tip} />
                <Feature label={FEATURE_LABELS.price_dwell_time_s.label} value={formatDuration(f.price_dwell_time_s)} tip={FEATURE_LABELS.price_dwell_time_s.tip} />
                <Feature label={FEATURE_LABELS.rage_click_score.label} value={formatPercent(f.rage_click_score)} tip={FEATURE_LABELS.rage_click_score.tip} />
                <Feature label={FEATURE_LABELS.scroll_retreat_count.label} value={String(f.scroll_retreat_count ?? "--")} tip={FEATURE_LABELS.scroll_retreat_count.tip} />
                <Feature label={FEATURE_LABELS.exit_intent_count.label} value={String(f.exit_intent_count ?? "--")} tip={FEATURE_LABELS.exit_intent_count.tip} />
                <Feature label={FEATURE_LABELS.checkout_hesitation_s.label} value={formatDuration(f.checkout_hesitation_s)} tip={FEATURE_LABELS.checkout_hesitation_s.tip} />
                <Feature label={FEATURE_LABELS.velocity_variance.label} value={formatVelocityVariance(f.velocity_variance)} tip={FEATURE_LABELS.velocity_variance.tip} />
                <Feature label={FEATURE_LABELS.session_duration_s.label} value={formatDuration(f.session_duration_s)} tip={FEATURE_LABELS.session_duration_s.tip} />
              </dl>
            ) : (
              <p className="text-[13px] text-[hsl(var(--muted-foreground))]">Behavior signals not yet computed for this session.</p>
            )}
          </CardBody>
        </Card>

        {/* Interventions */}
        <Card>
          <CardHeader>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">
              Intervention Recommendations
            </h2>
          </CardHeader>
          <CardBody>
            {interventions.loading ? (
              <Spinner />
            ) : interventions.error ? (
              <ErrorBox message={interventions.error} onRetry={interventions.refetch} />
            ) : interventions.data && interventions.data.recommendations.length > 0 ? (
              <ul className="space-y-3">
                {interventions.data.recommendations.map((rec) => (
                  <li
                    key={rec.intervention_id}
                    className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--secondary)/0.4)] p-4 transition-colors hover:bg-[hsl(var(--secondary)/0.7)]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] font-semibold text-[hsl(var(--foreground))]">{rec.name}</span>
                      <Badge variant="outline">Priority {rec.priority}</Badge>
                    </div>
                    <p className="mt-1.5 text-[12px] text-[hsl(var(--muted-foreground))]">{rec.description}</p>
                    <p className="mt-1.5 text-[11px] font-medium text-[hsl(var(--primary))]">
                      {rec.psychological_basis}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[13px] text-[hsl(var(--muted-foreground))]">No recommendations available.</p>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Event timeline */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Event Timeline</h2>
            <Badge variant="outline">{s.events.length} events</Badge>
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {s.events.length === 0 ? (
            <div className="p-6">
              <EmptyState title="No events recorded" />
            </div>
          ) : (
            <div className="max-h-[500px] overflow-y-auto">
              <table className="w-full text-left text-[13px]">
                <thead className="sticky top-0 z-10 border-b border-[hsl(var(--border))] bg-[hsl(var(--card))]">
                  <tr>
                    {["Time", "Type", "Description", "Details"].map((h) => (
                      <th key={h} className="px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--border)/0.5)]">
                  {s.events.map((e) => (
                    <tr key={e.id} className="transition-colors hover:bg-[hsl(var(--accent)/0.5)]">
                      <td className="whitespace-nowrap px-5 py-3 text-[hsl(var(--muted-foreground))]">
                        {formatDate(e.ts)}
                      </td>
                      <td className="px-5 py-3">
                        <Badge
                          variant={
                            e.type === "click" ? "default" :
                            e.type === "exit_intent" ? "destructive" :
                            e.type === "visibility" ? "outline" :
                            "secondary"
                          }
                        >
                          {e.type.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="px-5 py-3 text-[hsl(var(--foreground))]">
                        {formatEventDescription(e)}
                      </td>
                      <td className="px-5 py-3 text-[hsl(var(--muted-foreground))] text-[12px]">
                        {formatEventDetails(e)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

const MetricBox = memo(function MetricBox({ label, value, variant }: { label: string; value: string; variant?: string }) {
  return (
    <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 transition-shadow hover:shadow-sm">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">{label}</p>
      <p className={`mt-2 text-[18px] font-bold ${
        variant === "destructive" ? "text-[hsl(var(--destructive))]" :
        variant === "warning" ? "text-[hsl(var(--warning))]" :
        variant === "success" ? "text-[hsl(var(--success))]" :
        "text-[hsl(var(--foreground))]"
      }`}>
        {value}
      </p>
    </div>
  );
});

const Feature = memo(function Feature({ label, value, tip }: { label: string; value: string; tip?: string }) {
  return (
    <div>
      <dt className="text-[hsl(var(--muted-foreground))]" title={tip}>{label}</dt>
      <dd className="mt-0.5 font-semibold text-[hsl(var(--foreground))]">{value}</dd>
    </div>
  );
});
