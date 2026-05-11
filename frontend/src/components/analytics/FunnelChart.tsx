"use client";

import { useState, useEffect, useRef } from "react";

// ── Types ────────────────────────────────────────────────

export interface FunnelStep {
  name: string;
  visitors: number;
  conversions: number;
  conversionRate: number;
  dropOffRate: number;
  emotionProfile?: Record<string, number>;
  dominantEmotion?: string;
}

export interface FunnelResult {
  experimentId: string;
  steps: FunnelStep[];
  totalVisitors: number;
  overallConversionRate: number;
  variantId?: string;
}

export interface FunnelChartProps {
  data: FunnelResult;
  showEmotions?: boolean;
  height?: number;
  width?: number;
}

// ── Behavioral State Utilities ────────────────────────────────────────

const EMOTION_COLORS: Record<string, { bg: string; icon: string }> = {
  frustrated: { bg: "#EF4444", icon: "😤" },
  confused: { bg: "#F59E0B", icon: "😕" },
  hesitating: { bg: "#EAB308", icon: "🤔" },
  engaged: { bg: "#22C55E", icon: "😊" },
  disengaged: { bg: "#6B7280", icon: "😴" },
};

const getEmotionColor = (emotion: string) =>
  EMOTION_COLORS[emotion] || { bg: "#6B7280", icon: "❓" };

const getEmotionGradient = (profile?: Record<string, number>) => {
  if (!profile) return "from-blue-500 to-blue-600";

  const sortedEmotions = Object.entries(profile)
    .sort((a, b) => b[1] - a[1]);

  if (sortedEmotions.length < 2) {
    return "from-blue-500 to-blue-600";
  }

  const topEmotion = sortedEmotions[0][0];
  const topColor = getEmotionColor(topEmotion).bg;

  return `from-[${topColor.replace("#", "")}] to-blue-600`;
};

// ── SVG Path Generators ───────────────────────────────────

const generateTrapezoidPath = (
  x: number,
  y: number,
  width: number,
  height: number,
) => {
  const halfWidth = width / 2;
  return `
    M ${x - halfWidth},${y}
    L ${x + halfWidth},${y}
    L ${x + halfWidth},${y + height}
    L ${x - halfWidth},${y + height}
    Z
  `;
};

const generateTrapezoidGradient = (
  stepIndex: number,
  totalSteps: number,
  dropOffRate: number,
): string => {
  // Blue gradient for normal steps, red tint for high drop-off (> 40%)
  const isHighDropOff = dropOffRate > 0.4;

  if (isHighDropOff) {
    const intensity = Math.min((dropOffRate - 0.4) / 0.6, 1);
    const r = Math.floor(59 * (1 - intensity * 0.5));
    const g = Math.floor(130 * (1 - intensity * 0.3));
    const b = Math.floor(246 * (1 - intensity * 0.2));
    return `rgb(${r}, ${g}, ${b})`;
  }

  // Normal blue gradient
  return "url(#funnelGradient)";
};

// ── FunnelChart Component ───────────────────────────────────

