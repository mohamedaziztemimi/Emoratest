"use client";

import { useEffect, useRef, useState, useCallback } from "react";

// ── Types ────────────────────────────────────────────────────────

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

interface ZoomPanState {
  scale: number;
  offsetX: number;
  offsetY: number;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  data?: {
    clicks: number;
    emotion: string;
    x: number;
    y: number;
  };
}

// ── Constants ────────────────────────────────────────────────────────

const GAUSSIAN_RADIUS = 25;
const COLOR_SCALE = [
  { density: 0.0, color: "#3B82F6" },  // blue (cold)
  { density: 0.25, color: "#60A5FA" },
  { density: 0.5, color: "#8B5CF6" },
  { density: 0.75, color: "#10B981" },  // green
  { density: 0.85, color: "#34D399" },
  { density: 0.9, color: "#10B981" },
  { density: 0.95, color: "#F59E0B" },  // yellow
  { density: 0.975, color: "#F97316" },
  { density: 1.0, color: "#EF4444" },  // red (hot)
];

const EMOTION_COLORS: Record<string, string> = {
  confusion: "#F59E0B",
  frustration: "#EF4444",
  delight: "#10B981",
  anxiety: "#8B5CF6",
  focus: "#3B82F6",
  hesitation: "#FBBF24",
  satisfaction: "#60A5FA",
};

const ZOOM_LEVELS = [0.5, 1, 1.5] as const;
type ZoomLevel = (typeof ZOOM_LEVELS)[number];

// ── Helper Functions ────────────────────────────────────────────────

function getColorForDensity(density: number): string {
  for (let i = COLOR_SCALE.length - 1; i >= 0; i--) {
    if (density >= COLOR_SCALE[i].density) {
      return COLOR_SCALE[i].color;
    }
  }
  return COLOR_SCALE[COLOR_SCALE.length - 1].color;
}

function gaussianBlur(
  data: number[],
  width: number,
  height: number,
  radius: number
): number[] {
  const radiusInt = Math.floor(radius);
  const kernelSize = radiusInt * 2 + 1;
  const kernel: number[] = [];
  const sigma = radius / 3;
  const twoSigmaSquare = 2 * sigma * sigma;

  for (let i = 0; i < kernelSize; i++) {
    const x = i - radiusInt;
    kernel.push(Math.exp(-(x * x) / twoSigmaSquare));
  }

  const kernelSum = kernel.reduce((a, b) => a + b, 0);
  for (let i = 0; i < kernel.length; i++) {
    kernel[i] /= kernelSum;
  }

  const blurred = new Float32Array(width * height);

  // Horizontal pass
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      let sum = 0;
      for (let k = 0; k < kernel.length; k++) {
        const px = x + k - radiusInt;
        if (px >= 0 && px < width) {
          sum += data[y * width + px] * kernel[k];
        }
      }
      blurred[y * width + x] = sum;
    }
  }

  // Vertical pass
  const temp = new Float32Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      let sum = 0;
      for (let k = 0; k < kernel.length; k++) {
        const py = y + k - radiusInt;
        if (py >= 0 && py < height) {
          sum += blurred[py * width + x] * kernel[k];
        }
      }
      temp[y * width + x] = sum;
    }
  }

  return temp;
}

// ── HeatmapCanvas Component ────────────────────────────────────────────

