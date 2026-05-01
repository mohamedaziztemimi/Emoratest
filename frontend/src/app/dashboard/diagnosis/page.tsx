"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@/lib/hooks";
import {
  fetchPrimaryDiagnosis,
  fetchIssuesList,
  DiagnosisResponse,
  IssueListItem,
  ProblemSummary,
  EvidenceItem,
  RootCause,
  ActionItem,
} from "@/lib/api";
import { useRouter } from "next/navigation";

// ── Severity Config ────────────────────────────────────────────

const SEVERITY_CONFIG = {
  high: {
    bg: "bg-red-50",
    border: "border-red-200",
    badge: "bg-red-100 text-red-700",
    icon: "🔴",
  },
  medium: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    badge: "bg-amber-100 text-amber-700",
    icon: "🟠",
  },
  low: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    badge: "bg-blue-100 text-blue-700",
    icon: "🔵",
  },
};

// ── DEMO DATA (for instant value when no real data exists) ──────

const DEMO_DIAGNOSIS: DiagnosisResponse = {
  summary: {
    title: "Demo: High frustration detected on checkout",
    page_url: "https://example.com/checkout",
    page_name: "Checkout",
    affected_users_pct: 0,
    severity: "medium",
    estimated_lost_revenue: null,
  },
  evidence: [],
  root_cause: {
    primary_cause: "This is a demo to show what diagnoses look like",
    explanation: "When you have real session data (50+ sessions), diagnoses will be based on actual user behavior patterns.",
    contributing_factors: [],
  },
  actions: [
    {
      title: "Install the SDK to start collecting data",
      description: "Add the EmoraTest tracking script to your website",
      type: "edit_element",
      link: "/dashboard/settings",
    },
  ],
  supporting_charts: {
    page_stats: {
      total_sessions: 0,
      avg_friction: 0,
      top_emotion: "none",
    },
  },
  generated_at: new Date().toISOString(),
};

// ── Components ─────────────────────────────────────────────────

