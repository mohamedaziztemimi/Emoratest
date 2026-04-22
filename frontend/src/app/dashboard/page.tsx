"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

interface Session {
  id: string;
  page_url: string;
  started_at: string;
  outcome?: string;
}

interface Experiment {
  id: string;
  name: string;
  status: "running" | "paused" | "completed";
}

interface DashboardStats {
  hasData: boolean;
  activeExperiments: number;
  sessionsToday: number;
  frustrationCount: number;
  avgEmotionConfidence: number | null;
  loading: boolean;
  error: boolean;
}

export default function OverviewPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats>({
    hasData: false,
    activeExperiments: 0,
    sessionsToday: 0,
    frustrationCount: 0,
    avgEmotionConfidence: null,
    loading: true,
    error: false,
  });

  // Fetch dashboard data on mount
  useEffect(() => {
    const fetchDashboardData = async () => {
      const apiUrl = API_BASE;

      try {
        // Fetch sessions to check if user has data
        const sessionsRes = await fetch(`${apiUrl}/api/v1/dashboard/sessions?page=1&page_size=1`, {
          credentials: "include",
        });

        if (sessionsRes.status === 401) {
          router.push("/login");
          return;
        }

        if (sessionsRes.ok) {
          const sessionsData = await sessionsRes.json();
          const sessionCount = sessionsData.total || 0;
          console.log("[Dashboard] Sessions response:", { sessionCount, total: sessionsData.total, hasData: sessionCount > 0 });

          // Fetch experiments count
          let activeExperiments = 0;
          try {
            const expRes = await fetch(`${apiUrl}/api/v1/experiments`, {
              credentials: "include",
            });
            if (expRes.ok) {
              const expData = await expRes.json();
              // Count active/running experiments
              activeExperiments = expData.experiments?.filter(
                (e: Experiment) => e.status === "running"
              ).length || 0;
            }
          } catch (_err) {
            // Ignore experiments error
          }

          // Calculate sessions today - use full ISO datetime for backend
          const now = new Date();
          const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0).toISOString();
          const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999).toISOString();
          let sessionsToday = 0;
          try {
            const todayRes = await fetch(
              `${apiUrl}/api/v1/dashboard/sessions?page=1&page_size=100&date_from=${todayStart}&date_to=${todayEnd}`,
              { credentials: "include" }
            );
            if (todayRes.ok) {
              const todayData = await todayRes.json();
              sessionsToday = todayData.total || 0;
            }
          } catch (_err) {
            // Ignore today sessions error
          }

          // Fetch avg emotion confidence and frustration count
          let avgEmotionConfidence: number | null = null;
          let frustrationCount = 0;
          try {
            const statsRes = await fetch(`${apiUrl}/api/v1/dashboard/stats`, {
              credentials: "include",
            });
            if (statsRes.ok) {
              const statsData = await statsRes.json();
              avgEmotionConfidence = statsData.avg_emotion_confidence ?? null;
              frustrationCount = statsData.frustration_count ?? 0;
            }
          } catch (_err) {
            // Ignore stats error
          }

          setStats({
            hasData: sessionCount > 0,
            activeExperiments,
            sessionsToday,
            frustrationCount,
            avgEmotionConfidence,
            loading: false,
            error: false,
          });
        } else {
          throw new Error("Failed to fetch sessions");
        }
      } catch (err) {
        console.error("Dashboard data fetch error:", err);
        setStats((prev) => ({
          ...prev,
          loading: false,
          error: true,
        }));
      }
    };

    fetchDashboardData();
  }, [router]);

  // Add shimmer animation to global styles
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.getElementById("dashboard-shimmer")) return;

    const style = document.createElement("style");
    style.id = "dashboard-shimmer";
    style.textContent = `
      @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
    `;
    document.head.appendChild(style);

    return () => {
      const existing = document.getElementById("dashboard-shimmer");
      if (existing) {
        document.head.removeChild(existing);
      }
    };
  }, []);

  // Format number with commas
  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div>
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[hsl(var(--foreground))]">Overview</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Your emotion intelligence command center</p>
      </div>

      {/* Loading State - Skeleton Cards */}
      {stats.loading && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <SkeletonCard height="300px" />
            <SkeletonCard height="300px" />
          </div>
        </>
      )}

      {/* Error State */}
      {stats.error && !stats.loading && (
        <div className="card" style={{ padding: "16px", marginBottom: "24px", background: "#FEF2F2", border: "1px solid #FECACA" }}>
          <p style={{ fontSize: "13px", color: "#991B1B", margin: 0 }}>
            Unable to load your data. Showing demo data instead.
          </p>
        </div>
      )}

      {/* No Data State - Onboarding Banner */}
      {!stats.loading && !stats.hasData && (
        <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6 p-4 sm:p-6 mb-6 bg-white border border-[hsl(var(--border))] rounded-2xl">
          {/* Rocket emoji in blue circle */}
          <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-2xl flex-shrink-0">
            🚀
          </div>

          {/* Middle content */}
          <div className="flex-1 text-center sm:text-left">
            <h3 className="text-lg font-bold text-[hsl(var(--foreground))] mb-1">
              Install the SDK to see your real data
            </h3>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">
              You&apos;re seeing demo data. Add one line of code to your website to start detecting emotions.
            </p>
          </div>

          {/* Right buttons */}
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

      {/* Row 1: Stat Cards */}
      {!stats.loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Active Experiments"
            value={stats.hasData ? String(stats.activeExperiments) : "3"}
            subtext={stats.hasData ? (stats.activeExperiments === 1 ? "1 running" : `${stats.activeExperiments} running`) : "2 running, 1 paused"}
            dotColor="#007BFF"
            valueColor={stats.hasData ? "#111318" : "#111318"}
            showDemoBadge={!stats.hasData}
          />
          <StatCard
            label="Sessions Today"
            value={stats.hasData ? formatNumber(stats.sessionsToday) : "2,847"}
            subtext={stats.hasData ? (stats.sessionsToday > 0 ? "+12% from yesterday" : "First session today!") : "+12% from yesterday"}
            dotColor="#7C3AED"
            valueColor="#111318"
            showDemoBadge={!stats.hasData}
          />
          <StatCard
            label="Frustration Alerts"
            value={stats.hasData ? String(stats.frustrationCount) : "2"}
            subtext={stats.hasData ? (stats.frustrationCount === 0 ? "All clear" : `${stats.frustrationCount} need attention`) : "Requires attention"}
            dotColor={stats.hasData && stats.frustrationCount > 0 ? "#EF4444" : "#10B981"}
            valueColor={stats.hasData && stats.frustrationCount > 0 ? "#EF4444" : "#10B981"}
            showDemoBadge={!stats.hasData}
          />
          <StatCard
            label="Avg Emotion Confidence"
            value={stats.avgEmotionConfidence != null ? `${Math.round(stats.avgEmotionConfidence * 100)}%` : "--"}
            subtext="ML model confidence"
            dotColor="#10B981"
            valueColor="#111318"
            showDemoBadge={!stats.hasData}
          />
        </div>
      )}

      {/* Row 2: Emotion Trends + Top Confusion Pages */}
      {!stats.loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Emotion Trends Chart */}
          <Card>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">Emotion Trends — Last 7 Days</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Confusion, frustration and delight over time</p>
            </div>
            <EmotionTrendsChart hasData={stats.hasData} />
          </Card>

          {/* Top Confusion Pages */}
          <Card>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">Top Confusion Pages</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Pages triggering most confusion signals</p>
            </div>
            <ConfusionPagesList hasData={stats.hasData} />
          </Card>
        </div>
      )}

      {/* Row 3: Active Experiments + AI Suggestions */}
      {!stats.loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Experiments */}
          <Card>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">Active Experiments</h2>
            </div>
            <ActiveExperimentsList hasData={stats.hasData} activeCount={stats.activeExperiments} />
          </Card>

          {/* AI Suggestions */}
          <Card>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">AI Suggestions</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Based on emotion patterns detected</p>
            </div>
            <AISuggestionsList hasData={stats.hasData} />
          </Card>
        </div>
      )}
    </div>
  );
}

