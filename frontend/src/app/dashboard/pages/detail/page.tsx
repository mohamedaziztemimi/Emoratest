"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

interface PageDetailInsight {
  page_url: string;
  total_sessions: number;
  emotion_breakdown: Record<string, number>;
  trend: { frustration_change: number };
  interactive_elements: Array<{
    selector: string;
    element_type: string;
    click_count: number;
    rage_click_count: number;
    dominant_emotion: string;
    emotion_pct: number;
  }>;
  recent_sessions: Array<{
    id: string;
    started_at: string;
    primary_emotion: string | null;
    emotion_confidence: number | null;
  }>;
}

const EMOTION_CONFIG: Record<string, { color: string; label: string }> = {
  frustration: { color: "#EF4444", label: "Frustrated" },
  confusion: { color: "#F59E0B", label: "Confused" },
  anxiety: { color: "#F97316", label: "Anxious" },
  hesitation: { color: "#8B5CF6", label: "Hesitating" },
  satisfaction: { color: "#10B981", label: "Satisfied" },
  delight: { color: "#059669", label: "Delighted" },
  boredom: { color: "#6B7280", label: "Bored" },
  focus: { color: "#3B82F6", label: "Focused" },
};

export default function PageDetailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [data, setData] = useState<PageDetailInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get page URL from query parameter
  const pageUrl = searchParams.get("page") || "";

  const getPagePath = (url: string) => {
    try {
      const u = new URL(url);
      return u.pathname === "/" ? "Home" : u.pathname;
    } catch {
      // If not a full URL, return as-is
      return url === "/" ? "Home" : url;
    }
  };

  const getEmotionInfo = (emotion: string) => {
    return EMOTION_CONFIG[emotion] || { color: "#9CA3AF", label: emotion };
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
        // Use query parameter for the page URL to avoid issues with slashes
        const url = `${apiUrl}/api/v1/pages/insights/detail?page=${encodeURIComponent(pageUrl)}&days=7`;
        console.log("[DEBUG] Frontend fetching page detail:", { pageUrl, apiUrl, requestUrl: url });
        const res = await fetch(url, { credentials: "include" });

        if (res.status === 401) {
          router.push("/login");
          return;
        }

        console.log("[DEBUG] Frontend response status:", res.status);
        if (res.ok) {
          const detail = await res.json();
          console.log("[DEBUG] Frontend received data:", detail);
          setData(detail);
        } else if (res.status === 404) {
          const err = await res.json();
          console.log("[DEBUG] Frontend 404 error:", err);
          setError("No data available for this page");
        } else {
          const err = await res.text();
          console.log("[DEBUG] Frontend error response:", err);
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
          <div className="h-64 bg-gray-200 rounded" />
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

  const emotionEntries = Object.entries(data.emotion_breakdown).sort((a, b) => b[1] - a[1]);
  const trendValue = data.trend.frustration_change;

  return (
    <div className="max-w-6xl mx-auto p-8">
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
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{getPagePath(data.page_url)}</h1>
        <p className="text-sm text-gray-500 mt-1">{data.total_sessions} sessions in the last 7 days</p>
      </div>

      {/* Trend Banner */}
      {trendValue !== 0 && (
        <div
          className={`rounded-lg p-4 mb-6 ${
            trendValue > 0
              ? "bg-red-50 border border-red-200"
              : "bg-green-50 border border-green-200"
          }`}
        >
          <p className="text-sm">
            <span className="font-semibold">
              Frustration {trendValue > 0 ? "↑" : "↓"} {Math.abs(trendValue)}%
            </span>
            <span className="text-gray-600 ml-2">
              vs last week
            </span>
          </p>
        </div>
      )}

      {/* Emotion Breakdown */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Emotion Breakdown</h2>
        <div className="space-y-3">
          {emotionEntries.map(([emotion, pct]) => {
            const info = getEmotionInfo(emotion);
            return (
              <div key={emotion} className="flex items-center gap-3">
                <div className="w-24 text-sm text-gray-600 capitalize">{info.label}</div>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: info.color,
                    }}
                  />
                </div>
                <div className="w-12 text-right text-sm font-medium">{pct}%</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Interactive Elements */}
      {data.interactive_elements.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Interactive Elements</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                    Element
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                    Clicks
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                    Rage Clicks
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                    Dominant Emotion
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.interactive_elements.map((el, idx) => {
                  const emotionInfo = getEmotionInfo(el.dominant_emotion);
                  return (
                    <tr key={idx}>
                      <td className="px-4 py-3 text-sm font-mono text-gray-600">
                        {el.selector}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">{el.click_count}</td>
                      <td
                        className={`px-4 py-3 text-sm ${
                          el.rage_click_count > 0 ? "text-red-600 font-semibold" : "text-gray-600"
                        }`}
                      >
                        {el.rage_click_count}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: emotionInfo.color }}
                          />
                          <span className="text-sm capitalize">{emotionInfo.label}</span>
                          <span className="text-xs text-gray-500">({el.emotion_pct}%)</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
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
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    {emotionInfo && (
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: emotionInfo.color }}
                      />
                    )}
                    <span className="text-sm text-gray-600">
                      {new Date(session.started_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    {emotionInfo && (
                      <span className="text-sm capitalize text-gray-600">
                        {emotionInfo.label}
                      </span>
                    )}
                    {session.emotion_confidence && (
                      <span className="text-xs text-gray-500">
                        {Math.round(session.emotion_confidence * 100)}% conf
                      </span>
                    )}
                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
