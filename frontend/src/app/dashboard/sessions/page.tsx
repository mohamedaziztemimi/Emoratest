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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PAGE_SIZE = 20;

// ── Helper Functions (Prompt 20) ─────────────────────────────────────────────

// Country names mapping
const COUNTRY_NAMES: Record<string, string> = {
  DE: "Germany", US: "United States", GB: "United Kingdom", FR: "France",
  ES: "Spain", IT: "Italy", NL: "Netherlands", BE: "Belgium", AT: "Austria",
  CH: "Switzerland", SE: "Sweden", NO: "Norway", DK: "Denmark", FI: "Finland",
  PL: "Poland", CZ: "Czech Republic", PT: "Portugal", IE: "Ireland",
  CA: "Canada", AU: "Australia", JP: "Japan", KR: "South Korea",
  CN: "China", IN: "India", BR: "Brazil", MX: "Mexico", RU: "Russia",
  TR: "Turkey", SA: "Saudi Arabia", AE: "UAE", SG: "Singapore",
  NZ: "New Zealand", ZA: "South Africa", AR: "Argentina", CL: "Chile",
  CO: "Colombia", PE: "Peru", VE: "Venezuela", MY: "Malaysia", TH: "Thailand",
  VN: "Vietnam", ID: "Indonesia", PH: "Philippines", HK: "Hong Kong", TW: "Taiwan",
  IL: "Israel", EG: "Egypt", NG: "Nigeria", KE: "Kenya", MA: "Morocco",
  UA: "Ukraine", GR: "Greece", RO: "Romania", BG: "Bulgaria", HU: "Hungary",
  RS: "Serbia", HR: "Croatia", SI: "Slovenia", SK: "Slovakia", BA: "Bosnia",
  MK: "North Macedonia", AL: "Albania", LT: "Lithuania", LV: "Latvia", EE: "Estonia",
  IS: "Iceland", LU: "Luxembourg", MT: "Malta", CY: "Cyprus",
};

// Convert country code to flag emoji
function countryCodeToFlag(countryCode: string | null | undefined): string {
  if (!countryCode) return "";
  const code = countryCode.toUpperCase();
  const base = 127397; // Regional Indicator Symbol Letter A base
  return [...code].map(char => String.fromCodePoint(base + char.charCodeAt(0))).join("");
}

// Get country name from code
function getCountryName(countryCode: string | null | undefined): string {
  if (!countryCode) return "";
  return COUNTRY_NAMES[countryCode.toUpperCase()] || countryCode.toUpperCase();
}

