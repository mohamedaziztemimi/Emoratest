"use client";

import { useEffect, useRef, memo } from "react";

export type HeatmapType = "click" | "scroll" | "move";

export interface HeatmapPoint {
  x: number;
  y: number;
  value: number;
  emotion?: string;
}

export interface HeatmapCanvasProps {
  data: HeatmapPoint[];
  type: HeatmapType;
  width: number;
  height: number;
  pageScreenshot?: string;
}

const TYPE_CONFIG: Record<HeatmapType, { radius: number; opacity: number; color: string }> = {
  click: { radius: 30, opacity: 0.5, color: "#EF4444" },
  scroll: { radius: 40, opacity: 0.3, color: "#3B82F6" },
  move: { radius: 12, opacity: 0.15, color: "#8B5CF6" },
};

function HeatmapCanvas({ data, type, width, height }: HeatmapCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    // Size canvas to container
    const rect = container.getBoundingClientRect();
    const displayWidth = rect.width;
    const displayHeight = Math.max(500, rect.height);
    canvas.width = displayWidth;
    canvas.height = displayHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear
    ctx.clearRect(0, 0, displayWidth, displayHeight);

    if (data.length === 0) return;

    // Find data bounds to scale points to canvas
    let maxX = 0;
    let maxY = 0;
    data.forEach((p) => {
      if (p.x > maxX) maxX = p.x;
      if (p.y > maxY) maxY = p.y;
    });

    // Add padding
    maxX = Math.max(maxX, 1);
    maxY = Math.max(maxY, 1);

    const scaleX = (displayWidth - 40) / maxX;
    const scaleY = (displayHeight - 40) / maxY;
    const scale = Math.min(scaleX, scaleY);
    const offsetX = 20;
    const offsetY = 20;

    const config = TYPE_CONFIG[type];

    // Draw heat circles with radial gradient
    data.forEach((point) => {
      const x = point.x * scale + offsetX;
      const y = point.y * scale + offsetY;

      const gradient = ctx.createRadialGradient(x, y, 0, x, y, config.radius);
      gradient.addColorStop(0, hexToRgba(config.color, config.opacity));
      gradient.addColorStop(1, hexToRgba(config.color, 0));

      ctx.beginPath();
      ctx.arc(x, y, config.radius, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();
    });

    // Draw click dots on top for click type
    if (type === "click") {
      data.forEach((point) => {
        const x = point.x * scale + offsetX;
        const y = point.y * scale + offsetY;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#EF4444";
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    }
  }, [data, type, width, height]);

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden rounded-lg"
      style={{ minHeight: "500px", background: "linear-gradient(to bottom, hsl(var(--card)), hsl(var(--secondary)/0.3))" }}
    >
      <canvas ref={canvasRef} className="w-full h-full" style={{ minHeight: "500px" }} />

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex items-center gap-3 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--card)/0.9)] px-3 py-2 text-[11px] backdrop-blur-sm">
        <span className="font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-wider">Intensity</span>
        <div className="flex items-center gap-1">
          <div className="h-2 w-8 rounded-full" style={{ background: `linear-gradient(to right, ${hexToRgba(TYPE_CONFIG[type].color, 0.1)}, ${TYPE_CONFIG[type].color})` }} />
          <span className="text-[hsl(var(--muted-foreground))]">Low → High</span>
        </div>
      </div>
    </div>
  );
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export default memo(HeatmapCanvas);
