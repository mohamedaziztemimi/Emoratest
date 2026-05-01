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
  sessions_limit: number;
  reset_date: string;
}

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
    if (!seconds) return ". ";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  };

  // Get emotion color
  const getEmotionColor = (emotion: string) => {
    const colors: Record<string, string> = {
      frustration: "#EF4444",
      confusion: "#F59E0B",
      anxiety: "#F97316",
      hesitation: "#8B5CF6",
      satisfaction: "#059669",
      delight: "#10B981",
      focus: "#3B82F6",
      boredom: "#6B7280",
    };
    return colors[emotion] || "#6B7280";
  };

  return (
    <div>
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="type-page-title mb-1">Overview</h1>
        <p className="text-sm text-secondary">Your emotion intelligence command center</p>
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

      {/* Session Limit Warning Banner - Prompt 13 */}
      {!loading && usage && !dismissedUsageBanner && (
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

      {/* Stat Cards - Prompt 14 */}
      {!loading && (
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

      {/* Top Issue Card - Prompt 15 */}
      {!loading && topIssue && (
        <TopIssueCard topIssue={topIssue} />
      )}

      {/* Pages Needing Attention - Prompt 16 */}
      {!loading && pagesAttention.length > 0 && (
        <PagesAttentionCard pages={pagesAttention} />
      )}

      {/* Problem Sessions - Prompt 17 */}
      {!loading && problemSessions.length > 0 && (
        <ProblemSessionsCard
          sessions={problemSessions}
          getTimeAgo={getTimeAgo}
          formatDuration={formatDuration}
          getEmotionColor={getEmotionColor}
        />
      )}

      {!loading && problemSessions.length === 0 && (
        <div className="card" style={{ padding: "20px" }}>
          <p className="type-body" style={{ textAlign: "center", color: "#059669" }}>
            ✓ No frustrated sessions detected — your users are happy!
          </p>
        </div>
      )}

      {/* Supporting Insights */}
      {!loading && (
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

// ── Stat Card Component ───────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  subtext,
  dotColor,
  valueColor,
}: {
  label: string;
  value: string;
  subtext: string;
  dotColor: string;
  valueColor: string;
}) {
  return (
    <div className="stat-card border-blue">
      <div className="stat-label" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
        <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: dotColor }} />
        {label}
      </div>

      <div className="stat-value" style={{ color: valueColor }}>
        {value}
      </div>

      <div className="stat-subtext">{subtext}</div>
    </div>
  );
}

// ── Top Issue Card - Prompt 15 ───────────────────────────────────────────────────

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

// ── Pages Attention Card - Prompt 16 ─────────────────────────────────────────────

function PagesAttentionCard({ pages }: { pages: PageAttention[] }) {
  const displayPages = pages;

  const getEmotionColor = (emotion: string) => {
    const colors: Record<string, string> = {
      frustration: "#EF4444",
      confusion: "#F59E0B",
      anxiety: "#F97316",
      hesitation: "#8B5CF6",
      satisfaction: "#059669",
      delight: "#10B981",
      focus: "#3B82F6",
      boredom: "#6B7280",
    };
    return colors[emotion] || "#6B7280";
  };

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

// ── Problem Sessions Card - Prompt 17 ────────────────────────────────────────────

function ProblemSessionsCard({
  sessions,
  getTimeAgo,
  formatDuration,
  getEmotionColor,
}: {
  sessions: ProblemSession[];
  getTimeAgo: (date: string) => string;
  formatDuration: (seconds: number | null) => string;
  getEmotionColor: (emotion: string) => string;
}) {
  const displaySessions = sessions;

  if (displaySessions.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Sessions needing attention</h2>
        </div>
        <p className="type-body" style={{ textAlign: "center", padding: "20px 0", color: "#059669" }}>
          ✓ No frustrated sessions detected .  your users are happy!
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
  const [data, setData] = useState<{ day: string; confusion: number; frustration: number; delight: number }[]>([]);
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
              confusion: d.friction,
              frustration: d.risk,
              delight: Math.max(0, 100 - d.friction - d.risk / 2),
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

  if (data.length === 0) {
    return <p style={{ fontSize: "13px", color: "#9CA3AF", textAlign: "center", padding: "20px 0" }}>Trend data being collected...</p>;
  }

  return (
    <div className="chart-compact">
      <svg viewBox="0 0 300 100" style={{ width: "100%", height: "120px" }}>
        {data.map((d, i) => {
          const x = 30 + i * 40;
          const yConfusion = 80 - (d.confusion / 100) * 60;
          const yFrustration = 80 - (d.frustration / 100) * 60;
          const yDelight = 80 - (d.delight / 100) * 60;

          return (
            <g key={i}>
              <line x1={x} y1={80} x2={x} y2={20} stroke="#E5E7EB" strokeWidth="1" />
              <circle cx={x} cy={yConfusion} r="3" fill="#F59E0B" />
              <circle cx={x} cy={yFrustration} r="3" fill="#EF4444" />
              <circle cx={x} cy={yDelight} r="3" fill="#10B981" />
              <text x={x} y="92" fontSize="8" fill="#9CA3AF" textAnchor="middle">{d.day.slice(0, 3)}</text>
            </g>
          );
        })}
      </svg>
      <div style={{ display: "flex", justifyContent: "center", gap: "12px", marginTop: "8px" }}>
        <LegendItem color="#F59E0B" label="Confusion" />
        <LegendItem color="#EF4444" label="Frustration" />
        <LegendItem color="#10B981" label="Delight" />
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