// Format IP address - shorten IPv6, keep IPv4 as is
function formatIpAddress(ip: string | null | undefined): string {
  if (!ip) return "Unknown";
  // IPv6 addresses are long and contain colons
  if (ip.includes(":") && ip.length > 25) {
    // Show first 4 groups + "..."
    const parts = ip.split(":");
    return parts.slice(0, 4).join(":") + "...";
  }
  return ip;
}

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
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);
  const fetcher = useCallback(() => fetchSessions(filters), [filtersKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const { data, error, loading, refetch } = useQuery(fetcher, [filtersKey], `sessions-${filtersKey}`);

  const setFilter = useCallback(<K extends keyof SessionFilters>(key: K, value: SessionFilters[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }, []);

  // Delete functions
  const deleteSession = useCallback(async (sessionId: string) => {
    setDeleting(true);
    setDeleteError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/dashboard/sessions/${sessionId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) {
        throw new Error("Failed to delete session");
      }
      setSelectedSessions((prev) => {
        const next = new Set(prev);
        next.delete(sessionId);
        return next;
      });
      refetch();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete");
    } finally {
      setDeleting(false);
    }
  }, [refetch]);

  const bulkDeleteSessions = useCallback(async () => {
    if (selectedSessions.size === 0) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/dashboard/sessions/bulk-delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ session_ids: Array.from(selectedSessions) }),
      });
      if (!res.ok) {
        throw new Error("Failed to delete sessions");
      }
      setSelectedSessions(new Set());
      refetch();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete");
    } finally {
      setDeleting(false);
    }
  }, [selectedSessions, refetch]);

  const toggleSessionSelection = useCallback((sessionId: string) => {
    setSelectedSessions((prev) => {
      const next = new Set(prev);
      if (next.has(sessionId)) {
        next.delete(sessionId);
      } else {
        next.add(sessionId);
      }
      return next;
    });
  }, []);

  const toggleAllSessions = useCallback(() => {
    if (!data) return;
    if (selectedSessions.size === data.sessions.length) {
      setSelectedSessions(new Set());
    } else {
      setSelectedSessions(new Set(data.sessions.map((s) => s.id)));
    }
  }, [data, selectedSessions.size]);

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
          {/* Bulk Actions Bar */}
          {selectedSessions.size > 0 && (
            <div className="flex items-center justify-between px-4 py-3 bg-[hsl(var(--accent))] border-b border-[hsl(var(--border))]">
              <span className="text-sm text-[hsl(var(--foreground))]">
                {selectedSessions.size} session{selectedSessions.size !== 1 ? "s" : ""} selected
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedSessions(new Set())}
                  className="px-3 py-1.5 text-sm font-medium text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))] rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={bulkDeleteSessions}
                  disabled={deleting}
                  className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleting ? "Deleting..." : "Delete Selected"}
                </button>
              </div>
            </div>
          )}

          {deleteError && (
            <div className="px-4 py-3 bg-red-50 border-b border-red-200">
              <p className="text-sm text-red-600">{deleteError}</p>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead className="border-b border-[hsl(var(--border))] bg-[hsl(var(--secondary)/0.5)]">
                <tr>
                  <th className="px-3 py-3.5 w-10">
                    <input
                      type="checkbox"
                      checked={selectedSessions.size === data.sessions.length}
                      onChange={toggleAllSessions}
                      className="rounded border-[hsl(var(--border))]"
                    />
                  </th>
                  {["Visitor", "Page", "Emotion", "Confidence", "Duration", "Outcome", "Time", ""].map((h) => (
                    <th
                      key={h}
                      className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]"
                    >
                      {h || " "}
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
                    <td className="px-3 py-3.5">
                      <input
                        type="checkbox"
                        checked={selectedSessions.has(s.id)}
                        onChange={() => toggleSessionSelection(s.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-[hsl(var(--border))]"
                      />
                    </td>
                    <td
                      className="px-5 py-3.5 cursor-pointer"
                      onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                    >
                      <div className="space-y-0.5">
                        {/* IP address - primary identifier */}
                        <span className="font-mono text-[13px] text-[hsl(var(--foreground))] block">
                          {formatIpAddress(s.ip_address)}
                        </span>
                        {/* Country flag + name */}
                        {s.country_code && (
                          <div className="flex items-center gap-1">
                            <span className="text-sm">{countryCodeToFlag(s.country_code)}</span>
                            <span className="text-[12px] text-[hsl(var(--muted-foreground))]">
                              {getCountryName(s.country_code)}
                            </span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td
                      className="max-w-[200px] truncate px-5 py-3.5 text-[hsl(var(--foreground))] cursor-pointer"
                      onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                    >
                      {formatPageUrl(s.page_url)}
                    </td>
                    <td
                      className="px-5 py-3.5 cursor-pointer"
                      onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                    >
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
                    <td
                      className="px-5 py-3.5 cursor-pointer"
                      onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                    >
                      {s.emotion_confidence !== null ? (
                        <span className="text-[13px] text-[hsl(var(--muted-foreground))]">
                          {s.emotion_confidence}%
                        </span>
                      ) : (
                        <span className="text-[12px] text-[hsl(var(--muted-foreground))]">--</span>
                      )}
                    </td>
                    <td
                      className="px-5 py-3.5 text-[hsl(var(--muted-foreground))] cursor-pointer"
                      onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                    >
                      {formatDuration(
                        // Calculate duration from started_at to ended_at, or use a reasonable default
                        s.ended_at
                          ? (new Date(s.ended_at).getTime() - new Date(s.started_at).getTime()) / 1000
                          : null
                      )}
                    </td>
                    <td
                      className="px-5 py-3.5 cursor-pointer"
                      onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                    >
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
                    <td
                      className="px-5 py-3.5 text-[hsl(var(--muted-foreground))] cursor-pointer"
                      onClick={() => (window.location.href = `/dashboard/sessions/${s.id}`)}
                    >
                      {formatTimeAgo(s.started_at)}
                    </td>
                    <td className="px-5 py-3.5">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(`Delete session ${s.id.slice(0, 8)}...?`)) {
                            deleteSession(s.id);
                          }
                        }}
                        disabled={deleting}
                        className="p-1.5 text-[hsl(var(--muted-foreground))] hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete session"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                      </button>
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
