"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@/lib/hooks";
import {
  fetchWhyAnalysisSummary,
  fetchEmotionConversion,
  fetchDropOffReasons,
  fetchEmotionTrend,
  WhyAnalysisSummary,
  EmotionConversionResponse,
  DropOffReasonsResponse,
  EmotionTrendResponse,
} from "@/lib/api";

const EMOTION_COLORS: Record<string, string> = {
  confusion: "#F59E0B",
  frustration: "#EF4444",
  delight: "#10B981",
  focus: "#3B82F6",
  anxiety: "#F97316",
  boredom: "#6B7280",
  hesitation: "#8B5CF6",
  satisfaction: "#059669",
};

function getEmotionColor(emotion: string): string {
  return EMOTION_COLORS[emotion.toLowerCase()] || "#6B7280";
}

function formatPct(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

/* ── Low data banner ────────────────────────────────────── */
function LowDataBanner({ sessions, withEmotion }: { sessions: number; withEmotion: number }) {
  if (withEmotion >= 20) return null;
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 flex items-start gap-3">
      <span className="text-amber-500 text-lg leading-none mt-0.5">⚠</span>
      <div>
        <p className="text-sm font-medium text-amber-800">Limited emotion data</p>
        <p className="text-xs text-amber-600 mt-0.5">
          Only {withEmotion} of {sessions} sessions have emotion predictions.
          Insights become reliable with 20+ emotion-tagged sessions.
        </p>
      </div>
    </div>
  );
}

/* ── Stat card ──────────────────────────────────────────── */
function StatCard({
  label,
  value,
  sub,
  accent,
  emotion,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
  emotion?: string | null;
}) {
  const color = emotion ? getEmotionColor(emotion) : undefined;
  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] p-5 hover:shadow-sm transition-shadow">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">{label}</p>
      <div className="flex items-center gap-2">
        {color && <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />}
        <p className={`text-2xl font-bold ${accent || "text-gray-900"}`} style={color ? { color } : undefined}>
          {value}
        </p>
      </div>
      {sub && <p className="text-xs text-gray-400 mt-1.5">{sub}</p>}
    </div>
  );
}

/* ── Friction comparison ───────────────────────────────── */
function FrictionComparison({ summary }: { summary: WhyAnalysisSummary }) {
  const abandoned = summary.avg_friction_abandoned;
  const converted = summary.avg_friction_converted;
  if (abandoned == null || converted == null) return null;

  const diff = Math.abs(abandoned - converted) * 100;
  const higher = abandoned > converted ? "abandoned" : "converted";

  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] p-5">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">Friction Comparison</p>
      <div className="flex items-end gap-8">
        <div>
          <p className="text-xs text-gray-500 mb-1">Abandoned Users</p>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-red-500">{(abandoned * 100).toFixed(0)}%</span>
            <span className="text-xs text-gray-400">friction</span>
          </div>
        </div>
        <div className="pb-1 text-gray-300 text-lg">vs</div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Converted Users</p>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-green-500">{(converted * 100).toFixed(0)}%</span>
            <span className="text-xs text-gray-400">friction</span>
          </div>
        </div>
      </div>
      {diff > 1 && (
        <p className="text-sm text-gray-500 mt-3 pt-3 border-t border-gray-100">
          {higher === "abandoned"
            ? `Users who abandon experience ${diff.toFixed(0)}% more friction — reducing friction could improve conversions.`
            : "Friction levels are similar between both groups."}
        </p>
      )}
      {diff <= 1 && (
        <p className="text-sm text-gray-500 mt-3 pt-3 border-t border-gray-100">
          Friction levels are similar — drop-offs may be driven by emotional factors rather than UX friction.
        </p>
      )}
    </div>
  );
}

