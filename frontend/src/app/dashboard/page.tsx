"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";
import { WaitlistModal } from "@/components/WaitlistModal";

// ── Types ─────────────────────────────────────────────────────────────────────

interface EmotionPulse {
  emotion_score: number;
  emotion_trend: number;
  sessions_today: number;
  sessions_with_issues: number;
  frustration_alerts: number;
  active_experiments: number;
}

interface TopIssue {
  has_issue: boolean;
  page_url?: string;
  page_title?: string;
  issue_type?: string;
  severity?: "high" | "medium";
  affected_sessions?: number;
  frustration_pct?: number;
  time_window?: string;
}

interface PageAttention {
  page_url: string;
  dominant_emotion: string;
  emotion_pct: number;
  session_count: number;
}

interface ProblemSession {
  id: string;
  visitor_id: string;
  page_url: string;
  primary_emotion: string;
  emotion_confidence: number | null;
  created_at: string;
  duration_seconds: number | null;
}

interface UsageData {
  plan: string;
  sessions_used: number;
  sessions_limit: number | null;  // null = unlimited
  reset_date: string;
}

// ── Emotion Colors (4 behavioral states) ─────────────────────────────────────────
const EMOTION_COLORS = {
  frustrated: "#EF4444",  // red
  confused: "#F59E0B",    // amber
  engaged: "#10B981",     // green
  disengaged: "#6B7280",  // gray
} as const;

// Also support old emotion names for backward compatibility with API
const LEGACY_EMOTION_COLORS = {
  frustration: "#EF4444",
  confusion: "#F59E0B",
  delight: "#10B981",
  satisfaction: "#059669",
  focus: "#3B82F6",
  anxiety: "#F97316",
  hesitation: "#8B5CF6",
  boredom: "#6B7280",
} as const;

const getEmotionColor = (emotion: string): string => {
  const normalized = emotion.toLowerCase();
  // Check new 4 emotions first
  if (normalized in EMOTION_COLORS) {
    return EMOTION_COLORS[normalized as keyof typeof EMOTION_COLORS];
  }
  // Fall back to legacy colors
  if (normalized in LEGACY_EMOTION_COLORS) {
    return LEGACY_EMOTION_COLORS[normalized as keyof typeof LEGACY_EMOTION_COLORS];
  }
  return "#6B7280";
};

// ── Main Component ─────────────────────────────────────────────────────────────