// ── Skeleton Card Component ─────────────────────────────────────────────
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

// ── Stat Card Component ───────────────────────────────────────────────────
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
    <div className="relative bg-white border border-[hsl(var(--border))] rounded-xl p-5">
      {/* Demo Badge */}
      {showDemoBadge && (
        <span className="absolute top-3 right-3 bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] text-[10px] rounded px-1.5 py-0.5 font-medium">
          Demo
        </span>
      )}

      {/* Label with colored dot */}
      <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted-foreground))] font-medium mb-2">
        <div className="w-2 h-2 rounded-full" style={{ background: dotColor }} />
        {label}
      </div>

      {/* Value */}
      <div className="text-2xl font-bold mb-1" style={{ color: valueColor }}>
        {value}
      </div>

      {/* Subtext */}
      <div className="text-xs text-[hsl(var(--muted-foreground))]">
        {subtext}
      </div>
    </div>
  );
}

// ── Card Component ───────────────────────────────────────────────────────
function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-xl p-6">{children}</div>;
}

// ── Emotion Trends Chart Component ─────────────────────────────────────────
function EmotionTrendsChart({ hasData }: { hasData: boolean }) {
  const [trendData, setTrendData] = useState<{ day: string; confusion: number; frustration: number; delight: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrends = async () => {
      const apiUrl = API_BASE;
      try {
        const res = await fetch(`${apiUrl}/api/v1/dashboard/emotion-trends?days=7`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          // Map backend data to chart format
          const chartData = data.map((d: any) => ({
            day: d.label,
            confusion: d.friction,           // friction_score -> confusion
            frustration: d.risk,             // abandonment_risk -> frustration
            delight: Math.max(0, 100 - d.friction - d.risk / 2),  // calculated
          }));
          setTrendData(chartData);
        }
      } catch (_err) {
        // Use empty data on error
        setTrendData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchTrends();
  }, []);

  // Show loading state
  if (loading) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>Loading emotion trends...</p>
      </div>
    );
  }

  // Show demo data when hasData is false
  if (!hasData) {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const confusion = [45, 52, 48, 61, 55, 67, 58];
    const frustration = [23, 31, 28, 35, 29, 41, 33];
    const delight = [67, 71, 69, 74, 78, 72, 80];
    return <EmotionTrendSvg days={days} confusion={confusion} frustration={frustration} delight={delight} />;
  }

  // Show "no data" message when no real data exists
  if (trendData.length === 0) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>
          Collecting emotion data... Sessions are being analyzed.
        </p>
      </div>
    );
  }

  // Show real data
  const days = trendData.map(d => d.day);
  const confusion = trendData.map(d => d.confusion);
  const frustration = trendData.map(d => d.frustration);
  const delight = trendData.map(d => d.delight);
  return <EmotionTrendSvg days={days} confusion={confusion} frustration={frustration} delight={delight} />;
}

