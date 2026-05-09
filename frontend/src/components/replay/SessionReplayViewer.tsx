"use client";

import { useEffect, useRef, useState, useCallback } from "react";

// Inline SVG icons
const XIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const PlayIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M8 5v14l11-7z" />
  </svg>
);

const PauseIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
  </svg>
);

const SkipForwardIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
  </svg>
);

const BEHAVIORAL_STATES = {
  frustrated: { color: "#EF4444", label: "Frustrated", emoji: "😤" },
  confused: { color: "#F59E0B", label: "Confused", emoji: "😕" },
  hesitating: { color: "#EAB308", label: "Hesitating", emoji: "🤔" },
  engaged: { color: "#22C55E", label: "Engaged", emoji: "✓" },
  disengaged: { color: "#6B7280", label: "Disengaged", emoji: "😴" },
  neutral: { color: "#9CA3AF", label: "Neutral", emoji: "•" },
} as const;

type BehavioralState = keyof typeof BEHAVIORAL_STATES;

interface MousePathPoint {
  x: number;
  y: number;
  timestamp: number;
  scroll_x: number;
  scroll_y: number;
  viewport_width: number;
  viewport_height: number;
}

interface EmotionEvent {
  timestamp: string;
  primary_emotion: string;
  confidence: number;
  valence: number | null;
  arousal: number | null;
}

interface SessionReplayViewerProps {
  sessionId: string;
  mousePath: MousePathPoint[];
  emotions: EmotionEvent[];
  pageUrl: string | null;
  pageTitle: string | null;
  pageWidth: number | null;
  pageHeight: number | null;
  devicePixelRatio: number | null;
  durationSeconds: number | null;
  onClose: () => void;
}

// ── Key Moments Detection ─────────────────────────────────────────

type HighlightType = "rage_click" | "state_change" | "exit_intent" | "long_pause" | "erratic_movement" | "hesitation";

interface Highlight {
  timestamp: number;
  type: HighlightType;
  state: BehavioralState;
  description: string;
  icon: string;
}

const HIGHLIGHT_INFO: Record<HighlightType, { icon: string; label: string; color: string }> = {
  rage_click: { icon: "😤", label: "Rage Click", color: "#EF4444" },
  state_change: { icon: "🔄", label: "State Change", color: "#F59E0B" },
  exit_intent: { icon: "🚪", label: "Exit Intent", color: "#F97316" },
  long_pause: { icon: "⏸️", label: "Long Pause", color: "#6B7280" },
  erratic_movement: { icon: "⚡", label: "Erratic Movement", color: "#EC4899" },
  hesitation: { icon: "🤔", label: "Hesitation", color: "#EAB308" },
};

