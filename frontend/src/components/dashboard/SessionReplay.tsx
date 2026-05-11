"use client";

/**
 * rrweb Session Replay Player with Emotion Overlay
 *
 * Displays rrweb DOM recording with behavioral state color bar overlay.
 *
 * Privacy: Input fields are masked, elements with data-emoratest-mask are hidden.
 * Storage: Replay data is auto-deleted after 30 days (TODO: implement backend cleanup).
 */

import { useEffect, useRef, useState } from "react";

// rrweb-player types (simplified)
interface RRWebPlayer {
  replay: (events: unknown[], options?: { skipIndex?: number }) => void;
  getMetaData: () => { totalTime: number; startTime: number; endTime: number };
  getReplayIndex: () => number;
  play: () => void;
  pause: () => void;
  setSpeed: (speed: number) => void;
  goto: (timeOffset: number) => void;
  addStyle: (style: CSSStyleSheet) => void;
  addEventListener: (event: string, handler: () => void) => void;
  removeEventListener: (event: string, handler: () => void) => void;
}

interface EmotionEvent {
  timestamp: number;
  emotion: string;
  confidence?: number;
}

interface ReplayData {
  has_replay: boolean;
  events: unknown[];
  duration_ms: number;
  events_count: number;
  emotions: EmotionEvent[];
  page_url?: string;
}

const EMOTION_COLORS: Record<string, string> = {
  frustrated: "#EF4444",
  confused: "#F59E0B",
  hesitating: "#EAB308",
  engaged: "#22C55E",
  disengaged: "#6B7280",
};

const EMOTION_LABELS: Record<string, string> = {
  frustrated: "Frustrated",
  confused: "Confused",
  hesitating: "Hesitating",
  engaged: "Engaged",
  disengaged: "Disengaged",
};

interface SessionReplayProps {
  sessionId: string;
}

