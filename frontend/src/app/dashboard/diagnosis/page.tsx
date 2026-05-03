"use client";

import { useState } from "react";
import { useQuery } from "@/lib/hooks";
import { fetchPagesDiagnosis, PagesDiagnosisResponse, DiagnosisPageItem, DiagnosisIssueItem } from "@/lib/api";

// ── Severity Config ────────────────────────────────────────────
// Uses white cards with colored left-border accents and dots

const SEVERITY_CONFIG = {
  critical: {
    border: "border-l-4 border-l-red-500 border border-gray-200",
    badge: "bg-red-50 text-red-700 border border-red-200",
    icon: "🔴",
    dot: "bg-red-500",
  },
  warning: {
    border: "border-l-4 border-l-amber-500 border border-gray-200",
    badge: "bg-amber-50 text-amber-700 border border-amber-200",
    icon: "🟠",
    dot: "bg-amber-500",
  },
  info: {
    border: "border-l-4 border-l-blue-500 border border-gray-200",
    badge: "bg-blue-50 text-blue-700 border border-blue-200",
    icon: "🔵",
    dot: "bg-blue-500",
  },
};

// ── Components ─────────────────────────────────────────────────

function PageHeader({
  onDaysChange,
  days,
}: {
  onDaysChange: (v: number) => void;
  days: number;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Diagnosis</h1>
        <p className="text-sm text-gray-500 mt-1">
          Actionable insights from user behavior patterns
        </p>
      </div>
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {[
          { key: 1, label: "24h" },
          { key: 7, label: "7 days" },
          { key: 14, label: "14 days" },
          { key: 30, label: "30 days" },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onDaysChange(key)}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
              days === key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}

function SummaryStats({
  critical,
  warning,
  info,
  totalPages,
}: {
  critical: number;
  warning: number;
  info: number;
  totalPages: number;
}) {
  const totalIssues = critical + warning + info;

  if (totalIssues === 0) {
    return (
      <section className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 p-6 text-center">
        <span className="text-4xl mb-3 block">✅</span>
        <h2 className="text-lg font-semibold text-gray-900 mb-1">No issues detected</h2>
        <p className="text-sm text-gray-600">
          Your users are having a smooth experience across all pages.
        </p>
      </section>
    );
  }

  return (
    <section className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Total Issues</p>
        <p className="text-2xl font-bold text-gray-900">{totalIssues}</p>
        <p className="text-xs text-gray-500 mt-1">across {totalPages} page{totalPages !== 1 ? "s" : ""}</p>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Critical</p>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          <p className="text-2xl font-bold text-red-600">{critical}</p>
        </div>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Warnings</p>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <p className="text-2xl font-bold text-amber-600">{warning}</p>
        </div>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Info</p>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          <p className="text-2xl font-bold text-blue-600">{info}</p>
        </div>
      </div>
    </section>
  );
}

function IssueBadge({ severity }: { severity: "critical" | "warning" | "info" }) {
  const config = SEVERITY_CONFIG[severity];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ${config.badge}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function IssueCard({ issue }: { issue: DiagnosisIssueItem }) {
  const config = SEVERITY_CONFIG[issue.severity];

  return (
    <div className={`rounded-r-lg ${config.border} bg-white p-4`}>
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-shrink-0 mt-0.5">
          <span className={`w-2 h-2 rounded-full ${config.dot} inline-block`} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h4 className="font-semibold text-gray-900">{issue.title}</h4>
            <IssueBadge severity={issue.severity} />
          </div>
          <p className="text-sm text-gray-600">{issue.description}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-3 text-sm pl-5">
        <div>
          <span className="text-gray-500">Affected sessions: </span>
          <span className="font-medium text-gray-900">{issue.affected_sessions}</span>
        </div>
        <div>
          <span className="text-gray-500">Impact: </span>
          <span className="font-medium text-gray-900">{issue.affected_percentage}%</span>
        </div>
      </div>

      <div className="bg-gray-50 rounded-md p-3 ml-5">
        <p className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">Recommendation</p>
        <p className="text-sm text-gray-800">{issue.recommendation}</p>
      </div>
    </div>
  );
}

function PageCard({ page }: { page: DiagnosisPageItem }) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Sort issues by severity
  const sortedIssues = [...page.issues].sort((a, b) => {
    const severityOrder = { critical: 0, warning: 1, info: 2 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });

  return (
    <section className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 sm:p-5 hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="flex-shrink-0">
            {page.critical_count > 0 && (
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-red-100 text-red-700 text-xs font-bold">
                {page.critical_count}
              </span>
            )}
            {page.critical_count === 0 && page.warning_count > 0 && (
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-amber-100 text-amber-700 text-xs font-bold">
                {page.warning_count}
              </span>
            )}
            {page.critical_count === 0 && page.warning_count === 0 && (
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
                {page.issue_count}
              </span>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-gray-900 truncate">{page.page_name}</h3>
              <span className={`text-xs px-2 py-0.5 rounded-full border ${
                page.critical_count > 0
                  ? "border-red-200 text-red-700 bg-red-50"
                  : page.warning_count > 0
                  ? "border-amber-200 text-amber-700 bg-amber-50"
                  : "border-blue-200 text-blue-700 bg-blue-50"
              }`}>
                {page.issue_count} issue{page.issue_count !== 1 ? "s" : ""}
              </span>
            </div>
            <p className="text-sm text-gray-500 truncate">{page.page_url}</p>
          </div>

          <div className="flex-shrink-0 text-right mr-2">
            <p className="text-xs text-gray-500">{page.total_sessions} sessions</p>
          </div>

          <svg
            className={`w-5 h-5 text-gray-400 transition-transform flex-shrink-0 ${
              isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-gray-100 p-4 sm:p-5 space-y-3">
          {sortedIssues.map((issue, idx) => (
            <IssueCard key={`${issue.type}-${idx}`} issue={issue} />
          ))}
        </div>
      )}
    </section>
  );
}

// ── NO DATA STATE ─────────────────────────────────────────────

function NoDataState() {
  return (
    <section className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-8 text-center">
      <span className="text-4xl mb-4 block">📊</span>
      <h2 className="text-lg font-semibold text-gray-900 mb-2">
        Not enough data yet
      </h2>
      <p className="text-gray-600 max-w-md mx-auto">
        Diagnosis requires at least 5 sessions per page to detect patterns.
        Sessions will appear once users visit your site with the EmoraTest SDK installed.
      </p>
    </section>
  );
}

// ── LOADING STATE ─────────────────────────────────────────────

function DiagnosisSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-100 rounded-lg h-20 animate-pulse" />
        ))}
      </div>
      <div className="bg-gray-100 rounded-xl h-32 animate-pulse" />
      <div className="bg-gray-100 rounded-xl h-32 animate-pulse" />
    </div>
  );
}

// ── MAIN PAGE ─────────────────────────────────────────────────

export default function DiagnosisPage() {
  const [days, setDays] = useState(7);

  const { data: diagnosis, loading, error } = useQuery(
    () => fetchPagesDiagnosis(days, 50),
    [days],
    `diagnosis-${days}`
  );

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <PageHeader onDaysChange={setDays} days={days} />
        <DiagnosisSkeleton />
      </div>
    );
  }

  if (error || !diagnosis) {
    return (
      <div className="max-w-4xl mx-auto">
        <PageHeader onDaysChange={setDays} days={days} />
        <NoDataState />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto pb-24">
      <PageHeader onDaysChange={setDays} days={days} />

      <SummaryStats
        critical={diagnosis.critical_issues}
        warning={diagnosis.warning_issues}
        info={diagnosis.info_issues}
        totalPages={diagnosis.total_pages}
      />

      {diagnosis.pages.length === 0 ? (
        <NoDataState />
      ) : (
        <div className="space-y-4">
          {diagnosis.pages.map((page) => (
            <PageCard key={page.page_url} page={page} />
          ))}
        </div>
      )}
    </div>
  );
}