export default function OverviewPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  // Data from new endpoints
  const [pulse, setPulse] = useState<EmotionPulse | null>(null);
  const [topIssue, setTopIssue] = useState<TopIssue | null>(null);
  const [pagesAttention, setPagesAttention] = useState<PageAttention[]>([]);
  const [problemSessions, setProblemSessions] = useState<ProblemSession[]>([]);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [showWaitlist, setShowWaitlist] = useState(false);
  const [dismissedUsageBanner, setDismissedUsageBanner] = useState(false);
  const [totalSessions, setTotalSessions] = useState(0);
  const [sdkKey, setSdkKey] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      const apiUrl = API_BASE;

      try {
        // Check if user has any sessions
        const sessionsRes = await fetch(`${apiUrl}/api/v1/dashboard/sessions?page=1&page_size=1`, {
          credentials: "include",
        });

        if (sessionsRes.status === 401) {
          router.push("/login");
          return;
        }

        if (sessionsRes.ok) {
          const sessionsData = await sessionsRes.json();
          setTotalSessions(sessionsData.total || 0);

          // Fetch SDK key for onboarding card
          try {
            const sdkRes = await fetch(`${apiUrl}/api/v1/merchant/sdk-key`, {
              credentials: "include",
            });
            if (sdkRes.ok) {
              const sdkData = await sdkRes.json();
              setSdkKey(sdkData.sdk_key || sdkData.key || null);
            }
          } catch {
            // Silent fail
          }

          // Fetch all dashboard data in parallel
          const [pulseRes, issueRes, pagesRes, sessionsListRes, usageRes] = await Promise.all([
            fetch(`${apiUrl}/api/v1/dashboard/emotion-pulse`, { credentials: "include" }),
            fetch(`${apiUrl}/api/v1/dashboard/top-issue`, { credentials: "include" }),
            fetch(`${apiUrl}/api/v1/dashboard/pages-attention?limit=3`, { credentials: "include" }),
            fetch(`${apiUrl}/api/v1/dashboard/problem-sessions?limit=5`, { credentials: "include" }),
            fetch(`${apiUrl}/api/v1/auth/usage`, { credentials: "include" }),
          ]);

          if (pulseRes.ok) {
            const pulseData = await pulseRes.json();
            setPulse(pulseData);
          }

          if (issueRes.ok) {
            const issueData = await issueRes.json();
            setTopIssue(issueData);
          }

          if (pagesRes.ok) {
            const pagesData = await pagesRes.json();
            setPagesAttention(pagesData);
          }

          if (sessionsListRes.ok) {
            const sessionsListData = await sessionsListRes.json();
            setProblemSessions(sessionsListData);
          }

          if (usageRes.ok) {
            const usageData = await usageRes.json();
            setUsage(usageData);
          }
        }
      } catch (err) {
        // Silently handle errors - show demo data
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [router]);

  // Verify installation by checking if sessions exist
  const handleVerifyInstallation = async () => {
    setVerifying(true);
    try {
      const apiUrl = API_BASE;
      const res = await fetch(`${apiUrl}/api/v1/dashboard/sessions?page=1&page_size=1`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        if (data.total > 0) {
          setVerified(true);
          // Reload data after verification
          setTimeout(() => window.location.reload(), 1000);
        }
      }
    } catch {
      // Silent fail
    } finally {
      setVerifying(false);
    }
  };

  // Format time ago
  const getTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (seconds < 60) return "Just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  // Format duration
  const formatDuration = (seconds: number | null) => {
    if (!seconds) return ".";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  };

  return (
    <div>
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="type-page-title mb-1">Overview</h1>
        <p className="text-sm text-secondary">Your behavioral intelligence command center</p>
      </div>

      {/* Loading State */}
      {loading && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SkeletonCard height="300px" />
            <SkeletonCard height="300px" />
          </div>
        </>
      )}

      {/* Empty State / Onboarding Card - Show when total sessions = 0 */}
      {!loading && totalSessions === 0 && (
        <OnboardingCard sdkKey={sdkKey} onVerify={handleVerifyInstallation} verifying={verifying} verified={verified} />
      )}

      {/* Session Limit Warning Banner - only show for limited plans */}
      {!loading && usage && !dismissedUsageBanner && totalSessions > 0 && usage.sessions_limit !== null && (
        <div
          className="mb-6 rounded-xl p-4 flex items-center justify-between"
          style={{
            background: usage.sessions_used >= usage.sessions_limit
              ? "#FEF2F2"
              : usage.sessions_used >= usage.sessions_limit * 0.8
              ? "#FFFBEB"
              : "#F0FDF4",
            border: `1px solid ${
              usage.sessions_used >= usage.sessions_limit
                ? "#FECACA"
                : usage.sessions_used >= usage.sessions_limit * 0.8
                ? "#FDE68A"
                : "#BBF7D0"
            }`,
          }}
        >
          <div className="flex items-center gap-3">
            <span style={{ fontSize: "20px" }}>
              {usage.sessions_used >= usage.sessions_limit ? "🚫" : usage.sessions_used >= usage.sessions_limit * 0.8 ? "⚠️" : "✓"}
            </span>
            <div>
              <p
                className="text-sm font-semibold"
                style={{
                  color:
                    usage.sessions_used >= usage.sessions_limit
                      ? "#DC2626"
                      : usage.sessions_used >= usage.sessions_limit * 0.8
                      ? "#D97706"
                      : "#059669",
                }}
              >
                {usage.sessions_used >= usage.sessions_limit
                  ? `You've reached your monthly session limit (${usage.sessions_limit} sessions)`
                  : `You've used ${usage.sessions_used} of ${usage.sessions_limit} sessions this month`}
              </p>
              <p className="text-xs text-[#6B7280] mt-0.5">
                {usage.sessions_used >= usage.sessions_limit
                  ? "New sessions are not being tracked."
                  : `Resets on ${new Date(usage.reset_date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowWaitlist(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white"
              style={{ background: "#007BFF" }}
            >
              {usage.sessions_used >= usage.sessions_limit ? "Join Waiting List" : "Need More?"}
            </button>
            <button
              onClick={() => setDismissedUsageBanner(true)}
              className="p-1 rounded hover:bg-black/5 text-[#6B7280]"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Stat Cards - Only show when we have data */}
      {!loading && totalSessions > 0 && (
        <div className="stat-grid mb-8">
          <StatCard
            label="Emotion Score"
            value={pulse ? String(pulse.emotion_score) : "0"}
            subtext={
              pulse
                ? (pulse.emotion_trend > 0 ? `↑ ${pulse.emotion_trend}% vs last week` : pulse.emotion_trend < 0 ? `${pulse.emotion_trend}% vs last week` : "Stable")
                : "No data yet"
            }
            dotColor={pulse ? (pulse.emotion_score > 60 ? "#10B981" : pulse.emotion_score > 40 ? "#F59E0B" : "#EF4444") : "#9CA3AF"}
            valueColor={pulse ? (pulse.emotion_score > 60 ? "#10B981" : pulse.emotion_score > 40 ? "#F59E0B" : "#EF4444") : "#9CA3AF"}
            tooltip="Average behavioral state across all sessions. Higher = more positive engagement. Calculated from emotion predictions and session outcomes."
          />
          <StatCard
            label="Sessions Today"
            value={pulse ? String(pulse.sessions_today) : "0"}
            subtext={pulse ? `${pulse.sessions_with_issues} with issues` : "No sessions yet"}
            dotColor="#007BFF"
            valueColor="#111318"
          />
          <StatCard
            label="Frustration Alerts"
            value={pulse ? String(pulse.frustration_alerts) : "0"}
            subtext={pulse ? (pulse.frustration_alerts === 0 ? "All clear" : "pages affected") : "No data yet"}
            dotColor={pulse && pulse.frustration_alerts > 0 ? "#EF4444" : "#10B981"}
            valueColor={pulse && pulse.frustration_alerts > 0 ? "#EF4444" : "#10B981"}
          />
          <StatCard
            label="Active Experiments"
            value={pulse ? String(pulse.active_experiments) : "0"}
            subtext={pulse ? (pulse.active_experiments === 1 ? "running" : pulse.active_experiments === 0 ? "none" : "running") : "No experiments"}
            dotColor="#7C3AED"
            valueColor="#111318"
          />
        </div>
      )}

      {/* Top Issue Card - Only show when we have data */}
      {!loading && totalSessions > 0 && topIssue && (
        <TopIssueCard topIssue={topIssue} />
      )}

      {/* Pages Needing Attention - Only show when we have data */}
      {!loading && totalSessions > 0 && pagesAttention.length > 0 && (
        <PagesAttentionCard pages={pagesAttention} />
      )}

      {/* Problem Sessions - Only show when we have data */}
      {!loading && totalSessions > 0 && problemSessions.length > 0 && (
        <ProblemSessionsCard
          sessions={problemSessions}
          getTimeAgo={getTimeAgo}
          formatDuration={formatDuration}
        />
      )}

      {/* Supporting Insights - Only show when we have data */}
      {!loading && totalSessions > 0 && (
        <SupportingInsights>
          <SupportingCard title="Emotion Trends" subtitle="Last 7 days">
            <EmotionTrendsCompact />
          </SupportingCard>

          <SupportingCard title="Active Experiments">
            <ActiveExperimentsCompact count={pulse?.active_experiments || 0} />
          </SupportingCard>
        </SupportingInsights>
      )}

      {/* Waitlist Modal */}
      <WaitlistModal isOpen={showWaitlist} onClose={() => setShowWaitlist(false)} />
    </div>
  );
}

// ── Onboarding Card Component ─────────────────────────────────────────────────────

function OnboardingCard({ sdkKey, onVerify, verifying, verified }: {
  sdkKey: string | null;
  onVerify: () => void;
  verifying: boolean;
  verified: boolean;
}) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const codeSnippet = sdkKey
    ? `<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "${sdkKey}" });
</script>`
    : `<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "YOUR_SDK_KEY" });