function detectHighlights(mousePath: MousePathPoint[], emotions: EmotionEvent[], startTimeMs: number, endTimeMs: number): Highlight[] {
  const highlights: Highlight[] = [];

  if (mousePath.length === 0) return highlights;

  // 1. Detect rage clicks
  const clickGroups: MousePathPoint[][] = [];
  let currentGroup: MousePathPoint[] = [];

  for (const point of mousePath) {
    const timeThreshold = 2000;
    const distanceThreshold = 50;

    if (currentGroup.length === 0) {
      currentGroup.push(point);
    } else {
      const lastPoint = currentGroup[currentGroup.length - 1];
      const timeDiff = point.timestamp - lastPoint.timestamp;
      const distance = Math.sqrt(Math.pow(point.x - lastPoint.x, 2) + Math.pow(point.y - lastPoint.y, 2));

      if (timeDiff <= timeThreshold && distance <= distanceThreshold) {
        currentGroup.push(point);
      } else {
        if (currentGroup.length >= 3) {
          clickGroups.push([...currentGroup]);
        }
        currentGroup = [point];
      }
    }
  }
  if (currentGroup.length >= 3) {
    clickGroups.push(currentGroup);
  }

  for (const group of clickGroups) {
    const relativeTime = (group[0].timestamp - startTimeMs) / 1000;
    highlights.push({
      timestamp: relativeTime,
      type: "rage_click",
      state: "frustrated",
      description: `Rage click: ${group.length} rapid clicks`,
      icon: HIGHLIGHT_INFO.rage_click.icon,
    });
  }

  // 2. Detect state changes to frustrated
  for (let i = 1; i < emotions.length; i++) {
    const prevState = mapToBehavioralState(emotions[i - 1].primary_emotion);
    const currState = mapToBehavioralState(emotions[i].primary_emotion);
    if (currState === "frustrated" && prevState !== "frustrated") {
      const emotionTime = new Date(emotions[i].timestamp).getTime();
      const relativeTime = (emotionTime - startTimeMs) / 1000;
      highlights.push({
        timestamp: relativeTime,
        type: "state_change",
        state: "frustrated",
        description: "Transitioned to frustrated",
        icon: HIGHLIGHT_INFO.state_change.icon,
      });
    }
  }

  // 3. Detect exit intents
  for (let i = 1; i < mousePath.length; i++) {
    const point = mousePath[i];
    const prevPoint = mousePath[i - 1];
    const timeDiff = (point.timestamp - prevPoint.timestamp);
    if (timeDiff <= 0) continue;

    const velocityY = Math.abs(point.y - prevPoint.y) / (timeDiff / 1000);
    const nearTop = point.y < 10 || point.scroll_y < 10;

    if (nearTop && velocityY > 500) {
      const relativeTime = (point.timestamp - startTimeMs) / 1000;
      highlights.push({
        timestamp: relativeTime,
        type: "exit_intent",
        state: "disengaged",
        description: "Exit intent detected",
        icon: HIGHLIGHT_INFO.exit_intent.icon,
      });
    }
  }

  // 4. Detect long pauses
  for (let i = 1; i < mousePath.length; i++) {
    const timeDiff = (mousePath[i].timestamp - mousePath[i - 1].timestamp) / 1000;
    if (timeDiff >= 3) {
      const relativeTime = (mousePath[i].timestamp - startTimeMs) / 1000;
      highlights.push({
        timestamp: relativeTime,
        type: "long_pause",
        state: "confused",
        description: `Long pause: ${Math.round(timeDiff)}s`,
        icon: HIGHLIGHT_INFO.long_pause.icon,
      });
    }
  }

  // 5. Detect erratic movements
  for (let i = 1; i < mousePath.length; i++) {
    const point = mousePath[i];
    const prevPoint = mousePath[i - 1];
    const timeDiff = (point.timestamp - prevPoint.timestamp) / 1000;
    if (timeDiff <= 0) continue;

    const distance = Math.sqrt(Math.pow(point.x - prevPoint.x, 2) + Math.pow(point.y - prevPoint.y, 2));
    const velocity = distance / timeDiff;

    if (velocity > 3000) {
      const relativeTime = (point.timestamp - startTimeMs) / 1000;
      highlights.push({
        timestamp: relativeTime,
        type: "erratic_movement",
        state: "confused",
        description: `Erratic movement: ${Math.round(velocity)}px/s`,
        icon: HIGHLIGHT_INFO.erratic_movement.icon,
      });
    }
  }

  // 6. Detect hesitation
  const hesitatingStates = emotions.filter(e => mapToBehavioralState(e.primary_emotion) === "hesitating");
  for (const emotion of hesitatingStates) {
    const emotionTime = new Date(emotion.timestamp).getTime();
    const relativeTime = (emotionTime - startTimeMs) / 1000;
    highlights.push({
      timestamp: relativeTime,
      type: "hesitation",
      state: "hesitating",
      description: "Hesitation detected",
      icon: HIGHLIGHT_INFO.hesitation.icon,
    });
  }

  // Sort and deduplicate
  highlights.sort((a, b) => a.timestamp - b.timestamp);
  const deduplicated: Highlight[] = [];
  let lastTimestamp = -Infinity;

  for (const highlight of highlights) {
    if (highlight.timestamp - lastTimestamp >= 1) {
      deduplicated.push(highlight);
      lastTimestamp = highlight.timestamp;
    }
  }

  // Prioritize frustrated and confused moments
  const prioritized = deduplicated.sort((a, b) => {
    const priorityOrder: Record<BehavioralState, number> = {
      frustrated: 1,
      confused: 2,
      hesitating: 3,
      disengaged: 4,
      engaged: 5,
      neutral: 6,
    };
    return priorityOrder[a.state] - priorityOrder[b.state];
  });

  return prioritized.slice(0, 20);
}

