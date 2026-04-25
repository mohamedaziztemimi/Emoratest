"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

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

// ── Main Component ─────────────────────────────────────────────────────────────

export default function OverviewPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [hasData, setHasData] = useState(false);

  // Data from new endpoints
  const [pulse, setPulse] = useState<EmotionPulse | null>(null);
  const [topIssue, setTopIssue] = useState<TopIssue | null>(null);
  const [pagesAttention, setPagesAttention] = useState<PageAttention[]>([]);
  const [problemSessions, setProblemSessions] = useState<ProblemSession[]>([]);

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
          const hasRealData = (sessionsData.total || 0) > 0;
          setHasData(hasRealData);

          // Fetch all dashboard data in parallel
          const [pulseRes, issueRes, pagesRes, sessionsListRes] = await Promise.all([
            fetch(`${apiUrl}/api/v1/dashboard/emotion-pulse`, { credentials: "include" }),
            fetch(`${apiUrl}/api/v1/dashboard/top-issue`, { credentials: "include" }),
            fetch(`${apiUrl}/api/v1/dashboard/pages-attention?limit=3`, { credentials: "include" }),
            fetch(`${apiUrl}/api/v1/dashboard/problem-sessions?limit=5`, { credentials: "include" }),
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
    if (!seconds) return "—";
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
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

      {/* No Data State */}
      {!loading && !hasData && (
        <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6 p-4 sm:p-6 mb-6 bg-white border border-[hsl(var(--border))] rounded-2xl">
          <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-2xl flex-shrink-0">
            🚀
          </div>
          <div className="flex-1 text-center sm:text-left">
            <h3 className="text-lg font-bold text-[hsl(var(--foreground))] mb-1">
              Install the SDK to see your real data
            </h3>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">
              You&apos;re seeing demo data. Add one line of code to your website to start detecting emotions.
            </p>
          </div>
          <div className="flex gap-3 w-full sm:w-auto">
            <a
              href="/dashboard/welcome"
              className="flex-1 sm:flex-none bg-gradient-to-r from-[#007BFF] to-[#7C3AED] text-white px-5 py-2.5 rounded-full font-semibold text-sm hover:opacity-90 transition-opacity"
            >
              Install SDK →
            </a>
            <a
              href="/docs"
              className="flex-1 sm:flex-none bg-white text-[#007BFF] border border-[hsl(var(--border))] rounded-lg px-6 py-3 text-sm font-medium hover:bg-[hsl(var(--accent))] transition-colors"
            >
              View docs
            </a>
          </div>
        </div>
      )}

      {/* Stat Cards - Prompt 14 */}
      {!loading && (
        <div className="stat-grid mb-8">
          <StatCard
            label="Emotion Score"
            value={hasData && pulse ? String(pulse.emotion_score) : "72"}
            subtext={
              hasData && pulse
                ? (pulse.emotion_trend > 0 ? `↑ ${pulse.emotion_trend}% vs last week` : pulse.emotion_trend < 0 ? `${pulse.emotion_trend}% vs last week` : "Stable")
                : "↑ 5% vs last week"
            }
            dotColor={hasData && pulse ? (pulse.emotion_score > 60 ? "#10B981" : pulse.emotion_score > 40 ? "#F59E0B" : "#EF4444") : "#10B981"}
            valueColor={hasData && pulse ? (pulse.emotion_score > 60 ? "#10B981" : pulse.emotion_score > 40 ? "#F59E0B" : "#EF4444") : "#10B981"}
            showDemoBadge={!hasData}
          />
          <StatCard
            label="Sessions Today"
            value={hasData && pulse ? String(pulse.sessions_today) : "1,247"}
            subtext={
              hasData && pulse
                ? `${pulse.sessions_with_issues} with issues`
                : "142 with issues"
            }
            dotColor="#007BFF"
            valueColor="#111318"
            showDemoBadge={!hasData}
          />
          <StatCard
            label="Frustration Alerts"
            value={hasData && pulse ? String(pulse.frustration_alerts) : "3"}
            subtext={hasData && pulse ? (pulse.frustration_alerts === 0 ? "All clear" : "pages affected") : "pages affected"}
            dotColor={hasData && pulse && pulse.frustration_alerts > 0 ? "#EF4444" : "#10B981"}
            valueColor={hasData && pulse && pulse.frustration_alerts > 0 ? "#EF4444" : "#10B981"}
            showDemoBadge={!hasData}
          />
          <StatCard
            label="Active Experiments"
            value={hasData && pulse ? String(pulse.active_experiments) : "2"}
            subtext={hasData && pulse ? (pulse.active_experiments === 1 ? "running" : "running") : "running"}
            dotColor="#7C3AED"
            valueColor="#111318"
            showDemoBadge={!hasData}
          />
        </div>
      )}

      {/* Top Issue Card - Prompt 15 */}
      {!loading && (
        <TopIssueCard hasData={hasData} topIssue={topIssue} />
      )}

      {/* Pages Needing Attention - Prompt 16 */}
      {!loading && pagesAttention.length > 0 && (
        <PagesAttentionCard hasData={hasData} pages={pagesAttention} />
      )}

      {/* Problem Sessions - Prompt 17 */}
      {!loading && (
        <ProblemSessionsCard
          hasData={hasData}
          sessions={problemSessions}
          getTimeAgo={getTimeAgo}
          formatDuration={formatDuration}
          getEmotionColor={getEmotionColor}
        />
      )}

      {/* Supporting Insights */}
      {!loading && (
        <SupportingInsights hasData={hasData}>
          <SupportingCard title="Emotion Trends" subtitle="Last 7 days">
            <EmotionTrendsCompact hasData={hasData} />
          </SupportingCard>

          <SupportingCard title="Active Experiments">
            <ActiveExperimentsCompact hasData={hasData} count={pulse?.active_experiments || 0} />
          </SupportingCard>
        </SupportingInsights>
      )}
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
  showDemoBadge = false,
}: {
  label: string;
  value: string;
  subtext: string;
  dotColor: string;
  valueColor: string;
  showDemoBadge?: boolean;
}) {
  return (
    <div className="stat-card border-blue">
      {showDemoBadge && (
        <span className="absolute top-3 right-3 bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] text-[10px] rounded px-1.5 py-0.5 font-medium">
          Demo
        </span>
      )}

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

function TopIssueCard({ hasData, topIssue }: { hasData: boolean; topIssue: TopIssue | null }) {
  // Demo data when no real data
  const demoIssue = {
    has_issue: true,
    page_url: "/checkout",
    page_title: "Checkout",
    issue_type: "Rage click spike",
    severity: "high" as const,
    affected_sessions: 50,
    frustration_pct: 38,
    time_window: "24h",
  };

  const issue = hasData && topIssue?.has_issue ? topIssue : demoIssue;
  const showAllClear = hasData && !topIssue?.has_issue;

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

  if (!issue.has_issue) return null;

  const isHigh = issue.severity === "high";

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
            Users {issue.issue_type?.toLowerCase().includes("rage") ? "rage-clicking" : "struggling"} on {issue.page_title}
          </div>
          <div className="primary-insight-subtitle">
            {issue.frustration_pct}% of users affected on {issue.page_title} • {issue.affected_sessions} sessions
          </div>
        </div>
      </div>

      <div className="primary-insight-content">
        <div className="primary-insight-detail">
          <span className="primary-insight-detail-label">Frustration</span>
          <span className="primary-insight-detail-value" style={{ color: "#EF4444" }}>
            {issue.frustration_pct}%
          </span>
        </div>
        <div className="primary-insight-detail">
          <span className="primary-insight-detail-label">Severity</span>
          <span className="primary-insight-detail-value" style={{ color: isHigh ? "#DC2626" : "#EA580C", textTransform: "capitalize" }}>
            {issue.severity}
          </span>
        </div>
        <div className="primary-insight-detail">
          <span className="primary-insight-detail-label">Affected</span>
          <span className="primary-insight-detail-value">{issue.affected_sessions} sessions</span>
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

      {!hasData && (
        <span className="absolute top-3 right-3 bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] text-[10px] rounded px-1.5 py-0.5 font-medium">
          Demo
        </span>
      )}
    </div>
  );
}

// ── Pages Attention Card - Prompt 16 ─────────────────────────────────────────────

function PagesAttentionCard({ hasData, pages }: { hasData: boolean; pages: PageAttention[] }) {
  const displayPages = hasData ? pages : [
    { page_url: "/checkout", dominant_emotion: "frustration", emotion_pct: 38, session_count: 89 },
    { page_url: "/pricing", dominant_emotion: "confusion", emotion_pct: 24, session_count: 56 },
    { page_url: "/signup", dominant_emotion: "hesitation", emotion_pct: 18, session_count: 34 },
  ];

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

              {!hasData && (
                <span className="absolute top-3 right-3 bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] text-[10px] rounded px-1.5 py-0.5 font-medium">
                  Demo
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Problem Sessions Card - Prompt 17 ────────────────────────────────────────────

function ProblemSessionsCard({
  hasData,
  sessions,
  getTimeAgo,
  formatDuration,
  getEmotionColor,
}: {
  hasData: boolean;
  sessions: ProblemSession[];
  getTimeAgo: (date: string) => string;
  formatDuration: (seconds: number | null) => string;
  getEmotionColor: (emotion: string) => string;
}) {
  const displaySessions = hasData ? sessions : [
    { id: "1", visitor_id: "a1b2c3d4", page_url: "/checkout", primary_emotion: "frustration", emotion_confidence: 78, created_at: new Date(Date.now() - 300000).toISOString(), duration_seconds: 154 },
    { id: "2", visitor_id: "e5f6g7h8", page_url: "/pricing", primary_emotion: "confusion", emotion_confidence: 65, created_at: new Date(Date.now() - 900000).toISOString(), duration_seconds: 89 },
    { id: "3", visitor_id: "i9j0k1l2", page_url: "/signup", primary_emotion: "anxiety", emotion_confidence: 72, created_at: new Date(Date.now() - 1800000).toISOString(), duration_seconds: 201 },
  ];

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

      {!hasData && (
        <div style={{ position: "relative" }}>
          <span className="absolute top-3 right-3 bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] text-[10px] rounded px-1.5 py-0.5 font-medium">
            Demo
          </span>
        </div>
      )}
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

function EmotionTrendsCompact({ hasData }: { hasData: boolean }) {
  const [data, setData] = useState<{ day: string; confusion: number; frustration: number; delight: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/dashboard/emotion-trends?days=7`, { credentials: "include" });
        if (res.ok) {
          const trendData = await res.json();
          const chartData = trendData.map((d: any) => ({
            day: d.label,
            confusion: d.friction,
            frustration: d.risk,
            delight: Math.max(0, 100 - d.friction - d.risk / 2),
          }));
          setData(chartData);
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

function ActiveExperimentsCompact({ hasData, count }: { hasData: boolean; count: number }) {
  if (hasData && count === 0) {
    return (
      <p className="type-body" style={{ textAlign: "center", padding: "16px 0", color: "#9CA3AF" }}>
        No active experiments. <a href="/dashboard/experiments" className="link">Create one →</a>
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="list-item">
        <div className="list-item-icon purple">
          <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: "16px", height: "16px" }}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023-.501.05.75.082M5 14.5l-1.456 7.28a.75.75 0 00.736.893h15.44a.75.75 0 00.736-.893L19 14.5M5 14.5h14" />
          </svg>
        </div>
        <div className="list-item-content">
          <div className="list-item-title">Checkout CTA Test</div>
          <div className="list-item-meta">
            <span className="badge badge-purple">A/B</span>
            <span className="badge badge-green">Running</span>
          </div>
          <div className="list-item-subtitle mt-1">Day 4 of 14</div>
        </div>
      </div>
      <a href="/dashboard/experiments" className="link" style={{ fontSize: "13px" }}>View all experiments →</a>
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

function SupportingInsights({ hasData, children }: { hasData: boolean; children: React.ReactNode }) {
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
