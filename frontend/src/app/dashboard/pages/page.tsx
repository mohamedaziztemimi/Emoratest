"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface PageInsightItem {
  page_url: string;
  session_count: number;
  dominant_emotion: string;
  dominant_emotion_pct: number;
  rage_clicks: number;
  avg_duration_seconds: number;
  top_signals: string[];
}

const EMOTION_CONFIG: Record<string, { color: string; label: string }> = {
  frustrated: { color: "#EF4444", label: "Frustrated" },
  confused: { color: "#F59E0B", label: "Confused" },
  engaged: { color: "#10B981", label: "Engaged" },
  disengaged: { color: "#6B7280", label: "Disengaged" },
  insufficient_data: { color: "#D1D5DB", label: "N/A" },
  unknown: { color: "#9CA3AF", label: "Unknown" },
  none: { color: "#D1D5DB", label: "None" },
};

export default function PageInsightsPage() {
  const router = useRouter();
  const [pages, setPages] = useState<PageInsightItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/v1/pages/insights?days=7&limit=50`, {
          credentials: "include",
        });

        if (res.status === 401) {
          router.push("/login");
          return;
        }

        if (res.ok) {
          const data = await res.json();
          setPages(data.pages || []);
        } else {
          setError("Failed to load page insights");
        }
      } catch (err) {
        console.error("Failed to fetch page insights:", err);
        setError("Failed to load page insights");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getPagePath = (url: string) => {
    try {
      const u = new URL(url);
      return u.pathname === "/" ? "Home" : u.pathname;
    } catch {
      return url;
    }
  };

  const getEmotionInfo = (emotion: string) => {
    return EMOTION_CONFIG[emotion] || EMOTION_CONFIG.unknown;
  };

  const handlePageClick = (pageUrl: string) => {
    // Use query parameter to avoid issues with slashes in URLs
    router.push(`/dashboard/pages/detail?page=${encodeURIComponent(pageUrl)}`);
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Page insights</h1>
        <p className="text-sm text-gray-500 mt-1">
          See which pages cause the most emotional friction
        </p>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {pages.length === 0 && !error && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-200 p-8 text-center">
          <span className="text-4xl mb-4 block">📊</span>
          <h2 className="text-xl font-bold text-gray-900 mb-2">No page data yet</h2>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Install the EmoraTest SDK to start tracking user emotions on your website.
          </p>
          <a
            href="/dashboard/settings"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#007BFF] text-white rounded-lg font-semibold hover:bg-[#0056b3] transition-colors"
          >
            View Setup Guide →
          </a>
        </div>
      )}

      {/* Pages List */}
      {pages.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                    Page
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                    Sessions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                    Dominant Emotion
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                    Avg Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                    Signals
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {pages.map((page) => {
                  const emotionInfo = getEmotionInfo(page.dominant_emotion);
                  const isNegative = ["frustrated", "confused", "disengaged"].includes(
                    page.dominant_emotion
                  );

                  return (
                    <tr
                      key={page.page_url}
                      onClick={() => handlePageClick(page.page_url)}
                      className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                        isNegative ? "bg-red-50/30" : ""
                      }`}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: emotionInfo.color }}
                          />
                          <div>
                            <p className="font-medium text-gray-900">{getPagePath(page.page_url)}</p>
                            {page.rage_clicks > 0 && (
                              <p className="text-xs text-red-600">{page.rage_clicks} rage clicks</p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {page.session_count}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: emotionInfo.color }}
                          />
                          <span className="text-sm capitalize">{emotionInfo.label}</span>
                          <span className="text-sm font-semibold">{page.dominant_emotion_pct}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {formatDuration(page.avg_duration_seconds)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {page.top_signals.slice(0, 2).map((signal) => (
                            <span
                              key={signal}
                              className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600"
                            >
                              {signal}
                            </span>
                          ))}
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
    </div>
  );
}