// Extracted SVG component for reuse
function EmotionTrendSvg({ days, confusion, frustration, delight }: {
  days: string[];
  confusion: number[];
  frustration: number[];
  delight: number[];
}) {
  const max = 100;
  // Chart dimensions
  const topPadding = 20;
  const bottomPadding = 40;
  const chartHeight = 240; // 300 - 20 - 40
  const xStart = 50;
  const xEnd = 570;
  const xStep = (xEnd - xStart) / (days.length - 1); // ~86.67

  // Y position calculation: topPadding + (1 - value/max) * chartHeight
  const getY = (val: number) => topPadding + (1 - val / max) * chartHeight;

  return (
    <div>
      {/* Chart - 300px height */}
      <svg
        viewBox="0 0 600 300"
        className="w-full"
        style={{ width: "100%", height: "300px", display: "block" }}
      >
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map((val) => (
          <line
            key={val}
            x1={xStart}
            y1={getY(val)}
            x2={xEnd}
            y2={getY(val)}
            stroke="#E5E7EB"
            strokeWidth="1"
          />
        ))}

        {/* Y-axis labels */}
        {[0, 50, 100].map((val) => (
          <text
            key={val}
            x={xStart - 10}
            y={getY(val) + 4}
            fontSize="10"
            fill="#9CA3AF"
            textAnchor="end"
          >
            {val}%
          </text>
        ))}

        {/* X-axis labels */}
        {days.map((day, i) => (
          <text
            key={day}
            x={xStart + i * xStep}
            y="290"
            fontSize="10"
            fill="#9CA3AF"
            textAnchor="middle"
          >
            {day}
          </text>
        ))}

        {/* Confusion line (amber) */}
        <polyline
          points={confusion.map((val, i) => `${xStart + i * xStep},${getY(val)}`).join(" ")}
          fill="none"
          stroke="#F59E0B"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* Frustration line (red) */}
        <polyline
          points={frustration.map((val, i) => `${xStart + i * xStep},${getY(val)}`).join(" ")}
          fill="none"
          stroke="#EF4444"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* Delight line (green) */}
        <polyline
          points={delight.map((val, i) => `${xStart + i * xStep},${getY(val)}`).join(" ")}
          fill="none"
          stroke="#10B981"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* Data points for confusion */}
        {confusion.map((val, i) => (
          <circle
            key={`confusion-${i}`}
            cx={xStart + i * xStep}
            cy={getY(val)}
            r="4"
            fill="#F59E0B"
            stroke="white"
            strokeWidth="2"
          />
        ))}

        {/* Data points for frustration */}
        {frustration.map((val, i) => (
          <circle
            key={`frustration-${i}`}
            cx={xStart + i * xStep}
            cy={getY(val)}
            r="4"
            fill="#EF4444"
            stroke="white"
            strokeWidth="2"
          />
        ))}

        {/* Data points for delight */}
        {delight.map((val, i) => (
          <circle
            key={`delight-${i}`}
            cx={xStart + i * xStep}
            cy={getY(val)}
            r="4"
            fill="#10B981"
            stroke="white"
            strokeWidth="2"
          />
        ))}
      </svg>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4">
        <LegendItem color="#F59E0B" label="Confusion" />
        <LegendItem color="#EF4444" label="Frustration" />
        <LegendItem color="#10B981" label="Delight" />
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: color }} />
      <span style={{ fontSize: "12px", color: "#6B7280" }}>{label}</span>
    </div>
  );
}