export function SessionReplay({ sessionId }: SessionReplayProps) {
  const [data, setData] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentEmotion, setCurrentEmotion] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalTime, setTotalTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<RRWebPlayer | null>(null);

  // Fetch replay data
  useEffect(() => {
    async function fetchReplay() {
      setLoading(true);
      setError(null);

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboard/sessions/${sessionId}/replay`,
          { credentials: "include" }
        );

        if (!res.ok) {
          throw new Error(`Failed to fetch replay: ${res.status}`);
        }

        const replayData: ReplayData = await res.json();
        setData(replayData);

        if (replayData.has_replay) {
          setTotalTime(replayData.duration_ms);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchReplay();
  }, [sessionId]);

  // Initialize rrweb-player
  useEffect(() => {
    if (!data?.has_replay || !containerRef.current || data.events.length === 0) {
      return;
    }

    // Dynamic import of rrweb-player
    async function initPlayer() {
      try {
        const rrwebPlayerModule = await import("rrweb-player");
        const rrwebPlayer = rrwebPlayerModule.default;

        if (!containerRef.current) return;

        // Create player instance
        const player = new rrwebPlayer({
          target: containerRef.current,
          props: {
            events: data!.events as any[],
            width: containerRef.current.offsetWidth,
            height: Math.max(400, Math.round(containerRef.current.offsetWidth * 9 / 16)),
            autoPlay: false,
            skipInactive: false,
            showController: true,
            mouseTail: {
              duration: 500,
              lineCap: "round",
              lineWidth: 2,
              strokeStyle: "#0E8FFF",
            },
          },
        });

        playerRef.current = player as unknown as RRWebPlayer;

        // Get total time
        const meta = player.getMetaData();
        setTotalTime(meta.totalTime);

        // Listen for time update to sync emotion overlay
        const updateTime = () => {
          if (playerRef.current) {
            const index = playerRef.current.getReplayIndex();
            // Approximate current time based on events
            if (data!.events[index] && typeof data!.events[index] === "object") {
              const event = data!.events[index] as { timestamp?: number };
              if (event.timestamp) {
                const eventTime = event.timestamp - ((data!.events[0] as { timestamp?: number })?.timestamp || 0);
                setCurrentTime(eventTime);
              }
            }
          }
        };

        player.addEventListener("update", updateTime);

        return () => {
          // Note: rrweb-player doesn't have removeEventListener in its type
          // The event listener will be cleaned up when the component unmounts
        };
      } catch (err) {
        console.error("Failed to load rrweb-player:", err);
        setError("Failed to load replay player");
      }
    }

    const cleanup = initPlayer();

    return () => {
      cleanup.then((fn) => fn?.()).catch(() => {});
    };
  }, [data?.has_replay, data?.events]);

  // Update current emotion based on playback time
  useEffect(() => {
    if (!data?.emotions || data.emotions.length === 0) {
      return;
    }

    // Find the emotion that matches current time
    const baseTime = data.emotions[0]?.timestamp || 0;
    const currentTimestamp = baseTime + currentTime / 1000;

    // Find most recent emotion before current time
    let matchedEmotion: string | null = null;
    for (const emo of data.emotions) {
      if (emo.timestamp <= currentTimestamp) {
        matchedEmotion = emo.emotion;
      } else {
        break;
      }
    }

    setCurrentEmotion(matchedEmotion);
  }, [currentTime, data?.emotions]);

  // Playback controls
  function togglePlay() {
    if (!playerRef.current) return;

    if (isPlaying) {
      playerRef.current.pause();
    } else {
      playerRef.current.play();
    }
    setIsPlaying(!isPlaying);
  }

  function setSpeed(speed: number) {
    if (!playerRef.current) return;
    playerRef.current.setSpeed(speed);
    setPlaybackSpeed(speed);
  }

  function skipToFrustration() {
    if (!data?.emotions || !playerRef.current) return;

    const frustrationEvent = data.emotions.find((e) => e.emotion === "frustrated");
    if (!frustrationEvent) return;

    const baseTime = data.emotions[0]?.timestamp || 0;
    const offset = (frustrationEvent.timestamp - baseTime) * 1000;
    playerRef.current.goto(offset);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
        <div className="text-gray-500">Loading replay...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-red-50 rounded-lg border border-red-200">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!data?.has_replay) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg border border-gray-200">
        <div className="text-gray-500">No replay available for this session</div>
      </div>
    );
  }

  // Edge case: Session too short (< 2 seconds)
  if (data.duration_ms < 2000) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg border border-gray-200">
        <div className="text-gray-500">Session too short for replay (less than 2 seconds)</div>
      </div>
    );
  }

  // Edge case: Too many events warning
  const showEventWarning = data.events_count > 5000;

  // Build emotion timeline
  const emotionTimeline = data.emotions.map((emo, idx) => {
    const baseTime = data.emotions[0]?.timestamp || 0;
    const offsetPercent = ((emo.timestamp - baseTime) / (totalTime / 1000)) * 100;
    const color = EMOTION_COLORS[emo.emotion] || "#999";

    return (
      <div
        key={idx}
        className="absolute top-0 bottom-0 w-0.5"
        style={{
          left: `${Math.min(100, Math.max(0, offsetPercent))}%`,
          backgroundColor: color,
        }}
        title={`${EMOTION_LABELS[emo.emotion] || emo.emotion} at ${new Date(emo.timestamp * 1000).toLocaleTimeString()}`}
      />
    );
  });

  // Key moments (frustration spikes, state changes)
  const keyMoments = data.emotions
    .filter((e, i) => {
      if (e.emotion === "frustrated") return true;
      // State changes
      if (i > 0 && data.emotions[i - 1]?.emotion !== e.emotion) return true;
      return false;
    })
    .map((emo, idx) => {
      const baseTime = data.emotions[0]?.timestamp || 0;
      const offset = (emo.timestamp - baseTime) * 1000;
      return (
        <button
          key={idx}
          onClick={() => playerRef.current?.goto(offset)}
          className="px-3 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50 transition"
        >
          <span className="font-medium" style={{ color: EMOTION_COLORS[emo.emotion] }}>
            {EMOTION_LABELS[emo.emotion] || emo.emotion}
          </span>
          <span className="ml-2 text-gray-500">
            {new Date(offset).toLocaleTimeString([], { minute: "2-digit", second: "2-digit" })}
          </span>
        </button>
      );
    });

  return (
    <div className="space-y-4">
      {/* Warning for large event counts */}
      {showEventWarning && (
        <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>Large replay ({data.events_count.toLocaleString()} events) — playback may be slow</span>
        </div>
      )}

      {/* Player container */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <div ref={containerRef} className="w-full" />

        {/* Emotion overlay bar */}
        {data.emotions.length > 0 && (
          <div className="relative h-2 bg-gray-200" style={{ position: "relative" }}>
            {emotionTimeline}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between bg-white border rounded-lg p-4">
        <div className="flex items-center gap-4">
          {/* Play/Pause */}
          <button
            onClick={togglePlay}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            {isPlaying ? "Pause" : "Play"}
          </button>

          {/* Speed controls */}
          <div className="flex gap-1">
            {[1, 2, 4].map((speed) => (
              <button
                key={speed}
                onClick={() => setSpeed(speed)}
                className={`px-3 py-1 rounded text-sm ${
                  playbackSpeed === speed
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>

          {/* Skip to frustration */}
          {data.emotions.some((e) => e.emotion === "frustrated") && (
            <button
              onClick={skipToFrustration}
              className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition text-sm"
            >
              Skip to Frustration
            </button>
          )}
        </div>

        {/* Current emotion badge */}
        {currentEmotion && (
          <div
            className="px-4 py-2 rounded-full text-white text-sm font-medium"
            style={{ backgroundColor: EMOTION_COLORS[currentEmotion] || "#999" }}
          >
            {EMOTION_LABELS[currentEmotion] || currentEmotion}
          </div>
        )}

        {/* Session info */}
        <div className="text-sm text-gray-500">
          <div>Duration: {((totalTime || 0) / 1000).toFixed(1)}s</div>
          {data.page_url && (
            <div className="truncate max-w-xs">{data.page_url}</div>
          )}
        </div>
      </div>

      {/* Key moments */}
      {keyMoments.length > 0 && (
        <div className="bg-white border rounded-lg p-4">
          <h3 className="font-semibold mb-3 text-gray-700">Key Moments</h3>
          <div className="flex flex-wrap gap-2">
            {keyMoments}
          </div>
        </div>
      )}
    </div>
  );
}
