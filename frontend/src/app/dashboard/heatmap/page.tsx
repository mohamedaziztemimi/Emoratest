"use client";

import { useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@/lib/hooks";
import { fetchElementEmotions, fetchHeatmapData, type ElementEmotionItem } from "@/lib/api";
import { formatDate } from "@/lib/format";
import HeatmapCanvas, { type HeatmapType } from "./HeatmapCanvas";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";

const EMOTION_COLORS: Record<string, string> = {
  confusion: "#F59E0B",
  frustration: "#EF4444",
  delight: "#10B981",
  anxiety: "#F97316",
  focus: "#3B82F6",
  boredom: "#6B7280",
  hesitation: "#8B5CF6",
  satisfaction: "#059669",
};

const VIEW_TABS = [
  { value: "elements", label: "Element Analysis" },
  { value: "visual", label: "Visual Heatmap" },
];

export default function HeatmapPage() {
  const router = useRouter();
  const [view, setView] = useState("elements");
  const [heatmapType, setHeatmapType] = useState<HeatmapType>("click");
  const [sortBy, setSortBy] = useState<"events" | "clicks" | "frustration">("events");

  // Fetch element emotions
  const elementFetcher = useCallback(() => fetchElementEmotions(), []);
  const elements = useQuery(elementFetcher, []);

  // Fetch visual heatmap data
  const heatmapFetcher = useCallback(() => fetchHeatmapData(heatmapType === "move" ? "move" : heatmapType), [heatmapType]);
  const heatmap = useQuery(heatmapFetcher, [heatmapType]);

  // Sort elements
  const sortedElements = useMemo(() => {
    if (!elements.data) return [];
    const items = [...elements.data.elements];
    if (sortBy === "clicks") items.sort((a, b) => b.click_count - a.click_count);
    else if (sortBy === "frustration") items.sort((a, b) => b.rage_click_rate - a.rage_click_rate);
    else items.sort((a, b) => b.event_count - a.event_count);
    return items;
  }, [elements.data, sortBy]);

  // Emotion summary across all elements
  const emotionSummary = useMemo(() => {
    if (!elements.data) return [];
    const counts: Record<string, number> = {};
    elements.data.elements.forEach((el) => {
      if (el.dominant_emotion) {
        counts[el.dominant_emotion] = (counts[el.dominant_emotion] || 0) + el.session_count;
      }
    });
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    if (total === 0) return [];
    return Object.entries(counts)
      .map(([emotion, count]) => ({ emotion, count, pct: (count / total) * 100, color: EMOTION_COLORS[emotion] || "#6B7280" }))
      .sort((a, b) => b.count - a.count);
  }, [elements.data]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Emotion Heatmap</h1>
          <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">
            See which page elements trigger emotions — from delight to frustration
          </p>
        </div>
        {elements.data && (
          <Badge variant="outline">{elements.data.total_elements} elements tracked</Badge>
        )}
      </div>

      {/* View Toggle */}
      <div className="flex gap-1 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-1 w-fit">
        {VIEW_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setView(tab.value)}
            className={`rounded-lg px-4 py-1.5 text-[12px] font-medium transition-all ${
              view === tab.value
                ? "bg-[hsl(var(--primary))] text-white shadow-sm"
                : "text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {view === "elements" ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
          {/* Element Table */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Page Elements</h2>
                  <div className="flex gap-1 rounded-lg border border-[hsl(var(--border))] p-0.5">
                    {([
                      { value: "events", label: "Events" },
                      { value: "clicks", label: "Clicks" },
                      { value: "frustration", label: "Frustration" },
                    ] as const).map((s) => (
                      <button
                        key={s.value}
                        onClick={() => setSortBy(s.value)}
                        className={`rounded-md px-3 py-1 text-[11px] font-medium transition-all ${
                          sortBy === s.value
                            ? "bg-[hsl(var(--primary)/0.1)] text-[hsl(var(--primary))]"
                            : "text-[hsl(var(--muted-foreground))]"
                        }`}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardBody className="p-0">
                {elements.loading ? (
                  <div className="p-6"><Spinner /></div>
                ) : elements.error ? (
                  <div className="p-6"><ErrorBox message={elements.error} onRetry={elements.refetch} /></div>
                ) : sortedElements.length === 0 ? (
                  <div className="p-6"><EmptyState title="No element data" description="Collect more session data to see element interactions." /></div>
                ) : (
                  <div className="divide-y divide-[hsl(var(--border)/0.5)]">
                    {sortedElements.map((el, i) => (
                      <ElementRow key={el.element_id} element={el} rank={i + 1} />
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardBody>
                <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))] mb-4">Emotion Overview</h2>
                {emotionSummary.length > 0 ? (
                  <div className="space-y-3">
                    {emotionSummary.map((item) => (
                      <div key={item.emotion}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                            <span className="text-[12px] font-medium capitalize text-[hsl(var(--foreground))]">{item.emotion}</span>
                          </div>
                          <span className="text-[12px] font-semibold text-[hsl(var(--muted-foreground))]">{item.pct.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-[hsl(var(--secondary))]">
                          <div className="h-full rounded-full" style={{ width: `${item.pct}%`, backgroundColor: item.color }} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[12px] text-[hsl(var(--muted-foreground))]">No emotion data yet.</p>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))] mb-3">Quick Stats</h2>
                <div className="space-y-3 text-[13px]">
                  <div className="flex justify-between">
                    <span className="text-[hsl(var(--muted-foreground))]">Total Elements</span>
                    <span className="font-semibold text-[hsl(var(--foreground))]">{elements.data?.total_elements || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[hsl(var(--muted-foreground))]">With Rage Clicks</span>
                    <span className="font-semibold text-red-600">
                      {sortedElements.filter((e) => e.rage_click_count > 0).length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[hsl(var(--muted-foreground))]">High Frustration</span>
                    <span className="font-semibold text-red-600">
                      {sortedElements.filter((e) => e.dominant_emotion === "frustration").length}
                    </span>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      ) : (
        /* Visual Heatmap View */
        <div className="space-y-4">
          <div className="flex gap-1 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-1 w-fit">
            {(["click", "scroll", "move"] as HeatmapType[]).map((type) => (
              <button
                key={type}
                onClick={() => setHeatmapType(type)}
                className={`rounded-lg px-4 py-1.5 text-[12px] font-medium capitalize transition-all ${
                  heatmapType === type
                    ? "bg-[hsl(var(--primary))] text-white shadow-sm"
                    : "text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
          <Card>
            <CardBody className="p-0">
              {heatmap.loading ? (
                <div className="p-6"><Spinner /></div>
              ) : heatmap.error ? (
                <div className="p-6"><ErrorBox message={heatmap.error} onRetry={heatmap.refetch} /></div>
              ) : heatmap.data && heatmap.data.points.length > 0 ? (
                <HeatmapCanvas data={heatmap.data.points} type={heatmapType} width={1200} height={800} />
              ) : (
                <div className="p-6"><EmptyState title={`No ${heatmapType} data`} description="Collect more sessions to see the visual heatmap." /></div>
              )}
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}

function ElementRow({ element: el, rank }: { element: ElementEmotionItem; rank: number }) {
  const [expanded, setExpanded] = useState(false);
  const hasFrustration = el.rage_click_rate > 0.1 || el.dominant_emotion === "frustration";

  // Use semantic label when available, fallback to element_id
  const displayName = el.label || el.element_id;
  const hasSemanticData = el.label || el.element_type || el.section;

  return (
    <div
      className={`px-5 py-4 transition-colors hover:bg-[hsl(var(--accent)/0.3)] cursor-pointer ${
        hasFrustration ? "border-l-2 border-l-red-400" : ""
      }`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center gap-4">
        {/* Rank */}
        <span className="w-6 text-[12px] font-semibold text-[hsl(var(--muted-foreground))]">#{rank}</span>

        {/* Element info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[13px] font-semibold text-[hsl(var(--foreground))]">
              {displayName}
            </span>
            {el.element_type && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0.5">
                {el.element_type}
              </Badge>
            )}
            {el.section && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0.5 text-[hsl(var(--muted-foreground))]">
                {el.section}
              </Badge>
            )}
            {el.rage_click_count > 0 && (
              <span className="rounded-md bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700">
                {el.rage_click_count} rage click{el.rage_click_count !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          <div className="mt-1 flex items-center gap-4 text-[12px] text-[hsl(var(--muted-foreground))]">
            <span>{el.event_count} events</span>
            <span>{el.click_count} clicks</span>
            <span>{el.session_count} sessions</span>
          </div>
        </div>

        {/* Emotion */}
        <div className="text-right">
          {el.dominant_emotion ? (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: EMOTION_COLORS[el.dominant_emotion] || "#6B7280" }} />
              <span
                className="text-[13px] font-semibold capitalize"
                style={{ color: EMOTION_COLORS[el.dominant_emotion] || "#6B7280" }}
              >
                {el.dominant_emotion}
              </span>
              {el.emotion_confidence != null && (
                <span className="text-[11px] text-[hsl(var(--muted-foreground))]">
                  {(el.emotion_confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
          ) : (
            <span className="text-[12px] text-[hsl(var(--muted-foreground))]">No emotion</span>
          )}
        </div>

        {/* Expand arrow */}
        <svg
          className={`w-4 h-4 text-[hsl(var(--muted-foreground))] transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </div>

      {/* Expanded details */}
      {expanded && el.emotion_breakdown && (
        <div className="mt-4 ml-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Object.entries(el.emotion_breakdown)
            .sort(([, a], [, b]) => (b as number) - (a as number))
            .map(([emotion, pct]) => (
              <div key={emotion}>
                <div className="flex items-center gap-1.5 mb-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: EMOTION_COLORS[emotion] || "#6B7280" }} />
                  <span className="text-[11px] font-medium capitalize text-[hsl(var(--foreground))]">{emotion}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-[hsl(var(--secondary))]">
                  <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: EMOTION_COLORS[emotion] || "#6B7280" }} />
                </div>
                <span className="text-[10px] text-[hsl(var(--muted-foreground))]">{(pct as number).toFixed(0)}%</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