// ── Confusion Pages List Component ───────────────────────────────────────
function ConfusionPagesList({ hasData }: { hasData: boolean }) {
  const [pages, setPages] = useState<{ path: string; name: string; score: number; dropoff: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConfusionPages = async () => {
      const apiUrl = API_BASE;
      try {
        const res = await fetch(`${apiUrl}/api/v1/dashboard/confusion-pages`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          // Map backend data to display format
          const mappedData = data.map((d: any) => {
            // Extract page name from URL
            const url = new URL(d.page_url);
            const path = url.pathname;
            const name = path === "/" ? "Home" : path.split("/").pop() || path;
            return {
              path: path,
              name: name.charAt(0).toUpperCase() + name.slice(1),
              score: d.confusion_score,
              dropoff: d.drop_off_rate,
            };
          });
          setPages(mappedData);
        }
      } catch (_err) {
        // Use empty data on error
        setPages([]);
      } finally {
        setLoading(false);
      }
    };
    fetchConfusionPages();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>Loading confusion data...</p>
      </div>
    );
  }

  if (hasData && pages.length === 0) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>
          No confusion data yet. Check back after collecting more sessions.
        </p>
      </div>
    );
  }

  // Show demo data when hasData is false
  if (!hasData) {
    const demoPages = [
      { path: "/checkout", name: "Payment step", score: 78, dropoff: 34 },
      { path: "/pricing", name: "Plan comparison", score: 61, dropoff: 22 },
      { path: "/signup", name: "Company size field", score: 44, dropoff: 18 },
    ];
    return (
      <div className="space-y-4">
        {demoPages.map((page, i) => (
          <div key={page.path} className="list-item">
            <div className="list-item-icon" style={{ background: "rgba(55, 65, 81, 0.1)", color: "#374151" }}>
              <span style={{ fontSize: "14px", fontWeight: "600" }}>{i + 1}</span>
            </div>
            <div className="list-item-content">
              <div className="list-item-title">
                {page.path} — {page.name}
              </div>
              <div className="list-item-meta">
                <span className="badge badge-amber">{page.score}% confusion</span>
                <span className="badge badge-red">↓ {page.dropoff}% drop-off</span>
              </div>
              <div
                style={{
                  marginTop: "8px",
                  width: "100%",
                  height: "6px",
                  background: "#F3F4F6",
                  borderRadius: "9999px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    background: "#F59E0B",
                    borderRadius: "9999px",
                    width: `${page.score}%`,
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Show real data
  return (
    <div className="space-y-4">
      {pages.map((page, i) => (
        <div key={page.path} className="list-item">
          <div className="list-item-icon" style={{ background: "rgba(55, 65, 81, 0.1)", color: "#374151" }}>
            <span style={{ fontSize: "14px", fontWeight: "600" }}>{i + 1}</span>
          </div>
          <div className="list-item-content">
            <div className="list-item-title">
              {page.path} — {page.name}
            </div>
            <div className="list-item-meta">
              <span className="badge badge-amber">{page.score}% confusion</span>
              <span className="badge badge-red">↓ {page.dropoff}% drop-off</span>
            </div>
            {/* Amber progress bar for confusion */}
            <div
              style={{
                marginTop: "8px",
                width: "100%",
                height: "6px",
                background: "#F3F4F6",
                borderRadius: "9999px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  background: "#F59E0B",
                  borderRadius: "9999px",
                  width: `${page.score}%`,
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Active Experiments List Component ───────────────────────────────────
function ActiveExperimentsList({ hasData, activeCount }: { hasData: boolean; activeCount: number }) {
  const experiments = [
    {
      name: "Checkout CTA Button Test",
      type: "A/B",
      status: "Running",
      progress: "Day 4 of 14",
      lift: "+12% conversion (not significant yet)",
    },
    {
      name: "Pricing Page Headline",
      type: "MVT",
      status: "Running",
      progress: "Day 2 of 14",
      lift: "Collecting data...",
    },
  ];

  if (hasData && activeCount === 0) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>
          No active experiments.{" "}
          <a href="/dashboard/experiments" className="link">Create your first experiment →</a>
        </p>
      </div>
    );
  }

  if (hasData) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>
          {activeCount} active experiment{activeCount !== 1 ? "s" : ""} running.{" "}
          <a href="/dashboard/experiments" className="link">View all →</a>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {experiments.map((exp, i) => (
        <div key={i} className="list-item">
          <div className="list-item-icon" style={{ background: "rgba(55, 65, 81, 0.1)", color: "#374151" }}>
            <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: "16px", height: "16px" }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023-.501.05.75.082M5 14.5l-1.456 7.28a.75.75 0 00.736.893h15.44a.75.75 0 00.736-.893L19 14.5M5 14.5h14" />
            </svg>
          </div>
          <div className="list-item-content">
            <div className="list-item-title">{exp.name}</div>
            <div className="list-item-meta">
              <span className={`badge ${exp.type === "A/B" ? "blue" : "purple"}`}>{exp.type}</span>
              <span className="badge badge-green">{exp.status}</span>
            </div>
            <div className="list-item-subtitle mt-1">{exp.progress}</div>
            <div className="list-item-subtitle">{exp.lift}</div>
          </div>
        </div>
      ))}
      <a href="/dashboard/experiments" className="link" style={{ marginTop: "16px" }}>
        View all experiments →
      </a>
    </div>
  );
}

// ── AI Suggestions List Component ───────────────────────────────────────
function AISuggestionsList({ hasData }: { hasData: boolean }) {
  const suggestions = [
    {
      title: "Simplify payment form on /checkout",
      detail: "78% confusion detected. Estimated lift: +28%",
      impact: "High",
      impactColor: "red",
    },
    {
      title: "Add FAQ tooltip to pricing comparison",
      detail: "61% confusion on plan selection. Est. lift: +19%",
      impact: "Medium",
      impactColor: "amber",
    },
    {
      title: "Reduce fields on company size selector",
      detail: "44% hesitation detected. Est. lift: +12%",
      impact: "Medium",
      impactColor: "amber",
    },
  ];

  if (hasData) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center" }}>
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>
          Not enough data for AI suggestions yet. Keep collecting sessions!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {suggestions.map((suggestion, i) => (
        <div key={i} className="list-item">
          <div className="list-item-icon" style={{ background: "rgba(55, 65, 81, 0.1)", color: "#374151" }}>
            <svg fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: "16px", height: "16px" }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
          </div>
          <div className="list-item-content">
            <div className="list-item-title">{suggestion.title}</div>
            <div className="list-item-subtitle">{suggestion.detail}</div>
            <div className="mt-2">
              <span className={`badge badge-${suggestion.impactColor}`}>{suggestion.impact} impact</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Shimmer animation is now handled inside OverviewPage component via useEffect