</script>`;

  return (
    <div className="card" style={{ padding: "32px", background: "linear-gradient(135deg, #EEF5FF 0%, #F3EEFF 100%)" }}>
      <div style={{ textAlign: "center", marginBottom: "24px" }}>
        <div style={{
          width: "64px",
          height: "64px",
          borderRadius: "50%",
          background: "linear-gradient(135deg, #007BFF 0%, #7C3AED 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 16px",
        }}>
          <svg style={{ width: "32px", height: "32px", color: "white" }} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        <h2 style={{ fontSize: "24px", fontWeight: 700, color: "#111318", margin: "0 0 8px 0" }}>
          Get started — install the SDK
        </h2>
        <p style={{ fontSize: "15px", color: "#6B7280", margin: 0 }}>
          Add this snippet to your website and start tracking behavioral states
        </p>
      </div>

      {/* SDK Key */}
      <div style={{ marginBottom: "20px" }}>
        <label style={{ fontSize: "13px", fontWeight: 600, color: "#374151", display: "block", marginBottom: "8px" }}>
          Your SDK Key
        </label>
        <div style={{
          display: "flex",
          gap: "8px",
          background: "white",
          border: "1px solid #E5E7EB",
          borderRadius: "8px",
          padding: "12px",
        }}>
          <code style={{
            flex: 1,
            fontFamily: "monospace",
            fontSize: "13px",
            color: "#374151",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}>
            {sdkKey || "Sign in to see your SDK key"}
          </code>
          <button
            onClick={() => sdkKey && copyToClipboard(sdkKey)}
            disabled={!sdkKey}
            style={{
              padding: "6px 12px",
              fontSize: "12px",
              fontWeight: 600,
              color: "white",
              background: copied ? "#10B981" : "#007BFF",
              border: "none",
              borderRadius: "6px",
              cursor: sdkKey ? "pointer" : "not-allowed",
            }}
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      {/* Installation Code */}
      <div style={{ marginBottom: "20px" }}>
        <label style={{ fontSize: "13px", fontWeight: 600, color: "#374151", display: "block", marginBottom: "8px" }}>
          Installation Code (add before &lt;/body&gt; tag)
        </label>
        <div style={{ position: "relative" }}>
          <pre style={{
            background: "#1E293B",
            color: "#10B981",
            padding: "16px",
            borderRadius: "8px",
            fontSize: "12px",
            overflow: "auto",
            margin: 0,
          }}>
            {codeSnippet}
          </pre>
          <button
            onClick={() => copyToClipboard(codeSnippet)}
            style={{
              position: "absolute",
              top: "8px",
              right: "8px",
              padding: "4px 8px",
              fontSize: "11px",
              color: "white",
              background: copied ? "#10B981" : "rgba(255,255,255,0.1)",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            {copied ? "✓" : "Copy"}
          </button>
        </div>
      </div>

      {/* Links and Verify */}
      <div style={{
        display: "flex",
        gap: "12px",
        alignItems: "center",
        flexWrap: "wrap",
      }}>
        <a
          href="/docs"
          style={{
            fontSize: "13px",
            color: "#007BFF",
            textDecoration: "underline",
          }}
        >
          View full documentation →
        </a>
        <button
          onClick={onVerify}
          disabled={verifying || verified}
          style={{
            padding: "10px 20px",
            fontSize: "13px",
            fontWeight: 600,
            color: "white",
            background: verified ? "#10B981" : "#007BFF",
            border: "none",
            borderRadius: "8px",
            cursor: verifying || verified ? "default" : "pointer",
          }}
        >
          {verified ? "✓ Data received!" : verifying ? "Checking..." : "Verify Installation"}
        </button>
      </div>

      {verified && (
        <p style={{
          marginTop: "12px",
          fontSize: "13px",
          color: "#10B981",
          textAlign: "center",
        }}>
          ✓ Installation verified! Reloading dashboard...
        </p>
      )}
    </div>
  );
}

// ── Stat Card Component ───────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  subtext,
  dotColor,
  valueColor,
  tooltip,
}: {
  label: string;
  value: string;
  subtext: string;
  dotColor: string;
  valueColor: string;
  tooltip?: string;
}) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="stat-card border-blue"
      style={{ position: "relative" }}
      onMouseEnter={() => tooltip && setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="stat-label" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
        <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: dotColor }} />
        {label}
        {tooltip && (
          <span style={{ fontSize: "12px", color: "#9CA3AF", marginLeft: "2px" }}>ⓘ</span>
        )}
      </div>

      <div className="stat-value" style={{ color: valueColor }}>
        {value}
      </div>

      <div className="stat-subtext">{subtext}</div>

      {tooltip && showTooltip && (
        <div style={{
          position: "absolute",
          top: "100%",
          left: 0,
          right: 0,
          marginTop: "8px",
          padding: "8px 12px",
          fontSize: "12px",
          color: "#6B7280",
          background: "#1F2937",
          borderRadius: "6px",
          zIndex: 10,
          lineHeight: 1.4,
        }}>
          {tooltip}
        </div>
      )}
    </div>
  );
}

// ── Top Issue Card ───────────────────────────────────────────────────────────────

function TopIssueCard({ topIssue }: { topIssue: TopIssue | null }) {
  const showAllClear = !topIssue?.has_issue;

  if (showAllClear) {
    return (
      <div className="card" style={{ padding: "20px", background: "#F0FDF4", borderColor: "#BBF7D0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "20px" }}>✓</span>
          <div>
            <h3 className="type-section-title" style={{ margin: 0, color: "#059669" }}>All clear</h3>
            <p className="type-body" style={{ margin: "4px 0 0 0", color: "#059669" }}>
              No critical issues detected. Your users are having a smooth experience.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!topIssue?.has_issue) return null;

  const isHigh = topIssue.severity === "high";

  return (
    <div
      className="primary-insight-card"
      style={{
        borderLeft: `4px solid ${isHigh ? "#EF4444" : "#F59E0B"}`,
        background: isHigh ? "#FEF2F2" : "#FFFBEB",
      }}
    >
      <div className="primary-insight-header">
        <div
          className="primary-insight-icon"
          style={{
            background: isHigh ? "rgba(239, 68, 68, 0.12)" : "rgba(245, 158, 11, 0.12)",
            color: isHigh ? "#EF4444" : "#F59E0B",
          }}
        >
          {isHigh ? "⚠️" : "📊"}
        </div>
        <div>
          <div className="primary-insight-title">
            Users {topIssue.issue_type?.toLowerCase().includes("rage") ? "rage-clicking" : "struggling"} on {topIssue.page_title}
          </div>
          <div className="primary-insight-subtitle">
            {topIssue.frustration_pct}% of users affected on {topIssue.page_title} • {topIssue.affected_sessions} sessions
          </div>
        </div>
      </div>

      <div className="primary-insight-content">
        <div className="primary-insight-detail">
          <span className="primary-insight-detail-label">Frustration</span>
          <span className="primary-insight-detail-value" style={{ color: "#EF4444" }}>
            {topIssue.frustration_pct}%
          </span>
        </div>
        <div className="primary-insight-detail">
          <span className="primary-insight-detail-label">Severity</span>
          <span className="primary-insight-detail-value" style={{ color: isHigh ? "#DC2626" : "#EA580C", textTransform: "capitalize" }}>
            {topIssue.severity}
          </span>
        </div>
        <div className="primary-insight-detail">
          <span className="primary-insight-detail-label">Affected</span>
          <span className="primary-insight-detail-value">{topIssue.affected_sessions} sessions</span>
        </div>
      </div>

      <a
        href="/dashboard/diagnosis"
        className="primary-insight-cta"
        style={{
          background: isHigh ? "#EF4444" : "#007BFF",
        }}
      >
        View diagnosis →
      </a>
    </div>
  );
}

// ── Pages Attention Card ─────────────────────────────────────────────────────────

function PagesAttentionCard({ pages }: { pages: PageAttention[] }) {
  const displayPages = pages;

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Pages needing attention</h2>
        <p className="card-subtitle">Pages with the most emotional friction</p>
      </div>

      {displayPages.length === 0 ? (
        <p className="type-body" style={{ textAlign: "center", padding: "20px 0", color: "#9CA3AF" }}>
          All pages looking healthy
        </p>
      ) : (
        <div className="space-y-3">
          {displayPages.map((page, i) => (
            <div
              key={i}
              className="interactive-item"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px",
                borderRadius: "8px",
                border: "1px solid #F3F4F6",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span style={{ fontSize: "12px", fontWeight: "600", color: "#9CA3AF" }}>{i + 1}</span>
                <a
                  href={`/dashboard/pages?url=${encodeURIComponent(page.page_url)}`}
                  className="link"
                  style={{ fontSize: "14px", fontWeight: "500" }}
                >
                  {page.page_url}
                </a>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: getEmotionColor(page.dominant_emotion) }} />
                  <span style={{ fontSize: "13px", textTransform: "capitalize", color: "#374151" }}>{page.dominant_emotion}</span>
                  <span style={{ fontSize: "13px", fontWeight: "600", color: getEmotionColor(page.dominant_emotion) }}>{page.emotion_pct}%</span>
                </div>
                <span style={{ fontSize: "12px", color: "#9CA3AF" }}>{page.session_count} sessions</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Problem Sessions Card ───────────────────────────────────────────────────────

function ProblemSessionsCard({
  sessions,
  getTimeAgo,
  formatDuration,
}: {
  sessions: ProblemSession[];
  getTimeAgo: (date: string) => string;
  formatDuration: (seconds: number | null) => string;
}) {
  const displaySessions = sessions;

  if (displaySessions.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Sessions needing attention</h2>
        </div>
        <p className="type-body" style={{ textAlign: "center", padding: "20px 0", color: "#059669" }}>
          ✓ No frustrated sessions detected — your users are happy!
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Sessions needing attention</h2>
        <p className="card-subtitle">Recent sessions with negative emotions</p>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #F3F4F6" }}>
              <th style={{ textAlign: "left", padding: "10px", fontSize: "12px", color: "#9CA3AF", textTransform: "uppercase" }}>Visitor</th>
              <th style={{ textAlign: "left", padding: "10px", fontSize: "12px", color: "#9CA3AF", textTransform: "uppercase" }}>Page</th>
              <th style={{ textAlign: "left", padding: "10px", fontSize: "12px", color: "#9CA3AF", textTransform: "uppercase" }}>Emotion</th>
              <th style={{ textAlign: "left", padding: "10px", fontSize: "12px", color: "#9CA3AF", textTransform: "uppercase" }}>Duration</th>
              <th style={{ textAlign: "left", padding: "10px", fontSize: "12px", color: "#9CA3AF", textTransform: "uppercase" }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {displaySessions.map((session) => (
              <tr
                key={session.id}
                className="interactive-item"
                style={{ borderBottom: "1px solid #F3F4F6", cursor: "pointer" }}
                onClick={() => window.location.href = `/dashboard/sessions/${session.id}`}
              >
                <td style={{ padding: "12px 10px" }}>
                  <span style={{ fontFamily: "monospace", fontSize: "13px", color: "#007BFF" }}>
                    {session.visitor_id}
                  </span>
                </td>
                <td style={{ padding: "12px 10px", fontSize: "14px" }}>{session.page_url}</td>
                <td style={{ padding: "12px 10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: getEmotionColor(session.primary_emotion) }} />
                    <span style={{ fontSize: "13px", textTransform: "capitalize" }}>{session.primary_emotion}</span>
                  </div>
                </td>
                <td style={{ padding: "12px 10px", fontSize: "13px", color: "#6B7280" }}>{formatDuration(session.duration_seconds)}</td>
                <td style={{ padding: "12px 10px", fontSize: "13px", color: "#6B7280" }}>{getTimeAgo(session.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Supporting Components ─────────────────────────────────────────────────────

function SkeletonCard({ height = "140px" }: { height?: string }) {
  return (
    <div
      className="bg-[hsl(var(--secondary))] rounded-xl relative overflow-hidden"
      style={{ height }}
    >
      <div
        className="absolute inset-0 bg-gradient-to-r from-[hsl(var(--secondary))] via-[hsl(var(--muted))] to-[hsl(var(--secondary))] bg-[length:200%_100%] animate-[shimmer_1.5s_infinite]"
      />
    </div>
  );
}

function EmotionTrendsCompact() {
  const [data, setData] = useState<{ day: string; frustrated: number; confused: number; engaged: number; disengaged: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/dashboard/emotion-trends?days=7`, { credentials: "include" });
        if (res.ok) {
          const trendData = await res.json();
          if (trendData && trendData.length > 0) {
            setHasData(true);
            const chartData = trendData.map((d: any) => ({
              day: d.label,
              frustrated: d.risk || 0,
              confused: d.friction || 0,
              engaged: Math.max(0, 100 - (d.friction || 0) - (d.risk || 0) / 2),
              disengaged: Math.max(0, (d.risk || 0) / 4),
            }));
            setData(chartData);
          }
        }
      } catch (_err) {
        // Use empty on error
      } finally {
        setLoading(false);
      }
    };
    fetchTrends();
  }, []);

  if (loading) {
    return <div style={{ padding: "20px 0", textAlign: "center" }}><SkeletonCard height="120px" /></div>;
  }

  if (!hasData || data.length === 0) {
    return <p style={{ fontSize: "13px", color: "#9CA3AF", textAlign: "center", padding: "20px 0" }}>Trend data being collected...</p>;
  }

  return (
    <div className="chart-compact">
      <svg viewBox="0 0 300 100" style={{ width: "100%", height: "120px" }}>
        {data.map((d, i) => {
          const x = 30 + i * 40;
          const yFrustrated = 80 - (d.frustrated / 100) * 60;
          const yConfused = 80 - (d.confused / 100) * 60;
          const yEngaged = 80 - (d.engaged / 100) * 60;
          const yDisengaged = 80 - (d.disengaged / 100) * 60;

          return (
            <g key={i}>
              <line x1={x} y1={80} x2={x} y2={20} stroke="#E5E7EB" strokeWidth="1" />
              <circle cx={x} cy={yFrustrated} r="3" fill={EMOTION_COLORS.frustrated} />
              <circle cx={x} cy={yConfused} r="3" fill={EMOTION_COLORS.confused} />
              <circle cx={x} cy={yEngaged} r="3" fill={EMOTION_COLORS.engaged} />
              <circle cx={x} cy={yDisengaged} r="3" fill={EMOTION_COLORS.disengaged} />
              <text x={x} y="92" fontSize="8" fill="#9CA3AF" textAnchor="middle">{d.day.slice(0, 3)}</text>
            </g>
          );
        })}
      </svg>
      <div style={{ display: "flex", justifyContent: "center", gap: "12px", marginTop: "8px", flexWrap: "wrap" }}>
        <LegendItem color={EMOTION_COLORS.frustrated} label="Frustrated" />
        <LegendItem color={EMOTION_COLORS.confused} label="Confused" />
        <LegendItem color={EMOTION_COLORS.engaged} label="Engaged" />
        <LegendItem color={EMOTION_COLORS.disengaged} label="Disengaged" />
      </div>
    </div>
  );
}

