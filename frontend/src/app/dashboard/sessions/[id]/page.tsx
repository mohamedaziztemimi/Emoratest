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

const OUTCOME_LABELS = {
  purchase: "Bought",
  abandon: "Left Without Buying",
  browse: "Browsing Only",
  unknown: "Unknown",
} as const;

const INTENT_LABELS = {
  browsing: "Just Browsing",
  comparing: "Comparing Options",
  deciding: "Ready to Decide",
  buying: "Ready to Buy",
  exiting: "About to Leave",
  returning: "Returning Visitor",
} as const;

const DEVICE_LABELS = {
  desktop: "Desktop",
  mobile: "Mobile",
  tablet: "Tablet",
} as const;

const FEATURE_LABELS: Record<string, { label: string; tip: string }> = {
  hesitation_score: { label: "Decision Hesitation", tip: "How much this visitor paused before acting" },
  price_dwell_time_s: { label: "Time Studying Price", tip: "How long they looked at pricing" },
  rage_click_score: { label: "Frustration Level", tip: "Repeated clicks suggesting confusion or frustration" },
  scroll_retreat_count: { label: "Back-and-Forth Scrolling", tip: "Scrolled down then back up, indicating uncertainty" },
  exit_intent_count: { label: "Times Almost Left", tip: "Moved cursor toward closing the page" },
  checkout_hesitation_s: { label: "Checkout Hesitation", tip: "Time spent pausing during checkout" },
  velocity_variance: { label: "Browsing Erraticness", tip: "How erratic their navigation pattern was" },
  session_duration_s: { label: "Time on Site", tip: "Total time spent shopping" },
};

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
            Visitor Session
          </h1>
          <p className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">{s.page_url}</p>
        </div>
        <Badge variant={outcomeVariant(s.outcome)}>{OUTCOME_LABELS[s.outcome as keyof typeof OUTCOME_LABELS] || s.outcome}</Badge>
      </div>

      {/* Metric boxes */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricBox label="Likelihood to Leave" value={formatRisk(s.abandonment_risk)} variant={riskVariant(s.abandonment_risk)} />
        <MetricBox label="Shopping Friction" value={formatPercent(s.friction_score)} />
        <MetricBox label="Shopping Mode" value={INTENT_LABELS[s.intent_label as keyof typeof INTENT_LABELS] || s.intent_label || "--"} />
        <MetricBox label="Device" value={DEVICE_LABELS[s.device_type as keyof typeof DEVICE_LABELS] || s.device_type || "--"} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Features */}
        <Card>
          <CardHeader>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">
              Visitor Behavior Signals
            </h2>
            <p className="mt-0.5 text-[12px] text-[hsl(var(--muted-foreground))]">
              What this visitor&apos;s actions reveal about their shopping experience
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
                <Feature label={FEATURE_LABELS.velocity_variance.label} value={f.velocity_variance?.toFixed(2) ?? "--"} tip={FEATURE_LABELS.velocity_variance.tip} />
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
                    {["Time", "Type", "Element", "Position", "Velocity"].map((h) => (
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
                      <td className="px-5 py-3"><Badge>{e.type}</Badge></td>
                      <td className="px-5 py-3 text-[hsl(var(--muted-foreground))]">{e.element_id || "--"}</td>
                      <td className="px-5 py-3 text-[hsl(var(--muted-foreground))]">
                        {e.x != null && e.y != null ? `(${e.x}, ${e.y})` : "--"}
                      </td>
                      <td className="px-5 py-3 text-[hsl(var(--muted-foreground))]">
                        {e.velocity != null ? e.velocity.toFixed(1) : "--"}
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
