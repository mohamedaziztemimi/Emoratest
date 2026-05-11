"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import Spinner from "@/components/ui/Spinner";
import { fetchSessionReplay, type SessionReplayResponse, type MousePathPoint, type EmotionEventOut } from "@/lib/api";

interface ReplayViewerProps {
  sessionId: string;
}

// Behavioral State Color Mapping (5 states refactored from 8 emotions)
const EMOTION_COLORS: Record<string, { hex: string; rgba: string; emoji: string }> = {
  frustrated: { hex: "#EF4444", rgba: "rgba(239, 68, 68,", emoji: "😤" },  // red - rage clicks, erratic movement
  confused: { hex: "#F59E0B", rgba: "rgba(245, 158, 11,", emoji: "😕" },    // amber - back-and-forth scrolling
  hesitating: { hex: "#EAB308", rgba: "rgba(234, 179, 8,", emoji: "🤔" },  // yellow - hovering near CTAs
  engaged: { hex: "#22C55E", rgba: "rgba(34, 197, 94,", emoji: "😊" },     // green - steady movement, completing actions
  disengaged: { hex: "#6B7280", rgba: "rgba(107, 114, 128,", emoji: "😴" },  // gray - inactivity, fast scroll
  neutral: { hex: "#9CA3AF", rgba: "rgba(156, 163, 175,", emoji: "😐" },     // fallback
};

const REPLAY_COLORS = {
  background: "#F5F6FA",
  grid: "#E5E7EB",
};