/* ── Emotion Trend Chart ──────────────────────────────── */
function EmotionTrendChart({ data }: { data: EmotionTrendResponse }) {
  if (data.days.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Emotion Trends</p>
        <p className="text-gray-400 text-sm py-8 text-center">No trend data yet.</p>
      </div>
    );
  }

  const maxTotal = Math.max(...data.days.map((d) => d.total), 1);
  const daysToShow = data.days.slice(-30); // Show last 30 days max

  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
      <div className="mb-5">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Emotion Trends</p>
        <p className="text-sm text-gray-500">Daily emotion breakdown over time</p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-4">
        {data.emotions_seen.map((emotion) => (
          <div key={emotion} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: getEmotionColor(emotion) }} />
            <span className="text-xs capitalize text-gray-600">{emotion}</span>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="flex gap-0.5 items-end h-32">
        {daysToShow.map((day) => {
          if (day.total === 0) {
            return (
              <div key={day.date} className="flex-1 bg-gray-50 rounded-sm" style={{ minHeight: "4px" }} />
            );
          }

          const parts: Array<{ emotion: string; count: number; color: string }> = [];
          for (const [emotion, count] of Object.entries(day.emotions)) {
            parts.push({ emotion, count: count as number, color: getEmotionColor(emotion) });
          }
          parts.sort((a, b) => b.count - a.count);

          return (
            <div
              key={day.date}
              className="flex-1 flex flex-col justify-end rounded-sm overflow-hidden relative group"
              style={{ height: `${Math.max((day.total / maxTotal) * 100, 4)}%` }}
            >
              {parts.map((part) => (
                <div
                  key={part.emotion}
                  className="w-full hover:opacity-80 transition-opacity"
                  style={{
                    backgroundColor: part.color,
                    height: `${(part.count / day.total) * 100}%`,
                    minHeight: "2px",
                  }}
                  title={`${part.emotion}: ${part.count}`}
                />
              ))}
              <div className="absolute bottom-0 left-0 right-0 bg-gray-900/80 text-white text-[9px] py-0.5 px-1 text-center opacity-0 group-hover:opacity-100 transition-opacity truncate">
                {new Date(day.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
              </div>
            </div>
          );
        })}
      </div>

      {/* X-axis labels */}
      <div className="flex justify-between mt-2 text-[10px] text-gray-400">
        <span>{new Date(daysToShow[0]?.date || "").toLocaleDateString("en-US", { month: "short", day: "numeric" })}</span>
        <span>{new Date(daysToShow[daysToShow.length - 1]?.date || "").toLocaleDateString("en-US", { month: "short", day: "numeric" })}</span>
      </div>
    </div>
  );
}

/* ── Emotion → Conversion chart ────────────────────────── */
function EmotionConversionChart({ data }: { data: EmotionConversionResponse }) {
  if (data.items.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Emotion → Conversion</p>
        <p className="text-gray-400 text-sm py-8 text-center">No emotion data yet. Sessions need emotion predictions to appear here.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
      <div className="mb-5">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Emotion → Conversion</p>
        <p className="text-sm text-gray-500">How each detected emotion correlates with conversion rate</p>
      </div>
      <div className="space-y-3">
        {data.items.map((item) => {
          const color = getEmotionColor(item.emotion);
          const convPct = item.conversion_rate * 100;
          return (
            <div key={item.emotion} className="group">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-sm font-medium text-gray-700 capitalize">{item.emotion}</span>
                  {item.total_sessions < 5 && (
                    <span className="text-[10px] text-gray-400 bg-gray-100 rounded px-1.5 py-0.5">low sample</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400">{item.total_sessions} sessions</span>
                  <span className="text-sm font-semibold text-gray-800">{convPct.toFixed(1)}%</span>
                </div>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.max(convPct, 2)}%`, backgroundColor: color }}
                />
              </div>
              <div className="flex justify-between mt-1 text-[11px] text-gray-400">
                <span>{item.converted} converted · {item.abandoned} abandoned</span>
                {item.avg_friction != null && <span>Friction: {(item.avg_friction * 100).toFixed(0)}%</span>}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-gray-400">Overall conversion (emotion-tagged sessions only)</span>
        <span className="text-sm font-bold text-gray-900">{formatPct(data.overall_conversion_rate)}</span>
      </div>
    </div>
  );
}

/* ── Drop-off reasons table ────────────────────────────── */
function DropOffTable({ data }: { data: DropOffReasonsResponse }) {
  if (data.reasons.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Top Drop-Off Patterns</p>
        <p className="text-gray-400 text-sm py-8 text-center">No drop-off patterns detected yet. Need more abandoned sessions with emotion data.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
      <div className="mb-5">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Top Drop-Off Patterns</p>
        <p className="text-sm text-gray-500">Page + emotion combinations causing the most abandonment</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2.5 pr-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Page</th>
              <th className="text-left py-2.5 px-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Emotion</th>
              <th className="text-right py-2.5 px-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Sessions</th>
              <th className="text-right py-2.5 px-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Drop-off %</th>
              <th className="text-right py-2.5 pl-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Friction</th>
            </tr>
          </thead>
          <tbody>
            {data.reasons.map((r, i) => {
              const color = getEmotionColor(r.emotion);
              let displayUrl = r.page_url;
              try { displayUrl = new URL(r.page_url).pathname; } catch { /* keep */ }
              return (
                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                  <td className="py-3 pr-4 font-mono text-xs text-gray-600 max-w-[280px] truncate" title={r.page_url}>
                    {displayUrl}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium capitalize" style={{ color }}>
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                      {r.emotion}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-gray-700 font-medium">{r.sessions}</td>
                  <td className="py-3 px-4 text-right text-gray-700">{formatPct(r.drop_off_rate)}</td>
                  <td className="py-3 pl-4 text-right text-gray-700">
                    {r.avg_friction != null ? `${(r.avg_friction * 100).toFixed(0)}%` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Insights ───────────────────────────────────────────── */
type Insight = {
  emoji: string;
  text: string;
  priority: "High" | "Medium" | "Low";
};

function Insights({
  summary,
  emotionConversion,
  dropOff,
}: {
  summary: WhyAnalysisSummary | null;
  emotionConversion: EmotionConversionResponse | null;
  dropOff: DropOffReasonsResponse | null;
}) {
  const insights: Insight[] = [];

  // Low sample size
  if (summary && summary.sessions_with_emotion < 20) {
    insights.push({
      emoji: "⚠",
      text: "Collect more emotion data for reliable insights. Current sample size is too small for confident recommendations.",
      priority: "Medium",
    });
  }

  // High converting emotions
  if (emotionConversion) {
    for (const item of emotionConversion.items) {
      if (item.total_sessions >= 3 && item.conversion_rate > 0.6) {
        insights.push({
          emoji: "💡",
          text: `Users feeling ${item.emotion} convert well (${(item.conversion_rate * 100).toFixed(0)}%). Consider amplifying triggers for this emotional state.`,
          priority: "High",
        });
      }
    }
  }

  // Low converting emotions
  if (emotionConversion) {
    for (const item of emotionConversion.items) {
      if (item.total_sessions >= 3 && item.conversion_rate < 0.2) {
        insights.push({
          emoji: "🔍",
          text: `${item.emotion.charAt(0).toUpperCase() + item.emotion.slice(1)} correlates with low conversion (${(item.conversion_rate * 100).toFixed(0)}%). Investigate UX friction on pages where this emotion dominates.`,
          priority: "High",
        });
      }
    }
  }

  // Friction comparison
  if (summary && summary.avg_friction_abandoned !== null && summary.avg_friction_converted !== null) {
    const diff = (summary.avg_friction_abandoned - summary.avg_friction_converted) * 100;
    if (diff > 5) {
      insights.push({
        emoji: "⚡",
        text: `Abandoned users experience ${diff.toFixed(0)}% more friction. Reducing page friction could directly improve conversions.`,
        priority: "High",
      });
    } else if (diff <= 1) {
      insights.push({
        emoji: "💭",
        text: "Friction is similar for both groups — drop-offs may be emotional, not UX-related. Focus on messaging and trust signals.",
        priority: "Medium",
      });
    }
  }

  // Top drop-off pattern
  if (dropOff && dropOff.reasons.length === 1) {
    const top = dropOff.reasons[0];
    let displayUrl = top.page_url;
    try { displayUrl = new URL(top.page_url).pathname; } catch { /* keep */ }
    insights.push({
      emoji: "🎯",
      text: `Most abandonment happens on ${displayUrl} with ${top.emotion}. This is your #1 optimization target.`,
      priority: "High",
    });
  }

  if (insights.length === 0) {
    return null;
  }

  const priorityColors: Record<string, string> = {
    High: "bg-red-100 text-red-700",
    Medium: "bg-amber-100 text-amber-700",
    Low: "bg-blue-100 text-blue-700",
  };

  return (
    <div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
      <div className="mb-5">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Insights</p>
        <p className="text-sm text-gray-500">Actionable recommendations based on your data</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, i) => (
          <div key={i} className="bg-gray-50 rounded-lg p-4 flex gap-3">
            <span className="text-xl flex-shrink-0">{insight.emoji}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-700">{insight.text}</p>
              <span className={`inline-block mt-2 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityColors[insight.priority]}`}>
                {insight.priority} Priority
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main page ─────────────────────────────────────────── */
export default function WhyAnalysisPage() {
  const [range, setRange] = useState<string>("30d");

  const dateRange = useMemo(() => {
    if (range === "all") return { from: undefined, to: undefined };
    const now = new Date();
    const to = now.toISOString();
    const days = range === "7d" ? 7 : range === "30d" ? 30 : 90;
    const from = new Date(now.getTime() - days * 86400000).toISOString();
    return { from, to };
  }, [range]);

  const { data: summary, loading: loadingSummary } = useQuery<WhyAnalysisSummary>(
    () => fetchWhyAnalysisSummary(dateRange.from, dateRange.to),
    [range],
    `why-summary-${range}`
  );
  const { data: emotionConversion, loading: loadingEC } = useQuery<EmotionConversionResponse>(
    () => fetchEmotionConversion(dateRange.from, dateRange.to),
    [range],
    `why-emotion-conversion-${range}`
  );
  const { data: dropOff, loading: loadingDO } = useQuery<DropOffReasonsResponse>(
    () => fetchDropOffReasons(dateRange.from, dateRange.to),
    [range],
    `why-drop-off-${range}`
  );
  const { data: emotionTrend, loading: loadingTrend } = useQuery<EmotionTrendResponse>(
    () => fetchEmotionTrend(dateRange.from, dateRange.to),
    [range],
    `why-trend-${range}`
  );

  const isLoading = loadingSummary || loadingEC || loadingDO || loadingTrend;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Why-Analysis</h1>
          <p className="text-sm text-gray-500 mt-1">
            Connect user emotions to conversion outcomes — understand <em>why</em> users drop off
          </p>
        </div>
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {[
            { key: "7d", label: "7 days" },
            { key: "30d", label: "30 days" },
            { key: "90d", label: "90 days" },
            { key: "all", label: "All time" },
          ].map((opt) => (
            <button
              key={opt.key}
              onClick={() => setRange(opt.key)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                range === opt.key
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#007BFF]" />
        </div>
      ) : (
        <>
          {/* Low data warning */}
          {summary && (
            <LowDataBanner sessions={summary.total_sessions} withEmotion={summary.sessions_with_emotion} />
          )}

          {/* Summary Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Total Sessions"
              value={summary?.total_sessions?.toString() || "0"}
              sub={`${summary?.sessions_with_emotion || 0} with emotion data`}
            />
            <StatCard
              label="Conversion Rate"
              value={formatPct(summary?.overall_conversion_rate)}
              accent={
                summary?.overall_conversion_rate != null
                  ? summary.overall_conversion_rate >= 0.1
                    ? "text-green-600"
                    : "text-gray-900"
                  : undefined
              }
            />
            <StatCard
              label="Best Converting Emotion"
              value={summary?.top_converting_emotion ? summary.top_converting_emotion.charAt(0).toUpperCase() + summary.top_converting_emotion.slice(1) : "—"}
              sub={summary?.top_converting_emotion_rate != null ? `${(summary.top_converting_emotion_rate * 100).toFixed(0)}% conversion rate` : undefined}
              emotion={summary?.top_converting_emotion}
            />
            <StatCard
              label="Worst Converting Emotion"
              value={summary?.top_drop_off_emotion ? summary.top_drop_off_emotion.charAt(0).toUpperCase() + summary.top_drop_off_emotion.slice(1) : "—"}
              sub={summary?.top_drop_off_emotion_rate != null ? `${(summary.top_drop_off_emotion_rate * 100).toFixed(0)}% conversion rate` : undefined}
              emotion={summary?.top_drop_off_emotion}
            />
          </div>

          {/* Friction Comparison */}
          {summary && <FrictionComparison summary={summary} />}

          {/* Emotion Trend Chart */}
          {emotionTrend && <EmotionTrendChart data={emotionTrend} />}

          {/* Emotion → Conversion Chart */}
          {emotionConversion && <EmotionConversionChart data={emotionConversion} />}

          {/* Drop-off Reasons */}
          {dropOff && <DropOffTable data={dropOff} />}

          {/* Insights */}
          <Insights summary={summary} emotionConversion={emotionConversion} dropOff={dropOff} />
        </>
      )}
    </div>
  );
}