function ActiveExperimentsCompact({ count }: { count: number }) {
  if (count === 0) {
    return (
      <p className="type-body" style={{ textAlign: "center", padding: "16px 0", color: "#9CA3AF" }}>
        No active experiments. <a href="/dashboard/experiments" className="link">Create one →</a>
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {count > 0 && (
        <>
          <div className="list-item">
            <div className="list-item-icon purple">
              <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: "16px", height: "16px" }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023-.501.05.75.082M5 14.5l-1.456 7.28a.75.75 0 00.736.893h15.44a.75.75 0 00.736-.893L19 14.5M5 14.5h14" />
              </svg>
            </div>
            <div className="list-item-content">
              <div className="list-item-title">{count} Active Experiment{count !== 1 ? "s" : ""}</div>
              <div className="list-item-meta">
                <span className="badge badge-green">Running</span>
              </div>
            </div>
          </div>
          <a href="/dashboard/experiments" className="link" style={{ fontSize: "13px" }}>View all experiments →</a>
        </>
      )}
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: color }} />
      <span style={{ fontSize: "11px", color: "#6B7280" }}>{label}</span>
    </div>
  );
}

function SupportingInsights({ children }: { children: React.ReactNode }) {
  return (
    <div className="supporting-insights">
      <div className="supporting-insights-header">
        <h3 className="supporting-insights-title">Supporting Insights</h3>
        <span style={{ fontSize: "12px", color: "#9CA3AF" }}>Context & trends</span>
      </div>
      <div className="supporting-insights-grid">
        {children}
      </div>
    </div>
  );
}

function SupportingCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="supporting-card">
      <div className="supporting-card-title">{title}</div>
      {subtitle && <div className="supporting-card-subtitle">{subtitle}</div>}
      {children}
    </div>
  );
}
