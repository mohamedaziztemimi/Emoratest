"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

interface BehavioralSignals {
  avg_hesitation_score: number | null;
  avg_friction_score: number | null;
  rage_click_sessions: number;
  avg_scroll_retreats: number | null;
  avg_exit_intents: number | null;
}

interface DailyEmotionCount {
  date: string;
  emotion: string;
  count: number;
}

interface PageIssue {
  type: string;
  severity: string;
  title: string;
  description: string;
  affected_percentage: number | null;
  recommendation: string;
}

interface PageDetailInsight {
  page_url: string;
  total_sessions: number;
  frustration_rate: number;
  bounce_rate: number;
  rage_click_count: number;
  avg_duration: number;
  emotion_breakdown: Record<string, number>;
  emotion_counts: Record<string, number>;
  behavioral_signals: BehavioralSignals;
  daily_emotions: DailyEmotionCount[];
  issues: PageIssue[];
  recent_sessions: Array<{
    id: string;
    started_at: string;
    primary_emotion: string | null;
    emotion_confidence: number | null;
    outcome: string;
    friction_score: number | null;
    duration_seconds: number | null;
  }>;
}

const EMOTION_CONFIG: Record<string, { color: string; label: string }> = {
  frustration: { color: "#EF4444", label: "Frustration" },
  frustrated: { color: "#EF4444", label: "Frustrated" },
  anxiety: { color: "#F97316", label: "Anxiety" },
  confusion: { color: "#F59E0B", label: "Confusion" },
  confused: { color: "#F59E0B", label: "Confused" },
  focus: { color: "#3B82F6", label: "Focus" },
  satisfaction: { color: "#059669", label: "Satisfaction" },
  delight: { color: "#10B981", label: "Delight" },
  engaged: { color: "#10B981", label: "Engaged" },
  boredom: { color: "#6B7280", label: "Boredom" },
  disengaged: { color: "#6B7280", label: "Disengaged" },
  hesitation: { color: "#8B5CF6", label: "Hesitation" },
  insufficient_data: { color: "#D1D5DB", label: "N/A" },
  unknown: { color: "#9CA3AF", label: "Unknown" },
  none: { color: "#D1D5DB", label: "None" },
};

