/* ────────────────────────────────────────────────
   HeroHeatmap - Animated heatmap demo (light mode)
   ──────────────────────────────────────────────── */

"use client";

import { useEffect, useRef } from "react";

// Emotion types with colors
const EMOTIONS = [
  { type: "confusion", color: "#F59E0B", label: "Confusion" },
  { type: "frustration", color: "#EF4444", label: "Frustration" },
  { type: "engaged", color: "#10B981", label: "Engaged" },
  { type: "disengaged", color: "#6B7280", label: "Disengaged" },
] as const;

type EmotionType = typeof EMOTIONS[number]["type"];

interface Dot {
  x: number;
  y: number;
  vx: number;
  vy: number;
  emotion: EmotionType;
  radius: number;
  opacity: number;
  pulsePhase: number;
}

interface EmotionEvent {
  x: number;
  y: number;
  emotion: EmotionType;
  label: string;
  startTime: number;
}

// Wireframe element positions (normalized 0-1)
const WIREFRAME_ELEMENTS = [
  { type: "header", x: 0, y: 0, w: 1, h: 0.12 },
  { type: "product", x: 0.1, y: 0.15, w: 0.8, h: 0.35 },
  { type: "form", x: 0.1, y: 0.55, w: 0.35, h: 0.12 },
  { type: "form", x: 0.1, y: 0.69, w: 0.35, h: 0.12 },
  { type: "cta", x: 0.1, y: 0.84, w: 0.25, h: 0.08 },
];

