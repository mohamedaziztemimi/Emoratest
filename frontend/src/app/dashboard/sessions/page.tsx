"use client";

import { memo, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@/lib/hooks";
import { fetchSessions, type SessionFilters } from "@/lib/api";
import { formatDate, formatRisk, riskVariant, outcomeVariant } from "@/lib/format";
import { Card, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";

const PAGE_SIZE = 20;

const OUTCOME_DISPLAY: Record<string, string> = {
  purchase: "Converted",
  abandon: "Abandoned",
  browse: "Active",
  unknown: "Unknown",
};

const EMOTION_COLORS: Record<string, string> = {
  confusion: "#F59E0B",
  frustration: "#EF4444",
  delight: "#10B981",
  anxiety: "#F97316",
  hesitation: "#8B5CF6",
  focus: "#3B82F6",
  boredom: "#6B7280",
  satisfaction: "#059669",
};

const EMOTION_DISPLAY: Record<string, string> = {
  confusion: "Confusion",
  frustration: "Frustration",
  delight: "Delight",
  anxiety: "Anxiety",
  hesitation: "Hesitation",
  focus: "Focus",
  boredom: "Boredom",
  satisfaction: "Satisfaction",
};

export default function SessionsPage() {
  const [filters, setFilters] = useState<SessionFilters>({
    page: 1,
    page_size: PAGE_SIZE,
  });

  const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);
  const fetcher = useCallback(() => fetchSessions(filters), [filtersKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const { data, error, loading, refetch } = useQuery(fetcher, [filtersKey], `sessions-${filtersKey}`);

  const setFilter = useCallback(<K extends keyof SessionFilters>(key: K, value: SessionFilters[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }, []);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Sessions</h1>
        <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">
          Every visit to your site, and what happened
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardBody className="flex flex-wrap items-end gap-4">
          <FilterSelect
            label="Outcome"
            value={filters.outcome || ""}
            onChange={(v) => setFilter("outcome", v || undefined)}
            options={OUTCOME_OPTIONS}
          />
          <FilterSelect
            label="Device"
            value={filters.device_type || ""}
            onChange={(v) => setFilter("device_type", v || undefined)}
            options={DEVICE_OPTIONS}
          />
          <FilterInput
            label="Min leave risk"
            type="number"
            value={filters.risk_min ?? ""}
            onChange={(v) => setFilter("risk_min", v ? Number(v) : undefined)}
            className="w-24"
          />
          <FilterInput
            label="From"
            type="date"
            value={filters.date_from || ""}
            onChange={(v) => setFilter("date_from", v || undefined)}
          />
          <FilterInput
            label="To"
            type="date"
            value={filters.date_to || ""}
            onChange={(v) => setFilter("date_to", v || undefined)}
          />
        </CardBody>
      </Card>

      {/* Table */}
      {loading ? (
        <Spinner />
      ) : error ? (
        <ErrorBox message={error} onRetry={refetch} />
      ) : !data || data.sessions.length === 0 ? (
        <EmptyState title="No sessions found" description="Adjust your filters or wait for new data." />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead className="border-b border-[hsl(var(--border))] bg-[hsl(var(--secondary)/0.5)]">
                <tr>
                  {["Visitor", "Page Visited", "Started", "Result", "Leave Risk", "Emotion", "Device"].map((h) => (
                    <th
                      key={h}
                      className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--border)/0.5)]">
                {data.sessions.map((s) => (
                  <tr
                    key={s.id}
                    className="transition-colors hover:bg-[hsl(var(--accent)/0.5)]"
                  >
                    <td className="px-5 py-3.5">
                      <Link
                        href={`/dashboard/sessions/${s.id}`}
                        className="font-medium text-[hsl(var(--primary))] hover:underline"
                      >
                        {s.id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td className="max-w-[200px] truncate px-5 py-3.5 text-[hsl(var(--muted-foreground))]">
                      {s.page_url}
                    </td>
                    <td className="px-5 py-3.5 text-[hsl(var(--muted-foreground))]">
                      {formatDate(s.started_at)}
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge variant={outcomeVariant(s.outcome)}>{OUTCOME_DISPLAY[s.outcome] || s.outcome}</Badge>
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge variant={riskVariant(s.abandonment_risk)}>
                        {formatRisk(s.abandonment_risk)}
                      </Badge>
                    </td>
                    <td className="px-5 py-3.5">
                      {(() => {
                        const sessionAge = s.ended_at
                          ? (Date.now() - new Date(s.ended_at).getTime()) / 1000
                          : null;

                        if (s.primary_emotion) {
                          return (
                            <div className="flex items-center gap-2">
                              <span
                                className="h-2 w-2 rounded-full"
                                style={{ backgroundColor: EMOTION_COLORS[s.primary_emotion] || "#9CA3AF" }}
                              />
                              <span className="text-[12px] font-medium text-[hsl(var(--foreground))]">
                                {EMOTION_DISPLAY[s.primary_emotion] || s.primary_emotion}
                              </span>
                              {s.emotion_confidence && (
                                <span className="text-[10px] text-[hsl(var(--muted-foreground))]">
                                  {s.emotion_confidence}%
                                </span>
                              )}
                            </div>
                          );
                        }

                        // No emotion data yet
                        const isAnalyzing = sessionAge === null || sessionAge < 30;

                        return (
                          <div className="flex items-center gap-2">
                            {isAnalyzing && (
                              <span className="h-2 w-2 rounded-full bg-[hsl(var(--muted-foreground))] animate-pulse" />
                            )}
                            <span className="text-[11px] text-[hsl(var(--muted-foreground))]">
                              {isAnalyzing ? "Analyzing..." : "No data"}
                            </span>
                          </div>
                        );
                      })()}
                    </td>
                    <td className="px-5 py-3.5 text-[hsl(var(--muted-foreground))]">
                      {s.device_type || "--"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-[hsl(var(--border))] px-5 py-3.5">
              <p className="text-[12px] text-[hsl(var(--muted-foreground))]">
                Page {data.page} of {totalPages} &middot; {data.total} sessions
              </p>
              <div className="flex gap-2">
                <PaginationBtn
                  disabled={data.page <= 1}
                  onClick={() => setFilters((p) => ({ ...p, page: (p.page || 1) - 1 }))}
                >
                  Previous
                </PaginationBtn>
                <PaginationBtn
                  disabled={data.page >= totalPages}
                  onClick={() => setFilters((p) => ({ ...p, page: (p.page || 1) + 1 }))}
                >
                  Next
                </PaginationBtn>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

/* ── Constants (stable references) ─────────────────────── */
const OUTCOME_OPTIONS = [
  { value: "", label: "All Results" },
  { value: "purchase", label: "Converted" },
  { value: "abandon", label: "Abandoned" },
  { value: "browse", label: "Active" },
];

const DEVICE_OPTIONS = [
  { value: "", label: "All Devices" },
  { value: "desktop", label: "Desktop" },
  { value: "mobile", label: "Mobile" },
  { value: "tablet", label: "Tablet" },
];

/* ── Memoized filter controls ──────────────────────────── */
const FilterSelect = memo(function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="flex flex-col text-[12px]">
      <span className="mb-1.5 font-semibold text-[hsl(var(--muted-foreground))]">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-3 py-2 text-[13px] text-[hsl(var(--foreground))] outline-none transition-colors focus:border-[hsl(var(--ring))] focus:ring-2 focus:ring-[hsl(var(--ring)/0.2)]"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
});

const FilterInput = memo(function FilterInput({
  label,
  type,
  value,
  onChange,
  className,
}: {
  label: string;
  type: string;
  value: string | number;
  onChange: (v: string) => void;
  className?: string;
}) {
  return (
    <label className="flex flex-col text-[12px]">
      <span className="mb-1.5 font-semibold text-[hsl(var(--muted-foreground))]">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-3 py-2 text-[13px] text-[hsl(var(--foreground))] outline-none transition-colors focus:border-[hsl(var(--ring))] focus:ring-2 focus:ring-[hsl(var(--ring)/0.2)] ${className || ""}`}
      />
    </label>
  );
});

const PaginationBtn = memo(function PaginationBtn({
  children,
  disabled,
  onClick,
}: {
  children: React.ReactNode;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4 py-1.5 text-[12px] font-medium text-[hsl(var(--foreground))] transition-all hover:bg-[hsl(var(--accent))] disabled:opacity-40 disabled:cursor-not-allowed"
    >
      {children}
    </button>
  );
});