export default function HeatmapCanvas({
  data,
  type,
  width,
  height,
  pageScreenshot,
}: HeatmapCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [zoomPan, setZoomPan] = useState<ZoomPanState>({
    scale: 1,
    offsetX: 0,
    offsetY: 0,
  });
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
  });

  // Build density grid
  const densityGrid = useCallback(() => {
    const grid = new Float32Array(width * height).fill(0);

    data.forEach((point) => {
      const x = Math.floor(point.x * (width / 100));
      const y = Math.floor(point.y * (height / 100));
      if (x >= 0 && x < width && y >= 0 && y < height) {
        grid[y * width + x] += point.value;
      }
    });

    return gaussianBlur(Array.from(grid), width, height, GAUSSIAN_RADIUS);
  }, [data, width, height]);

  const blurredDensity = densityGrid();

  // Render heatmap
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw density grid
    const imageData = ctx.createImageData(width, height);
    const pixels = imageData.data;

    for (let i = 0; i < blurredDensity.length; i++) {
      const density = Math.min(blurredDensity[i], 1.0);
      const color = getColorForDensity(density);

      const idx = i * 4;
      // Convert hex to RGB
      const r = parseInt(color.slice(1, 3), 16);
      const g = parseInt(color.slice(3, 5), 16);
      const b = parseInt(color.slice(5, 7), 16);

      pixels[idx] = r;
      pixels[idx + 1] = g;
      pixels[idx + 2] = b;
      pixels[idx + 3] = 255; // alpha
    }

    ctx.putImageData(imageData, 0, 0);

    // Draw page screenshot as background
    if (pageScreenshot) {
      const img = new Image();
      img.onload = () => {
        ctx.globalAlpha = 0.5;
        ctx.drawImage(img, 0, 0, width, height);
        ctx.globalAlpha = 1.0;
      };
      img.src = pageScreenshot;
    }
  }, [blurredDensity, pageScreenshot, width, height]);

  useEffect(() => {
    render();
  }, [render]);

  // Handle mouse move for tooltip
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find nearby data points
    const nearbyPoints = data.filter(
      (p) =>
        Math.abs(p.x * (width / 100) - x) < 20 &&
        Math.abs(p.y * (height / 100) - y) < 20
    );

    if (nearbyPoints.length > 0) {
      const clicks = nearbyPoints.filter((p) => p.emotion).length;
      const emotions = nearbyPoints.map((p) => p.emotion).filter(Boolean) as string[];
      const emotionCounts = emotions.reduce<Record<string, number>>((acc, e) => {
        acc[e] = (acc[e] || 0) + 1;
        return acc;
      }, {});

      const dominantEmotion = Object.entries(emotionCounts)
        .sort((a, b) => b[1] - a[1])[0]?.[0] || "N/A";

      setTooltip({
        visible: true,
        x,
        y,
        data: {
          clicks,
          emotion: dominantEmotion,
          x: Math.floor(x / (width / 100)),
          y: Math.floor(y / (height / 100)),
        },
      });
    } else {
      setTooltip((prev) => ({ ...prev, visible: false }));
    }
  }, [data, width, height]);

  // Handle zoom
  const handleZoomIn = useCallback(() => {
    setZoomPan((prev) => {
      const currentIndex = ZOOM_LEVELS.indexOf(prev.scale as ZoomLevel);
      const nextIndex = Math.min(currentIndex + 1, ZOOM_LEVELS.length - 1);
      return {
        ...prev,
        scale: ZOOM_LEVELS[nextIndex],
      };
    });
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomPan((prev) => {
      const currentIndex = ZOOM_LEVELS.indexOf(prev.scale as ZoomLevel);
      const nextIndex = Math.max(currentIndex - 1, 0);
      return {
        ...prev,
        scale: ZOOM_LEVELS[nextIndex],
      };
    });
  }, []);

  // Handle pan (drag)
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const startX = e.clientX;
    const startY = e.clientY;
    const startOffsetX = zoomPan.offsetX;
    const startOffsetY = zoomPan.offsetY;

    const handleMouseMove = (me: MouseEvent) => {
      const dx = (me.clientX - startX) / zoomPan.scale;
      const dy = (me.clientY - startY) / zoomPan.scale;
      setZoomPan((prev) => ({
        ...prev,
        offsetX: Math.max(-width * 0.5, Math.min(0, startOffsetX + dx)),
        offsetY: Math.max(-height * 0.5, Math.min(0, startOffsetY + dy)),
      }));
    };

    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }, [zoomPan]);

  // Export canvas as PNG
  const handleExport = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement("a");
    link.download = `heatmap-${type}-${Date.now()}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  }, [type]);

  return (
    <div
      ref={containerRef}
      className="relative overflow-hidden border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--card))]"
      style={{ width: "100%", height }}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setTooltip((prev) => ({ ...prev, visible: false }))}
    >
      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={width * zoomPan.scale}
        height={height * zoomPan.scale}
        className="absolute left-0 top-0 origin-top-left"
        style={{
          transform: `translate(${zoomPan.offsetX}px, ${zoomPan.offsetY}px) scale(${zoomPan.scale})`,
          cursor: zoomPan.scale !== 1 ? "grab" : "default",
        }}
        onMouseDown={handleMouseDown}
      />

      {/* Zoom Controls */}
      <div className="absolute bottom-4 right-4 flex gap-2 bg-white rounded-lg shadow-lg border border-[hsl(var(--border))] p-2">
        <button
          onClick={handleZoomOut}
          disabled={zoomPan.scale === ZOOM_LEVELS[0]}
          className="p-2 hover:bg-[hsl(var(--accent))] disabled:opacity-50 rounded-md transition-colors"
          title="Zoom Out"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.047 12l-8-8m0 0l-8 8m8-8v16" />
          </svg>
        </button>

        <span className="text-sm font-medium text-[hsl(var(--foreground))]">
          {Math.round(zoomPan.scale * 100)}%
        </span>

        <button
          onClick={handleZoomIn}
          disabled={zoomPan.scale === ZOOM_LEVELS[ZOOM_LEVELS.length - 1]}
          className="p-2 hover:bg-[hsl(var(--accent))] disabled:opacity-50 rounded-md transition-colors"
          title="Zoom In"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 12h8m-8 8l8-8m0 0l8 8v16" />
          </svg>
        </button>

        <button
          onClick={handleExport}
          className="p-2 hover:bg-[hsl(var(--accent))] rounded-md transition-colors"
          title="Export PNG"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003 3v1m0-4h4m0 4h18" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9h6m-6-6v6m0 0l6-6" />
          </svg>
        </button>
      </div>

      {/* Tooltip */}
      {tooltip.visible && (
        <div
          className="absolute bg-[hsl(var(--popover))] text-[hsl(var(--popover-foreground))] px-3 py-2 rounded-lg shadow-lg pointer-events-none border border-[hsl(var(--border))]"
          style={{
            left: tooltip.x + 10,
            top: tooltip.y + 10,
            zIndex: 50,
          }}
        >
          {tooltip.data?.emotion && (
            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-[hsl(var(--border))]">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: EMOTION_COLORS[tooltip.data.emotion] || "#ccc" }}
              />
              <span className="font-semibold text-sm">{tooltip.data.emotion}</span>
            </div>
          )}
          <div className="text-xs space-y-1">
            <div>Position: ({tooltip.data.x}, {tooltip.data.y})</div>
            {tooltip.data.clicks !== undefined && (
              <div>Clicks in area: <span className="font-semibold">{tooltip.data.clicks}</span></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