export function HeroHeatmap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dotsRef = useRef<Dot[]>([]);
  const emotionEventRef = useRef<EmotionEvent | null>(null);
  const animationFrameRef = useRef<number>();
  const lastTimeRef = useRef<number>(0);

  const createDot = (): Dot => ({
    x: Math.random() * 600,
    y: Math.random() * 360,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    emotion: EMOTIONS[Math.floor(Math.random() * EMOTIONS.length)].type,
    radius: 6 + Math.random() * 4,
    opacity: 0.5 + Math.random() * 0.3,
    pulsePhase: Math.random() * Math.PI * 2,
  });

  useEffect(() => {
    dotsRef.current = Array.from({ length: 50 }, () => createDot());
  }, []);

  const triggerEmotionEvent = () => {
    const emotion = EMOTIONS[Math.floor(Math.random() * EMOTIONS.length)];
    const labels = [
      `${emotion.label} detected → 68% drop-off`,
      `${emotion.label} spike on CTA`,
      `${emotion.label} on checkout form`,
      `${emotion.label} at pricing step`,
    ];
    emotionEventRef.current = {
      x: 100 + Math.random() * 400,
      y: 80 + Math.random() * 200,
      emotion: emotion.type,
      label: labels[Math.floor(Math.random() * labels.length)],
      startTime: Date.now(),
    };

    setTimeout(() => {
      emotionEventRef.current = null;
    }, 2000);
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const emotionEventInterval = setInterval(triggerEmotionEvent, 3000);

    const render = (timestamp: number) => {
      const delta = timestamp - lastTimeRef.current;

      if (delta < 16) {
        animationFrameRef.current = requestAnimationFrame(render);
        return;
      }

      lastTimeRef.current = timestamp;

      // Light mode background
      ctx.fillStyle = "#FAFAFA";
      ctx.fillRect(0, 0, 600, 360);

      // Draw wireframe elements
      ctx.strokeStyle = "#E5E7EB";
      ctx.lineWidth = 1;

      WIREFRAME_ELEMENTS.forEach((el) => {
        const x = el.x * 600;
        const y = el.y * 360;
        const w = el.w * 600;
        const h = el.h * 360;

        ctx.strokeRect(x, y, w, h);

        ctx.fillStyle = "#9CA3AF";
        ctx.font = "10px Inter, sans-serif";
        ctx.fillText(el.type, x + 4, y + 12);
      });

      // Draw CTA button
      ctx.fillStyle = "#E5E7EB";
      ctx.fillRect(60, 300, 90, 30);
      ctx.fillStyle = "#6B7280";
      ctx.font = "bold 11px Inter, sans-serif";
      ctx.fillText("Buy Now", 80, 319);

      // Update and draw dots
      dotsRef.current.forEach((dot) => {
        dot.x += dot.vx;
        dot.y += dot.vy;

        if (dot.x < 0 || dot.x > 600) dot.vx *= -1;
        if (dot.y < 0 || dot.y > 360) dot.vy *= -1;

        dot.x = Math.max(0, Math.min(600, dot.x));
        dot.y = Math.max(0, Math.min(360, dot.y));

        dot.pulsePhase += 0.02;

        const emotion = EMOTIONS.find((e) => e.type === dot.emotion);
        if (!emotion) return;

        const gradient = ctx.createRadialGradient(dot.x, dot.y, 0, dot.x, dot.y, dot.radius * 2);
        gradient.addColorStop(0, emotion.color + Math.floor(dot.opacity * 255).toString(16).padStart(2, "0"));
        gradient.addColorStop(1, emotion.color + "00");

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(dot.x, dot.y, dot.radius * 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = emotion.color + Math.floor(dot.opacity * 200).toString(16).padStart(2, "0");
        ctx.beginPath();
        ctx.arc(dot.x, dot.y, dot.radius * 0.5, 0, Math.PI * 2);
        ctx.fill();
      });

      // Draw emotion event
      if (emotionEventRef.current) {
        const event = emotionEventRef.current;
        const elapsed = Date.now() - event.startTime;
        const progress = elapsed / 2000;

        if (progress < 1) {
          const emotion = EMOTIONS.find((e) => e.type === event.emotion);
          if (emotion) {
            const ringRadius = 8 + progress * 40;
            const ringOpacity = 1 - progress;

            ctx.strokeStyle = emotion.color + Math.floor(ringOpacity * 255).toString(16).padStart(2, "0");
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(event.x, event.y, ringRadius, 0, Math.PI * 2);
            ctx.stroke();

            const ringRadius2 = 8 + ((progress + 0.3) % 1) * 40;
            const ringOpacity2 = 1 - ((progress + 0.3) % 1);

            ctx.strokeStyle = emotion.color + Math.floor(ringOpacity2 * 100).toString(16).padStart(2, "0");
            ctx.beginPath();
            ctx.arc(event.x, event.y, ringRadius2, 0, Math.PI * 2);
            ctx.stroke();

            const tooltipPadding = 8;
            const tooltipWidth = ctx.measureText(event.label).width + tooltipPadding * 2;
            const tooltipHeight = 28;
            const tooltipX = event.x - tooltipWidth / 2;
            const tooltipY = event.y - 40;

            ctx.fillStyle = emotion.color + "E6";
            ctx.beginPath();
            ctx.roundRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight, 4);
            ctx.fill();

            ctx.fillStyle = "#FFFFFF";
            ctx.font = "11px Inter, sans-serif";
            ctx.fillText(event.label, tooltipX + tooltipPadding, tooltipY + 18);
          }
        }
      }

      animationFrameRef.current = requestAnimationFrame(render);
    };

    animationFrameRef.current = requestAnimationFrame(render);

    return () => {
      clearInterval(emotionEventInterval);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={600}
        height={360}
        className="w-full rounded-2xl border border-gray-200 shadow-sm bg-white"
        style={{ aspectRatio: "600/360" }}
      />

      <div className="mt-3 flex items-center justify-center gap-3 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-[#EF4444]" />
          Frustrated
        </span>
        <span className="w-1 h-1 bg-gray-300 rounded-full" />
        <span className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" />
          Confused
        </span>
        <span className="w-1 h-1 bg-gray-300 rounded-full" />
        <span className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
          Engaged
        </span>
        <span className="w-1 h-1 bg-gray-300 rounded-full" />
        <span className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-[#6B7280]" />
          Disengaged
        </span>
      </div>
    </div>
  );
}