export default function PageDetailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [data, setData] = useState<PageDetailInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pageUrl = searchParams.get("page") || "";

  const getPagePath = (url: string) => {
    try {
      const u = new URL(url);
      return u.pathname === "/" ? "Home" : u.pathname;
    } catch {
      return url === "/" ? "Home" : url;
    }
  };

  const getEmotionInfo = (emotion: string) => {
    return EMOTION_CONFIG[emotion] || { color: "#9CA3AF", label: emotion };
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "bg-red-100 text-red-700 border-red-200";
      case "warning": return "bg-amber-100 text-amber-700 border-amber-200";
      case "info": return "bg-blue-100 text-blue-700 border-blue-200";
      default: return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const getOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case "purchase":
      case "checkout_completed":
        return "bg-green-100 text-green-700";
      case "abandon":
        return "bg-red-100 text-red-700";
      case "unknown":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-blue-100 text-blue-700";
    }
  };

  const getOutcomeLabel = (outcome: string) => {
    switch (outcome) {
      case "purchase": return "Converted";
      case "checkout_completed": return "Completed";
      case "abandon": return "Abandoned";
      case "signup": return "Signed Up";
      case "demo_booked": return "Demo Booked";
      case "lead_generated": return "Lead Generated";
      case "trial_started": return "Trial Started";
      default: return outcome;
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return "N/A";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  useEffect(() => {
    if (!pageUrl) {
      setError("No page specified");
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const url = `${apiUrl}/api/v1/pages/insights/detail?page=${encodeURIComponent(pageUrl)}&days=7`;
        const res = await fetch(url, { credentials: "include" });

        if (res.status === 401) {
          router.push("/login");
          return;
        }

        if (res.ok) {
          const detail = await res.json();
          setData(detail);
        } else if (res.status === 404) {
          setError("No data available for this page");
        } else {
          setError("Failed to load page details");
        }
      } catch (err) {
        console.error("Failed to fetch page detail:", err);
        setError("Failed to load page details");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [pageUrl, router]);

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-64" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8">
        <button
          onClick={() => router.push("/dashboard/pages")}
          className="text-[#007BFF] hover:underline mb-4"
        >
          ← Back to Page insights
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
          <p className="text-red-700">{error || "No data available"}</p>
        </div>
      </div>
    );
  }

  const emotionEntries = Object.entries(data.emotion_breakdown)
    .sort((a, b) => b[1] - a[1]);

  // Group daily emotions by date for the chart
  const dailyData: Record<string, Record<string, number>> = {};
  data.daily_emotions.forEach(({ date, emotion, count }) => {
    if (!dailyData[date]) dailyData[date] = {};
    dailyData[date][emotion] = (dailyData[date][emotion] || 0) + count;
  });
  const sortedDates = Object.keys(dailyData).sort();
  const maxCount = Math.max(
    ...Object.values(dailyData).flatMap(day => Object.values(day)),
    1
  );

  return (
    <div className="max-w-7xl mx-auto p-8">
      {/* Breadcrumb */}
      <div className="mb-6">
        <button
          onClick={() => router.push("/dashboard/pages")}
          className="text-[#007BFF] hover:underline text-sm"
        >
          Page insights
        </button>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900 font-medium">{getPagePath(data.page_url)}</span>
      </div>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">{getPagePath(data.page_url)}</h1>
        <p className="text-sm text-gray-500 mt-1">{data.total_sessions} sessions in the last 7 days</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Total Sessions</p>
          <p className="text-2xl font-bold text-gray-900">{data.total_sessions}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Frustration Rate</p>
          <p className={`text-2xl font-bold ${
            data.frustration_rate >= 20 ? "text-red-600" :
            data.frustration_rate >= 10 ? "text-amber-600" :
            "text-green-600"
          }`}>
            {data.frustration_rate}%
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Avg Duration</p>
          <p className="text-2xl font-bold text-gray-900">{formatDuration(data.avg_duration)}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Bounce Rate</p>
          <p className={`text-2xl font-bold ${
            data.bounce_rate >= 50 ? "text-red-600" :
            data.bounce_rate >= 30 ? "text-amber-600" :
            "text-gray-900"
          }`}>
            {data.bounce_rate}%
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase mb-1">Rage Clicks</p>
          <p className={`text-2xl font-bold ${
            data.rage_click_count > 0 ? "text-red-600" : "text-gray-400"
          }`}>
            {data.rage_click_count}
          </p>
        </div>
      </div>

      {/* Top Issues */}
      {data.issues.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Detected Issues</h2>
          <div className="space-y-4">
            {data.issues.map((issue, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{issue.title}</h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(issue.severity)}`}>
                    {issue.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">{issue.description}</p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-[#007BFF] font-medium">💡 {issue.recommendation}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Emotion Breakdown */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Emotion Breakdown</h2>
        <div className="space-y-3">
          {emotionEntries.map(([emotion, pct]) => {
            const info = getEmotionInfo(emotion);
            const count = data.emotion_counts[emotion] || 0;
            return (
              <div key={emotion} className="flex items-center gap-3">
                <div className="w-28 text-sm text-gray-600 capitalize">{info.label}</div>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: info.color,
                    }}
                  />
                </div>
                <div className="w-20 text-right text-sm">
                  <span className="font-medium">{pct}%</span>
                  <span className="text-gray-500 text-xs ml-1">({count})</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Behavioral Signals */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Behavioral Signals</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">Avg Hesitation</p>
            <p className="text-lg font-semibold text-gray-900">
              {data.behavioral_signals.avg_hesitation_score
                ? `${Math.round(data.behavioral_signals.avg_hesitation_score * 100)}%`
                : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Avg Friction</p>
            <p className="text-lg font-semibold text-gray-900">
              {data.behavioral_signals.avg_friction_score
                ? `${Math.round(data.behavioral_signals.avg_friction_score * 100)}%`
                : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Rage Click Sessions</p>
            <p className="text-lg font-semibold text-red-600">
              {data.behavioral_signals.rage_click_sessions}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Avg Scroll Retreats</p>
            <p className="text-lg font-semibold text-gray-900">
              {data.behavioral_signals.avg_scroll_retreats
                ? data.behavioral_signals.avg_scroll_retreats.toFixed(1)
                : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Avg Exit Intents</p>
            <p className="text-lg font-semibold text-gray-900">
              {data.behavioral_signals.avg_exit_intents
                ? data.behavioral_signals.avg_exit_intents.toFixed(1)
                : "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      {sortedDates.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">7-Day Trend</h2>
          <div className="space-y-2">
            {sortedDates.map((date) => {
              const dayData = dailyData[date];
              const dateObj = new Date(date);
              const label = dateObj.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
              return (
                <div key={date} className="flex items-center gap-2">
                  <div className="w-28 text-xs text-gray-500">{label}</div>
                  <div className="flex-1 flex gap-0.5 h-6">
                    {Object.entries(dayData)
                      .sort((a, b) => b[1] - a[1])
                      .map(([emotion, count]) => {
                        const info = getEmotionInfo(emotion);
                        const width = (count / maxCount) * 100;
                        return (
                          <div
                            key={emotion}
                            className="h-full rounded-sm first:rounded-l-lg last:rounded-r-lg"
                            style={{
                              width: `${width}%`,
                              backgroundColor: info.color,
                              minWidth: "2px",
                            }}
                            title={`${info.label}: ${count}`}
                          />
                        );
                      })}
                  </div>
                  <div className="w-12 text-xs text-gray-500 text-right">
                    {Object.values(dayData).reduce((a, b) => a + b, 0)}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
            <span className="text-xs text-gray-500">Emotions:</span>
            {Object.entries(EMOTION_CONFIG)
              .filter(([key]) => data.emotion_breakdown[key])
              .map(([key, { color, label }]) => (
                <div key={key} className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-xs text-gray-600">{label}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Recent Sessions */}
      {data.recent_sessions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Sessions</h2>
          <div className="space-y-2">
            {data.recent_sessions.map((session) => {
              const emotionInfo = session.primary_emotion
                ? getEmotionInfo(session.primary_emotion)
                : null;
              return (
                <div
                  key={session.id}
                  onClick={() => router.push(`/dashboard/sessions/${session.id}`)}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-200 transition-all"
                >
                  <div className="flex items-center gap-3">
                    {emotionInfo && (
                      <div
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: emotionInfo.color }}
                      />
                    )}
                    <span className="text-sm text-gray-600">
                      {new Date(session.started_at).toLocaleString()}
                    </span>
                    {session.duration_seconds !== null && (
                      <span className="text-xs text-gray-500">
                        {formatDuration(session.duration_seconds)}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {session.friction_score !== null && session.friction_score > 0.5 && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700">
                        High friction
                      </span>
                    )}
                    <span className={`px-2 py-0.5 text-xs rounded-full ${getOutcomeBadge(session.outcome)}`}>
                      {getOutcomeLabel(session.outcome)}
                    </span>
                    {emotionInfo && (
                      <span className="text-sm capitalize text-gray-600">
                        {emotionInfo.label}
                      </span>
                    )}
                    <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
