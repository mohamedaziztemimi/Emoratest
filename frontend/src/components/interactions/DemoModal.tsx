/* ────────────────────────────────────────────────────────
   DemoModal - Full-screen demo video modal with controls
   ──────────────────────────────────────────────────────── */

"use client";

import { clsx } from "clsx";
import { GlassCard } from "@/components/ui";
import { useEffect, useRef, useState } from "react";

export interface DemoModalProps {
  isOpen?: boolean;
  videoSrc?: string;
  onClose?: () => void;
}

const STATS = [
  { label: "+32% lift", gradient: "from-[var(--et-blue)] to-[var(--et-purple)]" },
  { label: "2min setup", gradient: "from-[var(--et-delight)] to-emerald-400" },
  { label: "85% accuracy", gradient: "from-[var(--et-blue)] to-cyan-400" },
];

export function DemoModal({ isOpen: controlledOpen, videoSrc = "https://www.youtube.com/embed/dQw4w9WgXcQ", onClose }: DemoModalProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [videoPlaying, setVideoPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(60);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const isOpen = controlledOpen ?? internalOpen;

  // Handle custom event for "open-demo-modal"
  useEffect(() => {
    const handleOpen = () => setInternalOpen(true);
    window.addEventListener("open-demo-modal", handleOpen);
    return () => window.removeEventListener("open-demo-modal", handleOpen);
  }, []);

  // Scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Keyboard ESC
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        handleClose();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen]);

  // Video controls simulation (for iframe we can't get actual progress, so simulate)
  useEffect(() => {
    if (isOpen && !videoPlaying) {
      // Simulate progress animation
      const interval = setInterval(() => {
        setProgress((p) => (p >= 100 ? 0 : p + 0.5));
        setCurrentTime((t) => (t >= duration ? 0 : t + 0.3));
      }, 300);
      return () => clearInterval(interval);
    }
  }, [isOpen, videoPlaying, duration]);

  const handleClose = () => {
    setInternalOpen(false);
    setVideoPlaying(false);
    setProgress(0);
    setCurrentTime(0);
    onClose?.();
  };

  const togglePlay = () => {
    setVideoPlaying(!videoPlaying);
    // For HTML5 video, we'd toggle videoRef.current?.play/pause
    // For iframe, we'd use YouTube API
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = ((e.clientX - rect.left) / rect.width) * 100;
    setProgress(percent);
    setCurrentTime((percent / 100) * duration);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{
        backgroundColor: "rgba(0, 0, 0, 0.85)",
        backdropFilter: "blur(8px)",
      }}
      onClick={handleClose}
    >
      <GlassCard
        glow="blue"
        className={clsx(
          "relative w-full max-w-[860px]",
          "transition-all duration-250 ease-out",
          isOpen ? "scale-100 opacity-100" : "scale-90 opacity-0"
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute -top-3 -right-3 z-10 w-8 h-8 rounded-full bg-[var(--et-bg-800)] border border-[var(--et-border)] text-[var(--et-text-secondary)] hover:text-[var(--et-text-primary)] hover:border-[var(--et-blue)] transition-all duration-200 flex items-center justify-center"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Video container */}
        <div className="relative aspect-video bg-[var(--et-bg-900)] rounded-[var(--et-radius-md)] overflow-hidden group">
          {videoSrc.includes("youtube") || videoSrc.includes("youtu.be") ? (
            <iframe
              ref={iframeRef}
              src={`${videoSrc}${isOpen ? "?autoplay=1" : ""}`}
              className="w-full h-full"
              allow="autoplay; fullscreen"
              allowFullScreen
            />
          ) : (
            <video
              ref={videoRef}
              src={videoSrc}
              className="w-full h-full"
              controls
              autoPlay={isOpen}
            />
          )}

          {/* Custom controls overlay */}
          <div
            className={clsx(
              "absolute bottom-0 left-0 right-0",
              "bg-gradient-to-t from-black/80 to-transparent",
              "p-4",
              "opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            )}
          >
            {/* Play/pause button */}
            <div className="flex items-center gap-4">
              <button
                onClick={togglePlay}
                className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
              >
                {videoPlaying ? (
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>

              {/* Progress bar */}
              <div
                className="flex-1 h-1.5 bg-white/20 rounded-full cursor-pointer group/progress"
                onClick={handleProgressClick}
              >
                <div
                  className="h-full bg-gradient-to-r from-[var(--et-blue)] to-[var(--et-purple)] rounded-full relative transition-all duration-100"
                  style={{ width: `${progress}%` }}
                >
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover/progress:opacity-100 transition-opacity" />
                </div>
              </div>

              {/* Time display */}
              <span className="text-xs text-white/80 font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>
          </div>
        </div>

        {/* Stats badges */}
        <div className="flex items-center justify-center gap-6 mt-6">
          {STATS.map((stat, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--et-bg-800)]/50 border border-[var(--et-border)]"
            >
              <div className="w-2 h-2 rounded-full bg-gradient-to-br from-[var(--et-blue)] to-[var(--et-purple)]" />
              <span className={clsx("text-sm font-bold bg-gradient-to-r", stat.gradient, "bg-clip-text text-transparent")}>
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}

// Convenience function to open the modal
export function openDemoModal() {
  window.dispatchEvent(new CustomEvent("open-demo-modal"));
}