// Map backend emotion names to 5 behavioral states
function mapToBehavioralState(emotion: string): BehavioralState {
  const map: Record<string, BehavioralState> = {
    frustration: "frustrated",
    frustrated: "frustrated",
    anxiety: "frustrated",
    confusion: "confused",
    confused: "confused",
    hesitation: "hesitating",
    hesitating: "hesitating",
    focus: "engaged",
    engaged: "engaged",
    satisfaction: "engaged",
    delight: "engaged",
    boredom: "disengaged",
    disengaged: "disengaged",
    insufficient_data: "neutral",
  };
  return map[emotion] || "neutral";
}

export function SessionReplayViewer({
  sessionId,
  mousePath,
  emotions,
  pageUrl,
  pageTitle,
  pageWidth,
  pageHeight,
  devicePixelRatio,
  durationSeconds,
  onClose,
}: SessionReplayViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [currentState, setCurrentState] = useState<BehavioralState>("neutral");
  const [highlightsMode, setHighlightsMode] = useState(false);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [currentHighlightIndex, setCurrentHighlightIndex] = useState(0);
  const [screenshotUrl, setScreenshotUrl] = useState<string | null>(null);
  const [screenshotLoading, setScreenshotLoading] = useState(true);

  // ── FIX 1: Calculate duration properly from epoch timestamps ─────────
  // Timestamps are epoch milliseconds - calculate relative duration
  const timestamps = mousePath.map(p => p.timestamp);
  const startTimeMs = timestamps.length > 0 ? Math.min(...timestamps) : 0;
  const endTimeMs = timestamps.length > 0 ? Math.max(...timestamps) : 0;
  // Calculate duration in milliseconds, then convert to seconds
  const durationMs = endTimeMs - startTimeMs;
  const totalDurationSeconds = Math.max(0.1, durationMs / 1000); // Convert to seconds, minimum 0.1s

  // Get viewport dimensions from first mouse path point
  const recordedViewport = mousePath.length > 0 ? {
    width: mousePath[0].viewport_width || 1920,
    height: mousePath[0].viewport_height || 1080,
  } : { width: 1920, height: 1080 };

  // Get current state based on time
  const getStateAtTime = useCallback((time: number): BehavioralState => {
    if (!emotions.length) return "neutral";

    const currentTimeMs = startTimeMs + time * 1000;
    let closestEmotion = emotions[0];
    let minDiff = Infinity;

    for (const emotion of emotions) {
      const emotionTime = new Date(emotion.timestamp).getTime();
      const diff = Math.abs(emotionTime - currentTimeMs);
      if (diff < minDiff) {
        minDiff = diff;
        closestEmotion = emotion;
      }
    }

    if (minDiff < 5000) {
      return mapToBehavioralState(closestEmotion.primary_emotion);
    }
    return "neutral";
  }, [emotions, startTimeMs]);

  // Detect highlights on mount
  useEffect(() => {
    const detected = detectHighlights(mousePath, emotions, startTimeMs, endTimeMs);
    setHighlights(detected);
  }, [mousePath, emotions, startTimeMs, endTimeMs]);

  // ── Load screenshot for replay background ─────────────────────────────
  useEffect(() => {
    const loadScreenshot = async () => {
      setScreenshotLoading(true);
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboard/sessions/${sessionId}/replay/screenshot`,
          { credentials: "include" }
        );

        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          setScreenshotUrl(url);
        } else {
          // Screenshot not available, will use wireframe fallback
          setScreenshotUrl(null);
        }
      } catch {
        // Error fetching screenshot, will use wireframe fallback
        setScreenshotUrl(null);
      } finally {
        setScreenshotLoading(false);
      }
    };

    loadScreenshot();

    // Cleanup object URL on unmount
    return () => {
      if (screenshotUrl) {
        URL.revokeObjectURL(screenshotUrl);
      }
    };
  }, [sessionId]);

  // ── FIX 3: Proper coordinate transformation and drawing ───────────────
  const drawFrame = useCallback((time: number) => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (mousePath.length === 0) return;

    // Calculate scale: fit recorded PAGE into canvas (for screenshot alignment)
    // The screenshot is the full page, so we scale based on page dimensions
    const safePageWidth = Math.max(pageWidth || recordedViewport.width, 800);
    const safePageHeight = Math.max(pageHeight || recordedViewport.height * 3, 1200);
    const scaleX = canvas.width / safePageWidth;
    const scaleY = canvas.height / safePageHeight;
    const scale = Math.min(scaleX, scaleY);

    // Calculate centering offset to maintain aspect ratio
    const scaledWidth = safePageWidth * scale;
    const scaledHeight = safePageHeight * scale;
    const offsetX = (canvas.width - scaledWidth) / 2;
    const offsetY = (canvas.height - scaledHeight) / 2;

    // Only draw wireframe if no screenshot available
    if (!screenshotUrl && !screenshotLoading) {
      drawWireframeBackground(ctx, canvas.width, canvas.height, pageUrl, scaledWidth, scaledHeight, offsetX, offsetY);
    }

    // Current time in milliseconds (relative to start)
    const currentTimestampMs = startTimeMs + time * 1000;

    // Find all points up to current time
    // Include a small buffer to ensure the first point is visible at time=0
    const bufferMs = 50; // 50ms buffer
    const pathPoints: typeof mousePath = [];
    for (const point of mousePath) {
      if (point.timestamp <= currentTimestampMs + bufferMs) {
        pathPoints.push(point);
      } else {
        break;
      }
    }

    // Always show at least the first point if available
    if (pathPoints.length === 0 && mousePath.length > 0) {
      pathPoints.push(mousePath[0]);
    }

    if (pathPoints.length === 0) return;

    // Get last 50 points for trail
    const trailPoints = pathPoints.slice(-50);

    // Draw trail line
    if (trailPoints.length > 1) {
      ctx.strokeStyle = "#3B82F6";
      ctx.lineWidth = 2;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.globalAlpha = 0.5;

      ctx.beginPath();
      for (let i = 0; i < trailPoints.length; i++) {
        const point = trailPoints[i];
        // Convert page coordinates to viewport coordinates, then scale
        const viewportX = point.x - point.scroll_x;
        const viewportY = point.y - point.scroll_y;
        // Apply centering offset
        const cx = viewportX * scale + offsetX;
        const cy = viewportY * scale + offsetY;

        if (i === 0) {
          ctx.moveTo(cx, cy);
        } else {
          ctx.lineTo(cx, cy);
        }
      }
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Draw current cursor position
    const lastPoint = pathPoints[pathPoints.length - 1];
    const viewportX = lastPoint.x - lastPoint.scroll_x;
    const viewportY = lastPoint.y - lastPoint.scroll_y;
    // Apply centering offset
    const cx = viewportX * scale + offsetX;
    const cy = viewportY * scale + offsetY;

    // Get current state color
    const state = getStateAtTime(time);
    const stateColor = BEHAVIORAL_STATES[state].color;

    // Draw cursor glow (larger, more visible)
    const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 30);
    gradient.addColorStop(0, stateColor + "CC");
    gradient.addColorStop(1, stateColor + "00");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(cx, cy, 30, 0, Math.PI * 2);
    ctx.fill();

    // Draw cursor dot (12px diameter = 6px radius)
    ctx.fillStyle = stateColor;
    ctx.beginPath();
    ctx.arc(cx, cy, 6, 0, Math.PI * 2);
    ctx.fill();

    // Draw cursor border
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();
  }, [mousePath, startTimeMs, getStateAtTime, recordedViewport, pageUrl, pageWidth, pageHeight, screenshotUrl, screenshotLoading]);

  // Draw wireframe background with grid and zone labels
  const drawWireframeBackground = (
    ctx: CanvasRenderingContext2D,
    canvasWidth: number,
    canvasHeight: number,
    url: string | null,
    scaledWidth: number,
    scaledHeight: number,
    offsetX: number,
    offsetY: number
  ) => {
    // Fill entire canvas background
    ctx.fillStyle = "#F9FAFB";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Draw grid pattern on entire canvas
    ctx.strokeStyle = "#E5E7EB";
    ctx.lineWidth = 1;

    const gridSize = 40;
    for (let x = 0; x < canvasWidth; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvasHeight);
      ctx.stroke();
    }
    for (let y = 0; y < canvasHeight; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvasWidth, y);
      ctx.stroke();
    }

    // Draw the viewport area (the actual page area)
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(offsetX, offsetY, scaledWidth, scaledHeight);
    ctx.strokeStyle = "#D1D5DB";
    ctx.lineWidth = 2;
    ctx.strokeRect(offsetX, offsetY, scaledWidth, scaledHeight);

    // Draw browser chrome mockup at top of viewport area
    const chromeHeight = 36;
    ctx.fillStyle = "#F3F4F6";
    ctx.fillRect(offsetX + 4, offsetY + 4, scaledWidth - 8, chromeHeight);
    ctx.strokeStyle = "#D1D5DB";
    ctx.lineWidth = 1;
    ctx.strokeRect(offsetX + 4, offsetY + 4, scaledWidth - 8, chromeHeight);

    // URL bar
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(offsetX + 12, offsetY + 10, scaledWidth - 24, 20);
    ctx.fillStyle = "#9CA3AF";
    ctx.font = "11px monospace";
    ctx.textAlign = "left";
    const displayUrl = url || "https://example.com/page";
    const maxWidth = scaledWidth - 40;
    const truncatedUrl = displayUrl.length > 50 ? displayUrl.slice(0, 47) + "..." : displayUrl;
    ctx.fillText(truncatedUrl, offsetX + 16, offsetY + 24);

    // Draw zone labels (positioned relative to viewport area)
    ctx.fillStyle = "#9CA3AF";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";

    // Header zone (top section after chrome)
    const headerY = offsetY + chromeHeight + 30;
    ctx.fillText("Header / Nav", offsetX + scaledWidth / 2, headerY);

    // Draw a subtle divider line
    ctx.strokeStyle = "#E5E7EB";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(offsetX, offsetY + scaledHeight * 0.2);
    ctx.lineTo(offsetX + scaledWidth, offsetY + scaledHeight * 0.2);
    ctx.stroke();
    ctx.setLineDash([]);

    // Content zone (middle)
    ctx.fillText("Content", offsetX + scaledWidth / 2, offsetY + scaledHeight / 2);

    // Draw a subtle divider line
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(offsetX, offsetY + scaledHeight * 0.85);
    ctx.lineTo(offsetX + scaledWidth, offsetY + scaledHeight * 0.85);
    ctx.stroke();
    ctx.setLineDash([]);

    // Footer zone (bottom)
    ctx.fillText("Footer", offsetX + scaledWidth / 2, offsetY + scaledHeight - 15);
  };

  // Animation loop
  const playbackRef = useRef({
    isPlaying,
    currentTime,
    totalDuration: totalDurationSeconds,
    playbackSpeed,
    highlightsMode,
    highlights,
    currentHighlightIndex,
  });

  useEffect(() => {
    playbackRef.current = {
      isPlaying,
      currentTime,
      totalDuration: totalDurationSeconds,
      playbackSpeed,
      highlightsMode,
      highlights,
      currentHighlightIndex,
    };
  }, [isPlaying, currentTime, totalDurationSeconds, playbackSpeed, highlightsMode, highlights, currentHighlightIndex]);

  useEffect(() => {
    if (!playbackRef.current.isPlaying) return;

    let startTime: number | null = null;
    let lastTime = playbackRef.current.currentTime;

    const animate = (timestamp: number) => {
      if (startTime === null) startTime = timestamp;
      const elapsed = (timestamp - startTime) / 1000 * playbackRef.current.playbackSpeed;

      let newTime: number;
      const ref = playbackRef.current;

      if (ref.highlightsMode && ref.highlights.length > 0) {
        const currentHighlight = ref.highlights[ref.currentHighlightIndex];
        const highlightStart = Math.max(0, currentHighlight.timestamp - 1.5);
        const highlightEnd = Math.min(ref.totalDuration, currentHighlight.timestamp + 1.5);

        newTime = Math.min(lastTime + elapsed, highlightEnd);

        if (newTime >= highlightEnd && ref.currentHighlightIndex < ref.highlights.length - 1) {
          const nextIdx = ref.currentHighlightIndex + 1;
          playbackRef.current.currentHighlightIndex = nextIdx;
          setCurrentHighlightIndex(nextIdx);
          const nextHighlight = ref.highlights[nextIdx];
          const nextStart = Math.max(0, nextHighlight.timestamp - 1.5);
          lastTime = nextStart;
          setCurrentTime(nextStart);
          startTime = timestamp;
          animationRef.current = requestAnimationFrame(animate);
          return;
        }

        if (newTime >= ref.totalDuration || ref.currentHighlightIndex >= ref.highlights.length - 1) {
          setIsPlaying(false);
          return;
        }
      } else {
        newTime = Math.min(lastTime + elapsed, ref.totalDuration);
        if (newTime >= ref.totalDuration) {
          setIsPlaying(false);
          return;
        }
      }

      lastTime = newTime;
      setCurrentTime(newTime);
      setCurrentState(getStateAtTime(newTime));
      drawFrame(newTime);

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, drawFrame, getStateAtTime]);

  // Setup canvas size
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const resizeCanvas = () => {
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      if (playbackRef.current) {
        drawFrame(playbackRef.current.currentTime);
      }
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    return () => window.removeEventListener("resize", resizeCanvas);
  }, [drawFrame]);

  // Draw initial frame
  useEffect(() => {
    drawFrame(0);
  }, [drawFrame]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying(p => !p);
      } else if (e.code === "ArrowLeft") {
        setCurrentTime(t => Math.max(0, t - 5));
        setIsPlaying(false);
      } else if (e.code === "ArrowRight") {
        setCurrentTime(t => Math.min(totalDurationSeconds, t + 5));
        setIsPlaying(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [totalDurationSeconds]);

  const togglePlay = () => setIsPlaying(p => !p);

  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = (parseFloat(e.target.value) / 100) * totalDurationSeconds;
    setCurrentTime(newTime);
    setCurrentState(getStateAtTime(newTime));
    if (!isPlaying) {
      drawFrame(newTime);
    }
  };

  // ── FIX 1: Format time as M:SS (relative seconds, not epoch) ───────────
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Build timeline state segments
  const timelineSegments = (() => {
    if (emotions.length === 0) return [];

    const segments: { start: number; end: number; state: BehavioralState }[] = [];
    let currentState: BehavioralState = "neutral";
    let segmentStart = 0;

    for (let t = 0; t <= totalDurationSeconds; t += 0.5) {
      const state = getStateAtTime(t);
      if (state !== currentState) {
        segments.push({ start: segmentStart, end: t, state: currentState });
        currentState = state;
        segmentStart = t;
      }
    }
    segments.push({ start: segmentStart, end: totalDurationSeconds, state: currentState });

    return segments.filter(s => s.end - s.start > 0.1);
  })();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-5xl max-h-[90vh] bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Session Replay</h2>
            <p className="text-sm text-gray-500">{pageTitle || pageUrl || "Unknown page"}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XIcon />
            </button>
          </div>
        </div>

        {/* Session metadata bar */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200 flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Duration:</span>
            <span className="font-medium text-gray-900">{formatTime(totalDurationSeconds)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Data points:</span>
            <span className="font-medium text-gray-900">{mousePath.length}</span>
          </div>
          {currentState !== "neutral" && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">State:</span>
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white"
                style={{ backgroundColor: BEHAVIORAL_STATES[currentState].color }}
              >
                {BEHAVIORAL_STATES[currentState].emoji} {BEHAVIORAL_STATES[currentState].label}
              </span>
            </div>
          )}
          {screenshotLoading && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Loading screenshot...</span>
            </div>
          )}
          {screenshotUrl && !screenshotLoading && (
            <div className="flex items-center gap-2">
              <span className="text-green-600 text-xs">✓ Screenshot loaded</span>
            </div>
          )}
        </div>

        {/* Main content */}
        <div className="flex">
          {/* Replay canvas */}
          <div ref={containerRef} className="flex-1 bg-gray-100 relative" style={{ minHeight: 400 }}>
            {/* Screenshot background (behind canvas) */}
            {screenshotUrl && (
              <img
                src={screenshotUrl}
                alt="Page screenshot"
                className="absolute inset-0 w-full h-full object-contain opacity-85"
                style={{ zIndex: 0 }}
              />
            )}

            {/* Canvas for cursor and trail (on top of screenshot) */}
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" style={{ zIndex: 1 }} />

            {/* State label overlay */}
            {currentState !== "neutral" && (
              <div
                className="absolute top-4 left-4 px-3 py-2 rounded-full text-sm font-medium text-white shadow-lg flex items-center gap-2"
                style={{ backgroundColor: BEHAVIORAL_STATES[currentState].color, zIndex: 2 }}
              >
                <span>{BEHAVIORAL_STATES[currentState].emoji}</span>
                <span>{BEHAVIORAL_STATES[currentState].label}</span>
              </div>
            )}

            {/* Time display */}
            <div
              className="absolute bottom-20 left-4 px-3 py-2 bg-white rounded-lg shadow text-sm font-mono"
              style={{ zIndex: 2 }}
            >
              {formatTime(currentTime)} / {formatTime(totalDurationSeconds)}
            </div>
          </div>

          {/* Sidebar with legend */}
          <div className="w-48 border-l border-gray-200 p-4 bg-gray-50">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
              Behavioral States
            </h3>
            <div className="space-y-2">
              {Object.entries(BEHAVIORAL_STATES).map(([key, { color, label, emoji }]) => (
                key !== "neutral" && (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-gray-700">{emoji} {label}</span>
                  </div>
                )
              ))}
            </div>

            {/* Session info */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                Session Info
              </h3>
              <div className="text-xs text-gray-600 space-y-1">
                <div>Duration: {formatTime(totalDurationSeconds)}</div>
                <div>Points: {mousePath.length}</div>
                <div>Viewport: {recordedViewport.width}x{recordedViewport.height}</div>
              </div>
            </div>

            {/* Keyboard shortcuts */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                Shortcuts
              </h3>
              <div className="text-xs text-gray-600 space-y-1">
                <div><kbd className="px-1 bg-gray-200 rounded">Space</kbd> Play/Pause</div>
                <div><kbd className="px-1 bg-gray-200 rounded">←</kbd><kbd className="px-1 bg-gray-200 rounded">→</kbd> Skip 5s</div>
              </div>
            </div>
          </div>
        </div>

        {/* Timeline scrubber */}
        <div className="px-6 py-4 bg-white border-t border-gray-200">
          {/* State timeline bar */}
          <div className="relative h-2 rounded-full overflow-hidden flex mb-3">
            {timelineSegments.map((seg, i) => (
              <div
                key={i}
                className="h-full"
                style={{
                  width: `${((seg.end - seg.start) / totalDurationSeconds) * 100}%`,
                  backgroundColor: BEHAVIORAL_STATES[seg.state].color,
                }}
                title={`${BEHAVIORAL_STATES[seg.state].label}: ${formatTime(seg.start)} - ${formatTime(seg.end)}`}
              />
            ))}
            {/* Highlight markers */}
            {highlights.map((hl, i) => (
              <div
                key={i}
                className="absolute top-0 w-1.5 h-full flex items-center justify-center cursor-pointer group"
                style={{ left: `${(hl.timestamp / totalDurationSeconds) * 100}%` }}
                onClick={() => {
                  setCurrentTime(hl.timestamp);
                  setCurrentState(getStateAtTime(hl.timestamp));
                  if (!isPlaying) drawFrame(hl.timestamp);
                }}
                title={`${hl.icon} ${hl.description} at ${formatTime(hl.timestamp)}`}
              >
                <div
                  className="w-2 h-2 rounded-full border-2 border-white shadow-sm"
                  style={{ backgroundColor: HIGHLIGHT_INFO[hl.type].color }}
                />
                <div className="absolute bottom-full mb-2 hidden group-hover:block whitespace-nowrap bg-gray-900 text-white text-xs px-2 py-1 rounded">
                  {hl.icon} {hl.description}
                </div>
              </div>
            ))}
          </div>

          {/* Scrubber controls */}
          <div className="flex items-center gap-4">
            <button
              onClick={togglePlay}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {isPlaying ? <PauseIcon /> : <PlayIcon />}
            </button>

            {highlights.length > 0 && (
              <button
                onClick={() => {
                  setHighlightsMode(!highlightsMode);
                  setCurrentHighlightIndex(0);
                  setCurrentTime(Math.max(0, highlights[0].timestamp - 1.5));
                  if (!isPlaying) setIsPlaying(true);
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                  highlightsMode
                    ? "bg-orange-100 text-orange-700 border border-orange-300"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                <SkipForwardIcon />
                {highlightsMode ? `Highlight ${currentHighlightIndex + 1}/${highlights.length}` : "Skip to Highlights"}
              </button>
            )}

            <input
              type="range"
              min="0"
              max="100"
              value={(currentTime / totalDurationSeconds) * 100 || 0}
              onChange={handleScrub}
              className="flex-1 h-2 bg-gray-200 rounded-full appearance-none cursor-pointer"
            />

            <div className="flex items-center gap-1">
              {[0.5, 1, 2, 4].map((speed) => (
                <button
                  key={speed}
                  onClick={() => setPlaybackSpeed(speed)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    playbackSpeed === speed
                      ? "bg-blue-100 text-blue-700 font-medium"
                      : "text-gray-500 hover:bg-gray-100"
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Key Moments List */}
        {highlights.length > 0 && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Key Moments ({highlights.length})</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-40 overflow-y-auto">
              {highlights.map((hl, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setCurrentTime(hl.timestamp);
                    setCurrentState(getStateAtTime(hl.timestamp));
                    if (!isPlaying) drawFrame(hl.timestamp);
                  }}
                  className={`text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                    Math.abs(currentTime - hl.timestamp) < 2
                      ? "bg-blue-100 border border-blue-300"
                      : "bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base">{hl.icon}</span>
                    <span className="font-medium text-gray-700">{hl.description}</span>
                  </div>
                  <div className="mt-1 text-gray-500 font-mono">{formatTime(hl.timestamp)}</div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
