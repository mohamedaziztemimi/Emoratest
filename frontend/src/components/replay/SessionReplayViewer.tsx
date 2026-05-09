"use client";

import { useEffect, useRef, useState, useCallback } from "react";

// Inline SVG icons to avoid external dependency
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

function detectHighlights(mousePath: MousePathPoint[], emotions: EmotionEvent[]): Highlight[] {
  const highlights: Highlight[] = [];

  if (mousePath.length === 0) return highlights;

  const timestamps = mousePath.map(p => p.timestamp);
  const minTime = Math.min(...timestamps, 0);
  const maxTime = Math.max(...timestamps, 0);

  // 1. Detect rage clicks (3+ clicks within 2 seconds within 50px)
  const clickGroups: MousePathPoint[][] = [];
  let currentGroup: MousePathPoint[] = [];

  for (const point of mousePath) {
    // Filter points that could be clicks (you might need to add metadata to track actual clicks)
    // For now, we'll use proximity and timing
    const timeThreshold = 2000; // 2 seconds
    const distanceThreshold = 50; // 50px

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

  // Add rage click highlights
  for (const group of clickGroups) {
    highlights.push({
      timestamp: (group[0].timestamp - minTime) / 1000,
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
      highlights.push({
        timestamp: (emotionTime - minTime) / 1000,
        type: "state_change",
        state: "frustrated",
        description: "Transitioned to frustrated",
        icon: HIGHLIGHT_INFO.state_change.icon,
      });
    }
  }

  // 3. Detect exit intents (mouse to top of viewport with high velocity)
  for (let i = 1; i < mousePath.length; i++) {
    const point = mousePath[i];
    const prevPoint = mousePath[i - 1];
    const timeDiff = (point.timestamp - prevPoint.timestamp) / 1000; // seconds
    if (timeDiff <= 0) continue;

    const velocityY = Math.abs(point.y - prevPoint.y) / timeDiff;
    const nearTop = point.y < 10 || point.scroll_y < 10;

    if (nearTop && velocityY > 500) {
      highlights.push({
        timestamp: (point.timestamp - minTime) / 1000,
        type: "exit_intent",
        state: "disengaged",
        description: "Exit intent detected",
        icon: HIGHLIGHT_INFO.exit_intent.icon,
      });
    }
  }

  // 4. Detect long pauses (3+ seconds gap between events)
  for (let i = 1; i < mousePath.length; i++) {
    const timeDiff = (mousePath[i].timestamp - mousePath[i - 1].timestamp) / 1000;
    if (timeDiff >= 3) {
      highlights.push({
        timestamp: (mousePath[i].timestamp - minTime) / 1000,
        type: "long_pause",
        state: "confused",
        description: `Long pause: ${Math.round(timeDiff)}s`,
        icon: HIGHLIGHT_INFO.long_pause.icon,
      });
    }
  }

  // 5. Detect erratic movements (velocity spikes above 3000px/s)
  for (let i = 1; i < mousePath.length; i++) {
    const point = mousePath[i];
    const prevPoint = mousePath[i - 1];
    const timeDiff = (point.timestamp - prevPoint.timestamp) / 1000;
    if (timeDiff <= 0) continue;

    const distance = Math.sqrt(Math.pow(point.x - prevPoint.x, 2) + Math.pow(point.y - prevPoint.y, 2));
    const velocity = distance / timeDiff;

    if (velocity > 3000) {
      highlights.push({
        timestamp: (point.timestamp - minTime) / 1000,
        type: "erratic_movement",
        state: "confused",
        description: `Erratic movement: ${Math.round(velocity)}px/s`,
        icon: HIGHLIGHT_INFO.erratic_movement.icon,
      });
    }
  }

  // 6. Detect hesitation (hesitating state near a click target)
  const hesitatingStates = emotions.filter(e => mapToBehavioralState(e.primary_emotion) === "hesitating");
  for (const emotion of hesitatingStates) {
    const emotionTime = new Date(emotion.timestamp).getTime();
    highlights.push({
      timestamp: (emotionTime - minTime) / 1000,
      type: "hesitation",
      state: "hesitating",
      description: "Hesitation detected",
      icon: HIGHLIGHT_INFO.hesitation.icon,
    });
  }

  // Sort by timestamp and deduplicate (keep only highlights 1+ seconds apart)
  highlights.sort((a, b) => a.timestamp - b.timestamp);
  const deduplicated: Highlight[] = [];
  let lastTimestamp = -Infinity;

  for (const highlight of highlights) {
    if (highlight.timestamp - lastTimestamp >= 1) {
      deduplicated.push(highlight);
      lastTimestamp = highlight.timestamp;
    }
  }

  // Prioritize frustrated and confused moments, max 20 highlights
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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

  // Calculate time range from mouse_path
  const timestamps = mousePath.map(p => p.timestamp);
  const minTime = Math.min(...timestamps, 0);
  const maxTime = Math.max(...timestamps, 0);
  const totalDuration = maxTime - minTime || 1;

  // Get current state based on time
  const getStateAtTime = useCallback((time: number): BehavioralState => {
    if (!emotions.length) return "neutral";

    // Find the emotion event closest to current time
    const currentTimeMs = minTime + time * 1000;
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

    // Only use state if within 5 seconds
    if (minDiff < 5000) {
      return mapToBehavioralState(closestEmotion.primary_emotion);
    }
    return "neutral";
  }, [emotions, minTime]);

  // Detect highlights on mount
  useEffect(() => {
    const detected = detectHighlights(mousePath, emotions);
    setHighlights(detected);
  }, [mousePath, emotions]);

  // Draw frame
  const drawFrame = useCallback((time: number) => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (mousePath.length === 0) return;

    // Calculate scale to fit viewport in canvas
    const containerRect = container.getBoundingClientRect();
    const scaleX = canvas.width / (pageWidth || containerRect.width);
    const scaleY = canvas.height / (pageHeight || containerRect.height);
    const scale = Math.min(scaleX, scaleY) * 0.9;

    // Calculate current timestamp
    const currentTimestamp = minTime + time * 1000;

    // Find all points up to current time
    const pathPoints: typeof mousePath = [];
    for (const point of mousePath) {
      if (point.timestamp <= currentTimestamp) {
        pathPoints.push(point);
      } else {
        break;
      }
    }

    if (pathPoints.length === 0) return;

    // Draw trail with state-based coloring
    const stateChanges: { time: number; state: BehavioralState }[] = [];
    for (let i = 0; i < pathPoints.length; i += 10) {
      const pointTime = pathPoints[i].timestamp - minTime;
      const pointState = getStateAtTime(pointTime / 1000);
      if (i === 0 || stateChanges[stateChanges.length - 1]?.state !== pointState) {
        stateChanges.push({ time: pointTime / 1000, state: pointState });
      }
    }

    // Draw trail segments
    for (let segIdx = 0; segIdx < stateChanges.length - 1; segIdx++) {
      const startState = stateChanges[segIdx];
      const endState = stateChanges[segIdx + 1];

      ctx.strokeStyle = BEHAVIORAL_STATES[startState.state].color;
      ctx.lineWidth = 3;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.globalAlpha = 0.6;

      ctx.beginPath();
      let started = false;

      for (const point of pathPoints) {
        const pointTime = (point.timestamp - minTime) / 1000;
        if (pointTime >= startState.time && pointTime <= endState.time) {
          const cx = canvas.width / 2 + (point.x - (pageWidth || 0) / 2) * scale / (devicePixelRatio || 1);
          const cy = canvas.height / 2 + (point.y - (pageHeight || 0) / 2) * scale / (devicePixelRatio || 1);
          if (!started) {
            ctx.moveTo(cx, cy);
            started = true;
          } else {
            ctx.lineTo(cx, cy);
          }
        }
      }
      ctx.stroke();
    }

    ctx.globalAlpha = 1;

    // Draw current cursor position
    const lastPoint = pathPoints[pathPoints.length - 1];
    const cx = canvas.width / 2 + (lastPoint.x - (pageWidth || 0) / 2) * scale / (devicePixelRatio || 1);
    const cy = canvas.height / 2 + (lastPoint.y - (pageHeight || 0) / 2) * scale / (devicePixelRatio || 1);

    // Draw cursor glow
    const state = getStateAtTime(time);
    const stateColor = BEHAVIORAL_STATES[state].color;

    const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 20);
    gradient.addColorStop(0, stateColor + "80");
    gradient.addColorStop(1, stateColor + "00");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(cx, cy, 20, 0, Math.PI * 2);
    ctx.fill();

    // Draw cursor dot
    ctx.fillStyle = stateColor;
    ctx.beginPath();
    ctx.arc(cx, cy, 8, 0, Math.PI * 2);
    ctx.fill();

    // Draw cursor border
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();
  }, [mousePath, minTime, getStateAtTime, pageWidth, pageHeight, devicePixelRatio]);

  // Animation loop (with highlights mode support)
  // Use refs to avoid infinite re-renders from changing currentTime
  const playbackRef = useRef({
    isPlaying,
    currentTime,
    totalDuration,
    playbackSpeed,
    highlightsMode,
    highlights,
    currentHighlightIndex,
  });

  // Update ref when values change
  useEffect(() => {
    playbackRef.current = {
      isPlaying,
      currentTime,
      totalDuration,
      playbackSpeed,
      highlightsMode,
      highlights,
      currentHighlightIndex,
    };
  }, [isPlaying, currentTime, totalDuration, playbackSpeed, highlightsMode, highlights, currentHighlightIndex]);

  useEffect(() => {
    if (!playbackRef.current.isPlaying) return;

    let startTime: number | null = null;
    let lastTime = playbackRef.current.currentTime;

    const animate = (timestamp: number) => {
      if (startTime === null) startTime = timestamp;
      const elapsed = (timestamp - startTime) / 1000 * playbackRef.current.playbackSpeed;

      let newTime: number;
      const ref = playbackRef.current; // Capture current ref values

      if (ref.highlightsMode && ref.highlights.length > 0) {
        // Skip to highlights mode: play 3 seconds around each highlight
        const currentHighlight = ref.highlights[ref.currentHighlightIndex];
        const highlightStart = Math.max(0, currentHighlight.timestamp - 1.5);
        const highlightEnd = Math.min(ref.totalDuration, currentHighlight.timestamp + 1.5);

        newTime = Math.min(lastTime + elapsed, highlightEnd);

        // Move to next highlight when we finish this one
        if (newTime >= highlightEnd && ref.currentHighlightIndex < ref.highlights.length - 1) {
          const nextIdx = ref.currentHighlightIndex + 1;
          playbackRef.current.currentHighlightIndex = nextIdx;
          setCurrentHighlightIndex(nextIdx);
          const nextHighlight = ref.highlights[nextIdx];
          const nextStart = Math.max(0, nextHighlight.timestamp - 1.5);
          lastTime = nextStart;
          setCurrentTime(nextStart);
          startTime = timestamp; // Reset timing
          animationRef.current = requestAnimationFrame(animate);
          return;
        }

        if (newTime >= ref.totalDuration || ref.currentHighlightIndex >= ref.highlights.length - 1) {
          setIsPlaying(false);
          return;
        }
      } else {
        // Normal playback
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
  }, [isPlaying]); // Only depend on isPlaying state

  // Setup canvas size
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const resizeCanvas = () => {
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      // Redraw current frame
      const ctx = canvas.getContext("2d");
      if (ctx && playbackRef.current) {
        // Trigger a redraw by updating a forced ref
        drawFrame(playbackRef.current.currentTime);
      }
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    return () => window.removeEventListener("resize", resizeCanvas);
  }, [drawFrame]); // Only redraw when drawFrame changes (should be stable due to useCallback)

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
        setCurrentTime(t => Math.min(totalDuration, t + 5));
        setIsPlaying(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [totalDuration]);

  const togglePlay = () => setIsPlaying(p => !p);

  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = (parseFloat(e.target.value) / 100) * totalDuration;
    setCurrentTime(newTime);
    setCurrentState(getStateAtTime(newTime));
    if (!isPlaying) {
      drawFrame(newTime);
    }
  };

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

    for (let t = 0; t <= totalDuration; t += 0.5) {
      const state = getStateAtTime(t);
      if (state !== currentState) {
        segments.push({ start: segmentStart, end: t, state: currentState });
        currentState = state;
        segmentStart = t;
      }
    }
    segments.push({ start: segmentStart, end: totalDuration, state: currentState });

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
            {/* Share replay button */}
            <button
              onClick={() => {
                const shareUrl = `${window.location.origin}/dashboard/sessions/${sessionId}`;
                navigator.clipboard.writeText(shareUrl);
                // Brief visual feedback
                const btn = document.activeElement as HTMLButtonElement;
                if (btn) {
                  const originalText = btn.innerHTML;
                  btn.innerHTML = '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>';
                  setTimeout(() => btn.innerHTML = originalText, 1500);
                }
              }}
              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Copy link to this replay"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
              </svg>
            </button>
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
            <span className="font-medium text-gray-900">{formatTime(totalDuration || 0)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Data points:</span>
            <span className="font-medium text-gray-900">{mousePath.length}</span>
          </div>
          {currentState !== "neutral" && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Dominant state:</span>
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white"
                style={{ backgroundColor: BEHAVIORAL_STATES[currentState].color }}
              >
                {BEHAVIORAL_STATES[currentState].emoji} {BEHAVIORAL_STATES[currentState].label}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Session ID:</span>
            <span className="font-mono text-xs text-gray-600">{sessionId.slice(0, 8)}...</span>
          </div>
        </div>

        {/* Main content */}
        <div className="flex">
          {/* Replay canvas */}
          <div ref={containerRef} className="flex-1 bg-gray-100 relative" style={{ minHeight: 400 }}>
            <canvas ref={canvasRef} className="w-full h-full" />

            {/* State label overlay */}
            {currentState !== "neutral" && (
              <div
                className="absolute top-4 left-4 px-3 py-2 rounded-full text-sm font-medium text-white shadow-lg flex items-center gap-2"
                style={{ backgroundColor: BEHAVIORAL_STATES[currentState].color }}
              >
                <span>{BEHAVIORAL_STATES[currentState].emoji}</span>
                <span>{BEHAVIORAL_STATES[currentState].label}</span>
              </div>
            )}

            {/* Time display */}
            <div className="absolute bottom-20 left-4 px-3 py-2 bg-white rounded-lg shadow text-sm font-mono">
              {formatTime(currentTime)} / {formatTime(totalDuration)}
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
                <div>Duration: {formatTime(totalDuration || 0)}</div>
                <div>Points: {mousePath.length}</div>
                <div>Emotions: {emotions.length}</div>
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

        {/* Timeline scrubber with state bar and highlight markers */}
        <div className="px-6 py-4 bg-white border-t border-gray-200">
          {/* State timeline bar with highlight markers */}
          <div className="relative h-2 rounded-full overflow-hidden flex mb-3">
            {timelineSegments.map((seg, i) => (
              <div
                key={i}
                className="h-full"
                style={{
                  width: `${((seg.end - seg.start) / totalDuration) * 100}%`,
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
                style={{ left: `${(hl.timestamp / totalDuration) * 100}%` }}
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
                {/* Tooltip on hover */}
                <div className="absolute bottom-full mb-2 hidden group-hover:block whitespace-nowrap bg-gray-900 text-white text-xs px-2 py-1 rounded">
                  {hl.icon} {hl.description}
                </div>
              </div>
            ))}
          </div>

          {/* Scrubber with Skip to Highlights button */}
          <div className="flex items-center gap-4">
            <button
              onClick={togglePlay}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <PauseIcon /> : <PlayIcon />}
            </button>

            {/* Skip to Highlights button */}
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
                title={highlightsMode ? "Exit highlights mode" : "Play only key moments"}
              >
                <SkipForwardIcon />
                {highlightsMode ? `Highlight ${currentHighlightIndex + 1}/${highlights.length}` : "Skip to Highlights"}
              </button>
            )}

            <input
              type="range"
              min="0"
              max="100"
              value={(currentTime / totalDuration) * 100 || 0}
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
            {highlights.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">No key moments detected in this session.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
