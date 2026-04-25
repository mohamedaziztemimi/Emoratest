"use client";

import { memo, useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@/lib/hooks";
import { fetchSessions, type SessionFilters } from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";

const PAGE_SIZE = 20;

// ── Helper Functions (Prompt 20) ─────────────────────────────────────────────

function formatPageUrl(url: string): string {
  // Strip http://localhost:8000 or other domains, show only path
  try {
    const parsed = new URL(url);
    return parsed.pathname || url;
  } catch {
    return url;
  }
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "--";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

function outcomeVariant(outcome: string): "default" | "success" | "warning" | "destructive" | "outline" {
  return OUTCOME_VARIANT[outcome] || "outline";
}

const OUTCOME_DISPLAY: Record<string, string> = {
  purchase: "Converted",
  abandon: "Abandoned",
  unknown: "Bounced",
  browse: "Left",
  signup: "Signed Up",
  trial_started: "Trial Started",
  lead_generated: "Lead",
  demo_booked: "Demo Booked",
  checkout_completed: "Checkout Done",
};

const OUTCOME_VARIANT: Record<string, "default" | "success" | "warning" | "destructive" | "outline"> = {
  purchase: "success",
  abandon: "destructive",
  unknown: "outline",
  browse: "outline",
  signup: "success",
  trial_started: "success",
  lead_generated: "success",
  demo_booked: "success",
  checkout_completed: "success",
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
  confusion: "Confused",
  frustration: "Frustrated",
  delight: "Delighted",
  anxiety: "Anxious",
  hesitation: "Hesitating",
  focus: "Focused",
  boredom: "Bored",
  satisfaction: "Satisfied",
};

// Prompt 19: Emotion filter options
const EMOTION_FILTERS = [
  { value: null, label: "All", color: "#6B7280" },
  { value: "frustration", label: "Frustrated", color: "#EF4444" },
  { value: "confusion", label: "Confused", color: "#F59E0B" },
  { value: "anxiety", label: "Anxious", color: "#F97316" },
  { value: "hesitation", label: "Hesitating", color: "#8B5CF6" },
  { value: "satisfaction", label: "Satisfied", color: "#059669" },
  { value: "delight", label: "Delighted", color: "#10B981" },
  { value: "boredom", label: "Bored", color: "#6B7280" },
  { value: "focus", label: "Focused", color: "#3B82F6" },
];

export default function SessionsPage() {
  const [filters, setFilters] = useState<SessionFilters>({
    page: 1,
    page_size: PAGE_SIZE,
  });
  const [selectedEmotion, setSelectedEmotion] = useState<string | null>(null);

  const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);
  const fetcher = useCallback(() => fetchSessions(filters), [filtersKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const { data, error, loading, refetch } = useQuery(fetcher, [filtersKey], `sessions-${filtersKey}`);

  const setFilter = useCallback(<K extends keyof SessionFilters>(key: K, value: SessionFilters[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }, []);

  // Prompt 19: Handle emotion filter selection
  const handleEmotionSelect = useCallback((emotion: string | null) => {
    setSelectedEmotion(emotion);
    setFilter("emotion", emotion || undefined);
  }, [setFilter]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="type-page-title">Sessions</h1>
        <p className="text-sm text-secondary">Every visit to your site, and what happened</p>
      </div>

      {/* Prompt 19: Emotion Filter Pills */}
      <div className="flex flex-wrap items-center gap-2">
        {EMOTION_FILTERS.map((filter) => (
          <button
            key={filter.value ?? "all"}
            onClick={() => handleEmotionSelect(filter.value)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              selectedEmotion === filter.value
                ? "text-white shadow-md"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
            }`}
            style={{
              ...(selectedEmotion === filter.value && {
                background: filter.color,
                borderColor: filter.color,
              }),
            }}
          >
            {filter.label}
          </button>
        ))}
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
                  {["Visitor", "Page", "Emotion", "Confidence", "Duration", "Outcome", "Time"].map((h) => (
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
                    className="transition-colors hover:bg-[hsl(var(--accent)/0.5)] cursor-pointer"
                    onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                  >
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-[13px] text-[hsl(var(--primary))]">
                        {s.id.slice(0, 8)}...
                      </span>
                    </td>
                    <td className="max-w-[200px] truncate px-5 py-3.5 text-[hsl(var(--foreground))]">
                      {formatPageUrl(s.page_url)}
                    </td>
                    <td className="px-5 py-3.5">
                      {s.primary_emotion ? (
                        <div className="flex items-center gap-2">
                          <span
                            className="h-2 w-2 rounded-full"
                            style={{ backgroundColor: EMOTION_COLORS[s.primary_emotion] || "#9CA3AF" }}
                          />
                          <span className="text-[13px] font-medium text-[hsl(var(--foreground))]">
                            {EMOTION_DISPLAY[s.primary_emotion] || s.primary_emotion}
                          </span>
                        </div>
                      ) : (
                        <span className="text-[12px] text-[hsl(var(--muted-foreground))]">--</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      {s.emotion_confidence !== null ? (
                        <span className="text-[13px] text-[hsl(var(--muted-foreground))]">
                          {s.emotion_confidence}%
                        </span>
                      ) : (
                        <span className="text-[12px] text-[hsl(var(--muted-foreground))]">--</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-[hsl(var(--muted-foreground))]">
                      {formatDuration(
                        // Calculate duration from started_at to ended_at, or use a reasonable default
                        s.ended_at
                          ? (new Date(s.ended_at).getTime() - new Date(s.started_at).getTime()) / 1000
                          : null
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge variant={outcomeVariant(s.outcome)}>
                        {(() => {
                          // If session ended but outcome is still unknown, show "Left"
                          if (s.outcome === "unknown" && s.ended_at) {
                            return "Left";
                          }
                          return OUTCOME_DISPLAY[s.outcome] || s.outcome;
                        })()}
                      </Badge>
                    </td>
                    <td className="px-5 py-3.5 text-[hsl(var(--muted-foreground))]">
                      {formatTimeAgo(s.started_at)}
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
