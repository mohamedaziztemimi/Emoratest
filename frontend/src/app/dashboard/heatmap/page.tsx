"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

// ── Components ────────────────────────────────────────────────────────

import HeatmapCanvas, { HeatmapPoint, HeatmapType } from "./HeatmapCanvas";
import EmotionOverlay, { EmotionZone } from "./EmotionOverlay";

// ── Types ────────────────────────────────────────────────────────

interface SessionInfo {
  id: string;
  sessionId: string;
  userId?: string;
  startTime: string;
  endTime?: string;
  dominantEmotion?: string;
  frustrationScore?: number;
}

interface HeatmapDataResponse {
  data: HeatmapPoint[];
  emotionZones: EmotionZone[];
  sessions: SessionInfo[];
  pageUrl: string;
}

interface EmotionBreakdown {
  emotion: string;
  count: number;
  percentage: number;
  color: string;
}

// ── Constants ────────────────────────────────────────────────────────

const EMOTION_ORDER = [
  "confusion",
  "frustration",
  "delight",
  "anxiety",
  "focus",
  "hesitation",
  "satisfaction",
] as const;

const EMOTION_COLORS: Record<string, string> = {
  confusion: "#F59E0B",
  frustration: "#EF4444",
  delight: "#10B981",
  anxiety: "#8B5CF6",
  focus: "#3B82F6",
  hesitation: "#FBBF24",
  satisfaction: "#60A5FA",
};

// ── Page Component ────────────────────────────────────────────────