export default function FunnelChart({
  data,
  showEmotions = false,
  height = 300,
  width = 600,
}: FunnelChartProps) {
  const [mounted, setMounted] = useState(false);
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number } | null>(null);

  // Animate on mount
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!data.steps || data.steps.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[hsl(var(--muted-foreground))]">
        <p>No funnel data available</p>
      </div>
    );
  }

  const maxVisitors = Math.max(...data.steps.map((s) => s.visitors));
  const chartHeight = height - 40; // Leave room for emotion bands
  const chartWidth = width - 40;
  const stepHeight = chartHeight / data.steps.length;
  const maxStepWidth = chartWidth;
  const xCenter = width / 2;

  return (
    <div className="relative" style={{ width, height }}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="overflow-visible"
      >
        {/* Gradients */}
        <defs>
          <linearGradient id="funnelGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#1D4ED8" />
          </linearGradient>
        </defs>

        {/* Draw funnel steps */}
        {data.steps.map((step, index) => {
          const stepWidth = (step.visitors / maxVisitors) * maxStepWidth;
          const stepY = index * stepHeight + 20; // 20px top padding
          const isHovered = hoveredStep === index;
          const dropOffRate = step.dropOffRate;

          return (
            <g key={index} onMouseEnter={() => setHoveredStep(index)} onMouseLeave={() => setHoveredStep(null)}>
              {/* Trapezoid */}
              <path
                d={generateTrapezoidPath(xCenter, stepY, stepWidth, stepHeight)}
                fill={generateTrapezoidGradient(index, data.steps.length, dropOffRate)}
                stroke="rgba(255, 255, 255, 0.3)"
                strokeWidth={1}
                className={`transition-all duration-300 ${mounted ? "opacity-100" : "opacity-0"}`}
                style={{
                  transitionDelay: `${index * 100}ms`,
                }}
              />

              {/* Step label */}
              <text
                x={xCenter}
                y={stepY + stepHeight / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                className={`fill-[hsl(var(--foreground))] font-semibold ${
                  isHovered ? "text-lg" : "text-sm"
                } transition-all`}
              >
                {step.name}
              </text>

              {/* Metrics */}
              <text
                x={xCenter}
                y={stepY + stepHeight / 2 + (isHovered ? 28 : 20)}
                textAnchor="middle"
                dominantBaseline="middle"
                className={`fill-[hsl(var(--foreground))] text-xs transition-all`}
              >
                {step.conversions.toLocaleString()} / {step.visitors.toLocaleString()} ({(step.conversionRate * 100).toFixed(1)}%)
              </text>

              {/* Drop-off badge between steps */}
              {index < data.steps.length - 1 && (
                <>
                  <line
                    x1={xCenter}
                    y1={stepY + stepHeight}
                    x2={xCenter}
                    y2={(index + 1) * stepHeight + 20}
                    stroke={dropOffRate > 0.3 ? "#EF4444" : "#94A3B8"}
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    opacity={mounted ? 1 : 0}
                    className="transition-opacity"
                    style={{ transitionDelay: `${index * 100}ms` }}
                  />

                  {/* Drop-off badge */}
                  <g
                    transform={`translate(${xCenter - 30}, ${stepY + stepHeight / 2})`}
                    opacity={mounted ? 1 : 0}
                    className="transition-opacity"
                    style={{ transitionDelay: `${index * 100 + 50}ms` }}
                  >
                    <rect
                      x={-30}
                      y={-10}
                      width={60}
                      height={20}
                      rx={10}
                      fill={dropOffRate > 0.3 ? "#FEF2F2" : "#F0FDF4"}
                      stroke={dropOffRate > 0.3 ? "#EF4444" : "#94A3B8"}
                      strokeWidth={1}
                    />
                    <text
                      x={0}
                      y={5}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      className={`text-xs font-semibold ${
                        dropOffRate > 0.3 ? "text-red-700" : "text-amber-700"
                      }`}
                    >
                      {(dropOffRate * 100).toFixed(0)}% drop-off
                    </text>
                  </g>

                  {/* Emotion icon on high drop-off */}
                  {dropOffRate > 0.3 && step.dominantEmotion && (
                    <text
                      x={xCenter + 15}
                      y={stepY + stepHeight / 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      className="text-lg transition-opacity"
                      opacity={mounted ? 1 : 0}
                      style={{ transitionDelay: `${index * 100 + 100}ms` }}
                    >
                      {getEmotionColor(step.dominantEmotion).icon}
                    </text>
                  )}
                </>
              )}
            </g>
          );
        })}

        {/* Total visitors label */}
        <text
          x={10}
          y={20}
          className={`fill-[hsl(var(--muted-foreground))] text-xs transition-opacity ${mounted ? "opacity-100" : "opacity-0"}`}
        >
          Total: {data.totalVisitors.toLocaleString()}
        </text>

        {/* Overall conversion rate */}
        <text
          x={10}
          y={40}
          className={`fill-[hsl(var(--foreground))] text-sm font-semibold transition-opacity ${mounted ? "opacity-100" : "opacity-0"}`}
        >
          Overall CR: {(data.overallConversionRate * 100).toFixed(1)}%
        </text>
      </svg>

      {/* Emotion bands (when enabled) */}
      {showEmotions && mounted && (
        <div className="absolute top-0 right-0 h-full w-32 flex flex-col gap-1 p-2 overflow-hidden">
          {data.steps.map((step, index) => {
            const emotionProfile = step.emotionProfile;
            const dominantEmotion = step.dominantEmotion;

            if (!emotionProfile || index === data.steps.length - 1) return null;

            const barHeight = (chartHeight / data.steps.length) * 0.6;
            const barY = index * (chartHeight / data.steps.length) + 25;

            // Sort emotions by value for stacked bar
            const sortedEmotions = Object.entries(emotionProfile)
              .sort((a, b) => b[1] - a[1]);

            return (
              <div
                key={index}
                className="relative"
                style={{ height: `${barHeight}px`, width: "100%" }}
              >
                {/* Emotion bars */}
                <div className="w-full h-full flex">
                  {sortedEmotions.map(([emotion, value], i) => {
                    const barWidth = (value / Math.max(...Object.values(emotionProfile))) * 100;
                    const color = getEmotionColor(emotion).bg;

                    return (
                      <div
                        key={emotion}
                        className="h-full transition-all hover:opacity-80 cursor-help"
                        style={{
                          width: `${barWidth}%`,
                          backgroundColor: color,
                        }}
                        title={`${emotion}: ${(value * 100).toFixed(1)}%`}
                      />
                    );
                  })}
                </div>

                {/* Dominant emotion icon */}
                {dominantEmotion && (
                  <span
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-xs"
                    title={dominantEmotion}
                  >
                    {getEmotionColor(dominantEmotion).icon}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Tooltip */}
      {hoveredStep !== null && tooltipPosition && (
        <div
          className="absolute bg-[hsl(var(--popover))] text-[hsl(var(--popover-foreground))] text-xs rounded shadow-lg border border-[hsl(var(--border))] p-3 pointer-events-none z-50"
          style={{
            left: `${tooltipPosition.x + 10}px`,
            top: `${tooltipPosition.y}px`,
          }}
        >
          <div className="font-semibold mb-2">{data.steps[hoveredStep].name}</div>
          <div className="space-y-1">
            <div>Visitors: {data.steps[hoveredStep].visitors.toLocaleString()}</div>
            <div>Conversions: {data.steps[hoveredStep].conversions.toLocaleString()}</div>
            <div>Conversion Rate: {(data.steps[hoveredStep].conversionRate * 100).toFixed(2)}%</div>
            <div>Drop-off: {(data.steps[hoveredStep].dropOffRate * 100).toFixed(1)}%</div>
            {data.steps[hoveredStep].dominantEmotion && (
              <div className="flex items-center gap-2">
                <span>Dominant Emotion:</span>
                <span className="text-lg">{getEmotionColor(data.steps[hoveredStep].dominantEmotion).icon}</span>
                <span>{data.steps[hoveredStep].dominantEmotion}</span>
              </div>
            )}
            {showEmotions && data.steps[hoveredStep].emotionProfile && (
              <div className="mt-2 pt-2 border-t border-[hsl(var(--border))]">
                <div className="font-semibold mb-1">Emotion Breakdown:</div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(data.steps[hoveredStep].emotionProfile).map(([emotion, value]) => (
                    <div key={emotion} className="flex items-center gap-2">
                      <span>{getEmotionColor(emotion).icon}</span>
                      <span className="capitalize">{emotion}:</span>
                      <span className="font-semibold">{(value * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