function PageHeader({
  onTimeRangeChange,
  timeRange,
  showDemoToggle,
  isDemoMode,
  onToggleDemo
}: {
  onTimeRangeChange: (v: string) => void;
  timeRange: string;
  showDemoToggle?: boolean;
  isDemoMode?: boolean;
  onToggleDemo?: () => void;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Diagnosis</h1>
        <p className="text-sm text-gray-500 mt-1">
          Turn user behavior into actionable fixes .  no charts required
        </p>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {[
            { key: "24h", label: "24h", hours: 24 },
            { key: "7d", label: "7 days", hours: 168 },
            { key: "30d", label: "30 days", hours: 720 },
          ].map(({ key, label, hours }) => (
            <button
              key={key}
              onClick={() => onTimeRangeChange(String(hours))}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                timeRange === String(hours)
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {showDemoToggle && (
          <button
            onClick={onToggleDemo}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
              isDemoMode
                ? "bg-purple-100 text-purple-700"
                : "bg-gray-100 text-gray-600 hover:text-gray-900"
            }`}
          >
            {isDemoMode ? "Demo Mode" : "View Demo"}
          </button>
        )}
      </div>
    </div>
  );
}

// ── 1. PROBLEM SUMMARY SECTION ────────────────────────────────

function ProblemSummarySection({ summary, isDemo }: { summary: ProblemSummary; isDemo?: boolean }) {
  const config = SEVERITY_CONFIG[summary.severity as keyof typeof SEVERITY_CONFIG] || SEVERITY_CONFIG.low;

  return (
    <section className={`rounded-2xl border ${config.border} ${config.bg} p-6 sm:p-8`}>
      {isDemo && (
        <div className="mb-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-semibold">
          <span>🎭</span>
          <span>Demo Mode .  sample data</span>
        </div>
      )}
      <div className="flex items-start gap-4">
        <span className="text-3xl">{config.icon}</span>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">{summary.title}</h2>
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${config.badge}`}>
              {summary.severity.toUpperCase()}
            </span>
          </div>
          <p className="text-gray-600 mb-4">
            <span className="font-semibold text-gray-900">{summary.affected_users_pct}%</span> of users are
            affected on{" "}
            <span className="text-[#007BFF] font-medium">
              {summary.page_name}
            </span>
          </p>
          {summary.estimated_lost_revenue && (
            <p className="text-sm text-gray-500">
              Estimated impact: {summary.estimated_lost_revenue}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

// ── 2. EVIDENCE SECTION ────────────────────────────────────────

function EvidenceSection({ evidence, severity, isDemo }: { evidence: EvidenceItem[]; severity: string; isDemo?: boolean }) {
  if (evidence.length === 0) return null;

  const config = SEVERITY_CONFIG[severity as keyof typeof SEVERITY_CONFIG] || SEVERITY_CONFIG.low;

  const getIconForType = (type: string) => {
    switch (type) {
      case "rage_clicks": return "👆";
      case "hesitation": return "⏸️";
      case "drop_off": return "🚪";
      case "session_pattern": return "📊";
      default: return "📈";
    }
  };

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Evidence</h3>
        {isDemo && (
          <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded-full">Sample data</span>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {evidence.map((item, idx) => (
          <div
            key={idx}
            className={`rounded-lg border ${config.border} ${config.bg} p-4`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{getIconForType(item.type)}</span>
              <span className="text-xs font-medium text-gray-500 uppercase">{item.type.replace("_", " ")}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{item.value}</p>
            <p className="text-sm text-gray-600 mt-1">{item.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── 3. WHY SECTION ─────────────────────────────────────────────

function WhySection({ rootCause, isDemo }: { rootCause: RootCause; isDemo?: boolean }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Why This Happens</h3>
        {isDemo && (
          <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded-full">Sample data</span>
        )}
      </div>
      <div className="space-y-4">
        <div>
          <p className="text-lg font-semibold text-gray-900 mb-2">{rootCause.primary_cause}</p>
          <p className="text-gray-600">{rootCause.explanation}</p>
        </div>
        {rootCause.contributing_factors.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Contributing Factors
            </p>
            <ul className="space-y-2">
              {rootCause.contributing_factors.map((factor, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-[#007BFF] mt-0.5">•</span>
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}

// ── 4. RECOMMENDED ACTIONS SECTION (Prompt 28) ──────────────

function ActionsSection({ actions, isDemo }: { actions: ActionItem[]; isDemo?: boolean }) {
  const router = useRouter();

  const handleAction = (action: ActionItem) => {
    if (isDemo) return; // Don't navigate in demo mode
    if (action.link) {
      router.push(action.link);
    }
  };

  if (actions.length === 0) return null;

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Recommended Actions</h3>
        {isDemo && (
          <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded-full">Sample data</span>
        )}
      </div>
      <div className="space-y-3">
        {actions.map((action, idx) => (
          <div
            key={idx}
            className={`group flex items-start gap-4 p-4 rounded-lg border transition-all ${
              isDemo
                ? "border-gray-200 bg-gray-50 cursor-default"
                : "border-gray-200 hover:border-[#007BFF] hover:bg-blue-50/30 cursor-pointer"
            }`}
            onClick={() => handleAction(action)}
          >
            <div className="flex-1">
              <h4 className={`font-semibold transition-colors ${
                isDemo ? "text-gray-900" : "text-gray-900 group-hover:text-[#007BFF]"
              }`}>
                {action.title}
              </h4>
              <p className="text-sm text-gray-600 mt-1">{action.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-400 uppercase">{action.type}</span>
              {!isDemo && (
                <svg className="w-5 h-5 text-gray-400 group-hover:text-[#007BFF] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── 5. SUPPORTING DATA SECTION (Prompt 28) ────────────────────

function SupportingCharts({ data, isDemo }: { data: DiagnosisResponse; isDemo?: boolean }) {
  const charts = data.supporting_charts;
  if (!charts || Object.keys(charts).length === 0) return null;

  const pageStats = charts.page_stats as Record<string, unknown> | undefined;
  const totalSessions = pageStats?.total_sessions;
  const avgFriction = pageStats?.avg_friction;
  const topEmotion = pageStats?.top_emotion;

  return (
    <section className="border-t border-gray-200 pt-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          Supporting Data
        </p>
        {isDemo && (
          <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded-full">Sample data</span>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Total Sessions</p>
          <p className="text-lg font-semibold text-gray-900">
            {typeof totalSessions === "number" ? totalSessions : ". "}
          </p>
        </div>
        {typeof avgFriction === "number" && (
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Avg Friction</p>
            <p className="text-lg font-semibold text-gray-900">
              {avgFriction}%
            </p>
          </div>
        )}
        {typeof topEmotion === "string" && (
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Top Emotion</p>
            <p className="text-lg font-semibold text-gray-900 capitalize">
              {topEmotion}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

// ── 7. ISSUE LIST ─────────────────────────────────────────────

function IssuesList({ issues, isDemo }: { issues: IssueListItem[]; isDemo?: boolean }) {
  const router = useRouter();

  if (issues.length === 0) return null;

  return (
    <section className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
          Other Issues Detected
        </h3>
        {isDemo && (
          <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded-full">Sample data</span>
        )}
      </div>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {issues.map((issue, idx) => {
          const config = SEVERITY_CONFIG[issue.severity as keyof typeof SEVERITY_CONFIG] || SEVERITY_CONFIG.low;
          const pageName = issue.page_url.split("/").filter(Boolean).pop() || "Page";

          return (
            <div
              key={issue.id}
              className={`flex items-center gap-4 p-4 ${idx !== issues.length - 1 ? "border-b border-gray-100" : ""} ${
                isDemo ? "cursor-default" : "hover:bg-gray-50 transition-colors cursor-pointer"
              }`}
              onClick={() => !isDemo && router.push(`/dashboard/pages?url=${encodeURIComponent(issue.page_url)}`)}
            >
              <span className="text-lg">{config.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{issue.title}</p>
                <p className="text-sm text-gray-500 truncate">{pageName}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-900">{issue.affected_users}</p>
                <p className="text-xs text-gray-500">users</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${config.badge}`}>
                {issue.severity}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ── NO DATA STATE (graceful, not error) ───────────────────────

function NoDataState({ sessionCount, onTryDemo }: { sessionCount: number; onTryDemo: () => void }) {
  const threshold = 5;  // Lowered from 20 - show diagnosis earlier
  const remaining = threshold - sessionCount;

  return (
    <section className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-200 p-8 text-center">
      <span className="text-4xl mb-4 block">📊</span>
      <h2 className="text-xl font-bold text-gray-900 mb-2">
        {sessionCount === 0 ? "Start collecting user data" : "Collecting more data..."}
      </h2>
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        {sessionCount === 0
          ? "Add the EmoraTest tracking script to your website to start analyzing user behavior and detecting issues."
          : `Need ${remaining} more session${remaining !== 1 ? "s" : ""} for detailed diagnosis. Currently tracking: ${sessionCount} session${sessionCount !== 1 ? "s" : ""}.`}
      </p>
      <div className="flex items-center justify-center gap-3 flex-wrap">
        <a
          href="/dashboard/settings"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#007BFF] text-white rounded-lg font-semibold hover:bg-[#0056b3] transition-colors"
        >
          View Setup Guide
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </a>
        <button
          onClick={onTryDemo}
          className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg font-semibold hover:bg-purple-200 transition-colors"
        >
          <span>🎭</span>
          Try Demo Mode
        </button>
      </div>
      {sessionCount > 0 && sessionCount < threshold && (
        <div className="mt-6 max-w-sm mx-auto">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-[#007BFF] h-2 rounded-full transition-all"
              style={{ width: `${(sessionCount / threshold) * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">{sessionCount} of {threshold} sessions collected</p>
        </div>
      )}
    </section>
  );
}

// ── LOADING STATE ─────────────────────────────────────────────

function DiagnosisSkeleton() {
  return (
    <div className="space-y-6">
      <div className="bg-gray-100 rounded-2xl h-32 animate-pulse" />
      <div className="bg-gray-100 rounded-xl h-24 animate-pulse" />
      <div className="bg-gray-100 rounded-xl h-32 animate-pulse" />
      <div className="bg-gray-100 rounded-xl h-40 animate-pulse" />
    </div>
  );
}

// ── MAIN PAGE ─────────────────────────────────────────────────

export default function DiagnosisPage() {
  const [timeRange, setTimeRange] = useState("24");
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [errorState, setErrorState] = useState<string | null>(null);
  const hours = parseInt(timeRange, 10);

  // Get merchant ID from localStorage (set during login)
  const merchantId = useMemo(() => {
    if (typeof window === "undefined") return "";
    try {
      const me = localStorage.getItem("auth_me");
      if (me) {
        const data = JSON.parse(me);
        return data.id || "";
      }
    } catch { }
    return "";
  }, []);

  // Fetch real data
  const { data: diagnosis, loading, error } = useQuery(
    () => fetchPrimaryDiagnosis(merchantId, hours),
    [merchantId, hours],
    `diagnosis-${hours}`
  );

  const { data: issues } = useQuery(
    () => fetchIssuesList(merchantId, hours),
    [merchantId, hours],
    `issues-${hours}`
  );

  // Handle errors gracefully - never show raw error
  if (error && !isDemoMode) {
    // Store error but show demo mode instead
    if (!errorState) setErrorState("data-unavailable");
  }

  // Show loading state
  if (loading && !isDemoMode) return (
    <div className="max-w-5xl mx-auto">
      <PageHeader
        onTimeRangeChange={setTimeRange}
        timeRange={timeRange}
        showDemoToggle={!loading}
        isDemoMode={isDemoMode}
        onToggleDemo={() => setIsDemoMode(true)}
      />
      <DiagnosisSkeleton />
    </div>
  );

  // Determine what to show
  const showDemo = isDemoMode;
  const displayDiagnosis = showDemo ? DEMO_DIAGNOSIS : diagnosis;
  const displayIssues = showDemo ? {
    issues: [
      {
        id: "1",
        title: "Demo: Users hesitating on pricing page",
        page_url: "https://example.com/pricing",
        affected_users: 0,
        severity: "medium",
      },
    ],
    total_issues: 1,
    high_severity_count: 0,
  } : issues;

  // No real data and not in demo mode - show "collect more data" state
  if (!isDemoMode && (!diagnosis || !diagnosis.summary || diagnosis.summary.affected_users_pct === 0)) {
    const pageStats = diagnosis?.supporting_charts?.page_stats as Record<string, unknown> | undefined;
    const sessionCount = typeof pageStats?.total_sessions === "number" ? pageStats.total_sessions : 0;
    return (
      <div className="max-w-5xl mx-auto">
        <PageHeader
          onTimeRangeChange={setTimeRange}
          timeRange={timeRange}
          showDemoToggle
          isDemoMode={false}
          onToggleDemo={() => setIsDemoMode(true)}
        />
        <NoDataState sessionCount={sessionCount} onTryDemo={() => setIsDemoMode(true)} />
      </div>
    );
  }

  // At this point, displayDiagnosis is guaranteed to be non-null
  // Either we're in demo mode (using DEMO_DIAGNOSIS) or we have real diagnosis data
  if (!displayDiagnosis) {
    return null;
  }

  // Main diagnosis view (real or demo)
  return (
    <div className="max-w-5xl mx-auto pb-24">
      <PageHeader
        onTimeRangeChange={setTimeRange}
        timeRange={timeRange}
        showDemoToggle={!isDemoMode}
        isDemoMode={isDemoMode}
        onToggleDemo={() => setIsDemoMode(!isDemoMode)}
      />

      {/* 1. PROBLEM SUMMARY .  TOP PRIORITY */}
      <ProblemSummarySection summary={displayDiagnosis.summary} isDemo={isDemoMode} />

      {/* 2. EVIDENCE .  SUPPORTING DATA */}
      <EvidenceSection
        evidence={displayDiagnosis.evidence}
        severity={displayDiagnosis.summary.severity}
        isDemo={isDemoMode}
      />

      {/* 3. WHY .  ROOT CAUSE */}
      <WhySection rootCause={displayDiagnosis.root_cause} isDemo={isDemoMode} />

      {/* 4. RECOMMENDED ACTIONS .  Prompt 28 */}
      <ActionsSection actions={displayDiagnosis.actions} isDemo={isDemoMode} />

      {/* 5. SUPPORTING DATA .  Prompt 28 */}
      <SupportingCharts data={displayDiagnosis} isDemo={isDemoMode} />

      {/* 7. OTHER ISSUES LIST */}
      {displayIssues && displayIssues.issues.length > 0 && (
        <IssuesList issues={displayIssues.issues} isDemo={isDemoMode} />
      )}
    </div>
  );
}