export function ReplayViewer({ sessionId }: ReplayViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const [data, setData] = useState<SessionReplayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [screenshotLoaded, setScreenshotLoaded] = useState(false);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isDragging, setIsDragging] = useState(false);

  // Scale state
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  // Map emotions to mouse path points
  const mousePathWithEmotions = useMemo(() => {
    if (!data?.mouse_path || data.mouse_path.length === 0) return [];

    const emotions = data.emotions || [];
    if (emotions.length === 0) {
      // No emotions - return all points as neutral
      return data.mouse_path.map(point => ({
        ...point,
        emotion: "neutral" as const,
        emotionData: null
      }));
    }

    // Sort emotions by timestamp
    const sortedEmotions = [...emotions].sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // Map each mouse path point to the closest emotion by timestamp
    return data.mouse_path.map(point => {
      const pointTime = point.timestamp;

      // Find the emotion with closest timestamp
      let closestEmotion: EmotionEventOut | null = null;
      let minDiff = Infinity;

      for (const emotion of sortedEmotions) {
        const emotionTime = new Date(emotion.timestamp).getTime();
        const diff = Math.abs(emotionTime - pointTime);

        if (diff < minDiff) {
          minDiff = diff;
          closestEmotion = emotion;
        }
      }

      // If closest emotion is within 5 seconds, use it
      if (closestEmotion && minDiff < 5000) {
        return {
          ...point,
          emotion: closestEmotion.primary_emotion,
          emotionData: closestEmotion
        };
      }

      return {
        ...point,
        emotion: "neutral" as const,
        emotionData: null
      };
    });
  }, [data]);

  // Get current emotion for the cursor position
  const currentEmotion = mousePathWithEmotions[currentIndex]?.emotion || "neutral";

  // Fetch replay data
  useEffect(() => {
    async function loadReplay() {
      try {
        setLoading(true);
        setError(null);
        const replay = await fetchSessionReplay(sessionId);
        setData(replay);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load replay");
      } finally {
        setLoading(false);
      }
    }
    loadReplay();
  }, [sessionId]);

  // Skip screenshot loading delay for auth-protected pages
  useEffect(() => {
    if (!data?.page_url) return;

    const authProtectedPaths = ["/dashboard", "/login", "/signup", "/settings", "/admin", "/account", "/auth"];
    const isAuthProtected = authProtectedPaths.some(path => {
      try {
        const url = new URL(data.page_url);
        return url.pathname.includes(path);
      } catch {
        return data.page_url.includes(path);
      }
    });

    if (isAuthProtected) {
      setScreenshotLoaded(false);
    }
  }, [data]);

  // Calculate scale to fit canvas
  useEffect(() => {
    if (!data?.mouse_path || data.mouse_path.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.parentElement?.getBoundingClientRect();
    if (!rect) return;

    const maxWidth = rect.width - 40; // padding
    const maxHeight = 500; // max height

    const pageWidth = data.page_width || 1920;
    const pageHeight = data.page_height || 1080;

    const scaleX = maxWidth / pageWidth;
    const scaleY = maxHeight / pageHeight;
    const newScale = Math.min(scaleX, scaleY, 1); // Don't scale up

    setScale(newScale);
  }, [data]);

  // Animation loop using requestAnimationFrame
  useEffect(() => {
    if (!isPlaying || !data?.mouse_path || data.mouse_path.length === 0) return;

    const points = data.mouse_path;
    let lastTimestamp = points[currentIndex]?.timestamp || 0;
    let startTime = performance.now();

    function animate(currentTime: number) {
      const elapsed = currentTime - startTime;
      const adjustedElapsed = elapsed * playbackSpeed;

      // Find the current index based on elapsed time
      let newIndex = currentIndex;
      for (let i = newIndex; i < points.length; i++) {
        if (points[i].timestamp - lastTimestamp > adjustedElapsed) {
          break;
        }
        newIndex = i;
      }

      if (newIndex >= points.length - 1) {
        // End of replay
        setIsPlaying(false);
        setCurrentIndex(points.length - 1);
        return;
      }

      setCurrentIndex(newIndex);
      animationRef.current = requestAnimationFrame(animate);
    }

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, currentIndex, data, playbackSpeed]);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || mousePathWithEmotions.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas size
    const containerWidth = canvas.parentElement?.clientWidth || 800;
    const canvasWidth = containerWidth - 40;
    const canvasHeight = 500;

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    // Clear canvas (transparent to show screenshot behind)
    ctx.fillStyle = screenshotLoaded ? "transparent" : REPLAY_COLORS.background;
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Draw grid only if no screenshot loaded
    if (!screenshotLoaded) {
      ctx.strokeStyle = REPLAY_COLORS.grid;
      ctx.lineWidth = 1;
      const gridSize = 50 * scale;

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

      // Draw page URL at top (only when no screenshot)
      ctx.fillStyle = "#6B7280";
      ctx.font = "12px sans-serif";
      ctx.fillText(data?.page_url || "Unknown page", 10, 20);
    }

    // Draw trail with emotion colors (last 50 points before current)
    const trailStart = Math.max(0, currentIndex - 50);
    const trailPoints = mousePathWithEmotions.slice(trailStart, currentIndex + 1);

    // Draw trail in segments by emotion
    for (let i = 0; i < trailPoints.length - 1; i++) {
      const point = trailPoints[i];
      const nextPoint = trailPoints[i + 1];
      const emotionColor = EMOTION_COLORS[point.emotion] || EMOTION_COLORS.neutral;

      const x1 = point.x * scale + offset.x;
      const y1 = point.y * scale + offset.y;
      const x2 = nextPoint.x * scale + offset.x;
      const y2 = nextPoint.y * scale + offset.y;

      // Calculate opacity based on position in trail (newer = more opaque)
      const opacity = (i / trailPoints.length) * 0.6 + 0.2;

      ctx.beginPath();
      ctx.strokeStyle = emotionColor.rgba + opacity + ")";
      ctx.lineWidth = 2;
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }

    // Draw cursor at current position with emotion color
    const currentPoint = mousePathWithEmotions[currentIndex];
    if (currentPoint) {
      const cursorX = currentPoint.x * scale + offset.x;
      const cursorY = currentPoint.y * scale + offset.y;
      const emotionColor = EMOTION_COLORS[currentEmotion] || EMOTION_COLORS.neutral;

      // Draw glow with emotion color
      const gradient = ctx.createRadialGradient(cursorX, cursorY, 0, cursorX, cursorY, 12);
      gradient.addColorStop(0, emotionColor.rgba + "0.5)");
      gradient.addColorStop(1, emotionColor.rgba + "0)");
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(cursorX, cursorY, 12, 0, Math.PI * 2);
      ctx.fill();

      // Draw cursor dot with emotion color
      ctx.fillStyle = emotionColor.hex;
      ctx.beginPath();
      ctx.arc(cursorX, cursorY, 6, 0, Math.PI * 2);
      ctx.fill();

      // Draw white border around cursor
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw emotion label near cursor
      if (currentEmotion !== "neutral") {
        const label = `${emotionColor.emoji} ${currentEmotion}`;
        ctx.font = "11px sans-serif";
        const textWidth = ctx.measureText(label).width;
        const padding = 4;

        // Label background
        ctx.fillStyle = emotionColor.hex + "dd";
        ctx.beginPath();
        ctx.roundRect(cursorX + 15, cursorY - 10, textWidth + padding * 2, 20, 4);
        ctx.fill();

        // Label text
        ctx.fillStyle = "#ffffff";
        ctx.fillText(label, cursorX + 15 + padding, cursorY + 4);
      }
    }
  }, [mousePathWithEmotions, currentIndex, scale, offset, currentEmotion, data, screenshotLoaded]);

  // Handlers
  const handleTogglePlay = () => {
    if (currentIndex >= (data?.mouse_path?.length || 0) - 1) {
      setCurrentIndex(0);
    }
    setIsPlaying(!isPlaying);
  };

  const handleScrubberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newIndex = parseInt(e.target.value);
    setCurrentIndex(newIndex);
    setIsPlaying(false);
  };

  const formatTimestamp = (timestamp: number) => {
    const seconds = Math.floor(timestamp / 1000);
    const ms = timestamp % 1000;
    return `${seconds}.${ms.toString().padStart(3, "0")}s`;
  };

  const currentTimestamp = data?.mouse_path?.[currentIndex]?.timestamp || 0;
  const totalDuration = data?.mouse_path?.length
    ? data.mouse_path[data.mouse_path.length - 1].timestamp - data.mouse_path[0].timestamp
    : 0;

  // Generate emotion timeline segments for the scrubber (must be before early returns)
  const emotionTimelineSegments = useMemo(() => {
    if (mousePathWithEmotions.length === 0) return [];

    const segments: { start: number; end: number; emotion: string; color: string }[] = [];
    let currentSegment: { start: number; emotion: string; color: string } | null = null;

    for (let i = 0; i < mousePathWithEmotions.length; i++) {
      const point = mousePathWithEmotions[i];
      const emotionColor = EMOTION_COLORS[point.emotion] || EMOTION_COLORS.neutral;

      if (!currentSegment || currentSegment.emotion !== point.emotion) {
        if (currentSegment) {
          segments.push({ ...currentSegment, end: i - 1 });
        }
        currentSegment = { start: i, emotion: point.emotion, color: emotionColor.hex };
      }
    }

    if (currentSegment) {
      segments.push({ ...currentSegment, end: mousePathWithEmotions.length - 1 });
    }

    return segments;
  }, [mousePathWithEmotions]);

  if (loading) {
    return (
      <Card>
        <CardBody className="flex items-center justify-center py-12">
          <Spinner />
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardBody className="py-12 text-center">
          <p className="text-red-500">Error loading replay: {error}</p>
        </CardBody>
      </Card>
    );
  }

  if (!data?.has_replay || !data.mouse_path || data.mouse_path.length === 0) {
    return (
      <Card>
        <CardBody className="py-12 text-center text-gray-500">
          <p>No replay data available for this session.</p>
        </CardBody>
      </Card>
    );
  }

  // Handle very short sessions
  if (mousePathWithEmotions.length < 5) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Session Replay</h3>
        </CardHeader>
        <CardBody>
          <p className="text-gray-500 mb-4">
            This session has limited replay data ({mousePathWithEmotions.length} points).
          </p>
          <div className="border rounded-lg p-4 bg-gray-50">
            <canvas ref={canvasRef} className="w-full" style={{ height: 200 }} />
          </div>
        </CardBody>
      </Card>
    );
  }

  // Calculate timeline percentages for emotion bar
  const timelinePercent = mousePathWithEmotions.length > 0
    ? (currentIndex / (mousePathWithEmotions.length - 1)) * 100
    : 0;

  // Build thum.io screenshot URL - skip for auth-protected pages
  const pageUrl = data?.page_url || "";
  const authProtectedPaths = ["/dashboard", "/login", "/signup", "/settings", "/admin", "/account", "/auth"];
  const isAuthProtected = authProtectedPaths.some(path => {
    try {
      const url = new URL(pageUrl);
      return url.pathname.includes(path);
    } catch {
      // If URL parsing fails, check string directly
      return pageUrl.includes(path);
    }
  });

  const screenshotUrl = pageUrl && !isAuthProtected
    ? `https://image.thum.io/get/width/1440/crop/900/${encodeURIComponent(pageUrl)}`
    : null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Session Replay</h3>
          <div className="text-sm text-gray-500">
            {data?.page_title || data?.page_url}
          </div>
        </div>
      </CardHeader>
      <CardBody>
        <div className="border rounded-lg overflow-hidden bg-white relative">
          {/* Screenshot background behind canvas */}
          {screenshotUrl && (
            <img
              src={screenshotUrl}
              alt="Page screenshot"
              className="absolute top-0 left-0 w-full h-full object-cover"
              style={{
                opacity: 0.85,
                zIndex: 0,
                pointerEvents: "none"
              }}
              onLoad={() => setScreenshotLoaded(true)}
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
                setScreenshotLoaded(false);
              }}
            />
          )}
          {/* Canvas with cursor trail on top */}
          <canvas
            ref={canvasRef}
            className="w-full relative"
            style={{ zIndex: 1 }}
          />
        </div>

        {/* Controls */}
        <div className="mt-4 space-y-4">
          {/* Progress bar / scrubber with emotion timeline */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>{formatTimestamp(currentTimestamp - mousePathWithEmotions[0].timestamp)}</span>
              <span>{formatTimestamp(totalDuration)}</span>
            </div>

            {/* Emotion timeline bar */}
            <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
              {emotionTimelineSegments.map((seg, idx) => {
                const startPct = (seg.start / (mousePathWithEmotions.length - 1)) * 100;
                const endPct = (seg.end / (mousePathWithEmotions.length - 1)) * 100;
                const width = endPct - startPct;

                return (
                  <div
                    key={idx}
                    className="absolute top-0 h-full"
                    style={{
                      left: `${startPct}%`,
                      width: `${width}%`,
                      backgroundColor: seg.color,
                    }}
                    title={`${seg.emotion}: ${seg.start} - ${seg.end}`}
                  />
                );
              })}

              {/* Current position indicator */}
              <div
                className="absolute top-0 h-full w-0.5 bg-white shadow"
                style={{ left: `${timelinePercent}%` }}
              />
            </div>

            <input
              type="range"
              min="0"
              max={mousePathWithEmotions.length - 1}
              value={currentIndex}
              onChange={handleScrubberChange}
              onMouseDown={() => setIsDragging(true)}
              onMouseUp={() => setIsDragging(false)}
              onTouchStart={() => setIsDragging(true)}
              onTouchEnd={() => setIsDragging(false)}
              className="w-full h-2 bg-transparent rounded-lg appearance-none cursor-pointer absolute top-0 opacity-0"
              style={{ marginTop: "-0.5rem" }}
            />
          </div>

          {/* Playback controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={handleTogglePlay}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                {isPlaying ? (
                  <>
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M5 4h3v12H5V4zm7 0h3v12h-3V4z" />
                    </svg>
                    Pause
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M6 4l10 6-10 6V4z" />
                    </svg>
                    Play
                  </>
                )}
              </button>

              <span className="text-sm text-gray-500">
                Point {currentIndex + 1} of {mousePathWithEmotions.length}
              </span>

              {/* Current emotion indicator */}
              {currentEmotion !== "neutral" && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                  style={{ backgroundColor: EMOTION_COLORS[currentEmotion]?.hex + "20", color: EMOTION_COLORS[currentEmotion]?.hex }}>
                  {EMOTION_COLORS[currentEmotion]?.emoji} {currentEmotion}
                </span>
              )}
            </div>

            {/* Speed controls */}
            <div className="flex items-center gap-1">
              <span className="text-sm text-gray-500 mr-2">Speed:</span>
              {[1, 2, 4].map((speed) => (
                <button
                  key={speed}
                  onClick={() => setPlaybackSpeed(speed)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    playbackSpeed === speed
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </div>

          {/* Emotion legend */}
          <div className="pt-2 border-t">
            <p className="text-xs text-gray-500 mb-2">Emotion colors:</p>
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              {Object.entries(EMOTION_COLORS).map(([emotion, { hex, emoji }]) => (
                <div key={emotion} className="flex items-center gap-1.5 text-xs">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: hex }}
                  />
                  <span className="text-gray-600">
                    {emoji} {emotion}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Session info */}
        {data?.duration_seconds && (
          <div className="mt-4 pt-4 border-t text-sm text-gray-500">
            Duration: {Math.floor(data.duration_seconds / 60)}m {data.duration_seconds % 60}s •{" "}
            {mousePathWithEmotions.length} data points
          </div>
        )}
      </CardBody>
    </Card>
  );
}