export default function HeatmapPage() {
  const router = useRouter();
  const searchParams = new URLSearchParams(
    typeof window !== "undefined" ? window.location.search : ""
  );

  // State
  const [heatmapType, setHeatmapType] = useState<HeatmapType>("click");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [deviceFilter, setDeviceFilter] = useState<string>("all");
  const [showEmotionOverlay, setShowEmotionOverlay] = useState(true);
  const [selectedZone, setSelectedZone] = useState<EmotionZone | null>(null);
  const [selectedSession, setSelectedSession] = useState<SessionInfo | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [data, setData] = useState<HeatmapDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const pageUrl = searchParams.get("page") || "/";

      // Fetch heatmap data
      const heatmapRes = await fetch(`/api/v1/dashboard/analytics/friction-map?page_url=${encodeURIComponent(pageUrl)}`);
      if (!heatmapRes.ok) throw new Error("Failed to fetch heatmap data");
      const heatmapData = await heatmapRes.json();

      // Fetch emotion zones (mock for now - would be from emotion API)
      const emotionZones: EmotionZone[] = [];

      // Fetch sessions (mock for now)
      const sessions: SessionInfo[] = [];

      setData({
        data: heatmapData.data || [],
        emotionZones,
        sessions,
        pageUrl,
      });
    } catch (err) {
      console.error("Failed to fetch heatmap data:", err);
      setError("Failed to load heatmap data");
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle type change
  const handleTypeChange = useCallback((type: HeatmapType) => {
    setHeatmapType(type);
  }, []);

  // Handle device filter
  const handleDeviceChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setDeviceFilter(e.target.value);
  }, []);

  // Toggle emotion overlay
  const toggleEmotionOverlay = useCallback(() => {
    setShowEmotionOverlay((prev) => !prev);
  }, []);

  // Handle zone click
  const handleZoneClick = useCallback((zone: EmotionZone) => {
    setSelectedZone(zone);
  }, []);

  // Calculate emotion breakdown
  const emotionBreakdown: EmotionBreakdown[] = useMemo(() => {
    if (!data || data.sessions.length === 0) return [];

    const counts: Record<string, number> = {};
    data.sessions.forEach((session) => {
      const emotion = session.dominantEmotion || "unknown";
      counts[emotion] = (counts[emotion] || 0) + 1;
    });

    const total = Object.values(counts).reduce((a, b) => a + b, 0);

    return EMOTION_ORDER.map((emotion) => ({
      emotion,
      count: counts[emotion] || 0,
      percentage: total > 0 ? ((counts[emotion] || 0) / total) * 100 : 0,
      color: EMOTION_COLORS[emotion] || "#6B7280",
    })).filter((item) => item.count > 0).sort((a, b) => b.count - a.count);
  }, [data]);

  // Top frustration zones
  const topFrustrationZones = useMemo(() => {
    if (!data) return [];
    return data.emotionZones
      .filter((z) => z.emotion === "frustration")
      .sort((a, b) => b.userCount - a.userCount)
      .slice(0, 5);
  }, [data]);

  // Loading skeleton
  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-[hsl(var(--muted))] rounded"></div>
          <div className="h-32 bg-[hsl(var(--muted))] rounded"></div>
          <div className="h-8 bg-[hsl(var(--muted))] rounded"></div>
        </div>
      </div>
    );
  }

  // Empty state
  if (!loading && (!data || data.data.length === 0)) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[hsl(var(--muted))] rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-[hsl(var(--muted-foreground))]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0l-6.828-6.828a4 4 0 015.656 0l6.828 6.828a4 4 0 0015.656 0l-6.828-6.828a4 4 0 0000.006-4 4 0 012-2.828-2.828a4 4 0 008.828-8.828a4 4 0 00-2.828a4 4 0 015.657 0l6.828-6.828a4 4 0 015.656z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">No Data Available</h3>
          <p className="text-[hsl(var(--muted-foreground))] mt-2">
            Select a page URL or wait for more data to be collected.
          </p>
          <button
            onClick={() => router.push("/dashboard")}
            className="mt-6 px-4 py-2 bg-[hsl(var(--primary))] text-white rounded-lg hover:bg-[hsl(var(--primary-dark))] transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h-4m-4 4v6h4m-4-4h4" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">Error Loading Data</h3>
          <p className="text-[hsl(var(--muted-foreground))] mt-2">{error}</p>
          <button
            onClick={fetchData}
            className="mt-6 px-4 py-2 bg-[hsl(var(--primary))] text-white rounded-lg hover:bg-[hsl(var(--primary-dark))] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Main content
  return (
    <div className="flex flex-col h-screen">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[hsl(var(--border))] bg-[hsl(var(--card))]">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-[hsl(var(--foreground))]">Heatmap</h1>

          {/* Type Toggle */}
          <div className="flex bg-[hsl(var(--muted))] rounded-lg p-1">
            {(["click", "scroll", "move"] as HeatmapType[]).map((type) => (
              <button
                key={type}
                onClick={() => handleTypeChange(type)}
                className={`px-4 py-2 rounded-md capitalize transition-colors ${
                  heatmapType === type
                    ? "bg-[hsl(var(--primary))] text-white"
                    : "bg-transparent text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))]"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange((prev) => ({ ...prev, start: e.target.value }))}
            className="px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--card))] text-[hsl(var(--foreground))]"
          />
          <span className="text-[hsl(var(--muted-foreground))]">to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange((prev) => ({ ...prev, end: e.target.value }))}
            className="px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--card))] text-[hsl(var(--foreground))]"
          />
        </div>

        {/* Device Filter */}
        <select
          value={deviceFilter}
          onChange={handleDeviceChange}
          className="px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--card))] text-[hsl(var(--foreground))]"
        >
          <option value="all">All Devices</option>
          <option value="desktop">Desktop</option>
          <option value="mobile">Mobile</option>
          <option value="tablet">Tablet</option>
        </select>

        {/* Emotion Overlay Toggle */}
        <button
          onClick={toggleEmotionOverlay}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            showEmotionOverlay
              ? "bg-[hsl(var(--primary))] text-white"
              : "bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]"
          }`}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 00-5.656 0l-3.172-3.172a4 4 0 00-5.656 0l6.828-6.828a4 4 0 005.656 0l6.828-6.828a4 4 0 0000.006-4 4 0 012-2.828-2.828a4 4 0 008.828-8.828a4 4 0 015.657 0l-6.828-6.828a4 4 0 015.656z" />
          </svg>
          <span className="text-sm">Emotion Overlay</span>
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Heatmap Canvas */}
        <div className="flex-1 relative bg-[hsl(var(--muted))]/20">
          {data && (
            <div className="relative w-full h-full">
              <HeatmapCanvas
                data={data.data}
                type={heatmapType}
                width={1200}
                height={800}
              />
              {/* Emotion Overlay */}
              {showEmotionOverlay && (
                <EmotionOverlay
                  emotionZones={data.emotionZones}
                  visible={showEmotionOverlay}
                  onZoneClick={handleZoneClick}
                />
              )}
            </div>
          )}
        </div>

        {/* Right Sidebar */}
        <div className="w-80 bg-[hsl(var(--card))] border-l border-[hsl(var(--border))] overflow-y-auto">
          {/* Emotion Breakdown */}
          <div className="p-4">
            <h2 className="text-lg font-semibold mb-4 text-[hsl(var(--foreground))]">Emotion Breakdown</h2>
            <div className="space-y-3">
              {emotionBreakdown.map((item) => (
                <div key={item.emotion} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-[hsl(var(--foreground))] capitalize">
                      {item.emotion}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-[hsl(var(--foreground))]">
                      {item.count}
                    </div>
                    <div className="text-xs text-[hsl(var(--muted-foreground))]">
                      {item.percentage.toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Frustration Zones */}
          <div className="border-t border-[hsl(var(--border))] p-4">
            <h2 className="text-lg font-semibold mb-4 text-[hsl(var(--foreground))]">Frustration Zones</h2>
            {topFrustrationZones.length > 0 ? (
              <div className="space-y-3">
                {topFrustrationZones.map((zone, index) => (
                  <button
                    key={index}
                    onClick={() => handleZoneClick(zone)}
                    className={`w-full text-left p-3 rounded-lg border border-[hsl(var(--border))] transition-colors hover:border-[hsl(var(--primary))] ${
                      selectedZone?.emotion === zone.emotion && selectedZone.x === zone.x
                        ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/5"
                        : "border-transparent hover:border-[hsl(var(--border))] hover:bg-[hsl(var(--muted))]"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm text-[hsl(var(--foreground))]">
                        Zone {index + 1}
                      </span>
                      <span className="text-xs bg-[hsl(var(--muted))] px-2 py-1 rounded text-[hsl(var(--muted-foreground))]">
                        {(zone.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-xs text-[hsl(var(--muted-foreground))]">
                      {zone.userCount} user{zone.userCount !== 1 ? "s" : ""}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[hsl(var(--muted-foreground))]">
                <p className="text-sm">No frustration zones detected</p>
              </div>
            )}
          </div>

          {/* Zone Detail */}
          {selectedZone && (
            <div className="border-t border-[hsl(var(--border))] p-4">
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-2">Emotion</h3>
                  <p className="text-lg font-bold capitalize" style={{ color: EMOTION_COLORS[selectedZone.emotion] }}>
                    {selectedZone.emotion}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-2">Confidence</h3>
                  <p className="text-2xl font-bold text-[hsl(var(--foreground))]">
                    {(selectedZone.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-2">Affected Users</h3>
                  <p className="text-lg font-bold text-[hsl(var(--foreground))]">
                    {selectedZone.userCount}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-2">Position</h3>
                  <p className="text-sm text-[hsl(var(--foreground))]">
                    ({selectedZone.x.toFixed(0)}, {selectedZone.y.toFixed(0)})
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-2">Size</h3>
                  <p className="text-sm text-[hsl(var(--foreground))]">
                    {selectedZone.width.toFixed(0)}% x {selectedZone.height.toFixed(0)}%
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Timeline */}
        <div className="h-48 bg-[hsl(var(--card))] border-t border-[hsl(var(--border))] flex items-center px-4">
          <div className="flex-1">
            <h2 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-2">Session Replay</h2>
            {data && data.sessions.length > 0 ? (
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {data.sessions.slice(0, 20).map((session) => (
                  <button
                    key={session.id}
                    onClick={() => setSelectedSession(session)}
                    className={`flex-shrink-0 px-3 py-2 rounded-lg border transition-colors ${
                      selectedSession?.sessionId === session.sessionId
                        ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-white"
                        : "border-[hsl(var(--border))] hover:border-[hsl(var(--primary))] hover:bg-[hsl(var(--muted))]"
                    }`}
                  >
                    <div className="text-sm font-medium text-center">
                      {session.dominantEmotion || "Unknown"}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[hsl(var(--muted-foreground))]">No sessions available</p>
            )}
          </div>
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                isPlaying
                  ? "bg-[hsl(var(--primary))] text-white"
                  : "bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]"
              }`}
              disabled={!selectedSession}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isPlaying ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 4h4v12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3l4 4l-4 4h8" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
