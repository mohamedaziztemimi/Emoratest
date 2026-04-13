"use client";

import { useState } from "react";

// ── Types ────────────────────────────────────────────────────────

export interface EmotionZone {
  x: number;
  y: number;
  width: number;
  height: number;
  emotion: string;
  confidence: number;
  userCount: number;
}

export interface EmotionOverlayProps {
  emotionZones: EmotionZone[];
  visible: boolean;
  onZoneClick: (zone: EmotionZone) => void;
}

// ── Constants ────────────────────────────────────────────────────────

const EMOTION_COLORS: Record<string, { bg: string; text: string }> = {
  confusion: { bg: "rgba(245, 158, 11, 0.2)", text: "#F59E0B" },
  frustration: { bg: "rgba(239, 68, 68, 0.2)", text: "#EF4444" },
  delight: { bg: "rgba(16, 185, 129, 0.2)", text: "#10B981" },
  anxiety: { bg: "rgba(139, 92, 246, 0.2)", text: "#8B5CF6" },
  focus: { bg: "rgba(59, 130, 246, 0.2)", text: "#3B82F6" },
  hesitation: { bg: "rgba(251, 191, 36, 0.2)", text: "#FBBF24" },
  satisfaction: { bg: "rgba(96, 165, 250, 0.2)", text: "#60A5FA" },
  other: { bg: "rgba(107, 114, 128, 0.2)", text: "#6B7280" },
};

const getEmotionColor = (emotion: string) =>
  EMOTION_COLORS[emotion as keyof typeof EMOTION_COLORS] || EMOTION_COLORS.other;

// ── EmotionOverlay Component ────────────────────────────────────────────

export default function EmotionOverlay({
  emotionZones,
  visible,
  onZoneClick,
}: EmotionOverlayProps) {
  const [hoveredZone, setHoveredZone] = useState<EmotionZone | null>(null);

  // Handle zone click
  const handleClick = (zone: EmotionZone) => {
    onZoneClick(zone);
  };

  // Group zones by emotion for z-index
  const groupedZones = emotionZones.reduce<Record<string, EmotionZone[]>>((acc, zone) => {
    if (!acc[zone.emotion]) {
      acc[zone.emotion] = [];
    }
    acc[zone.emotion].push(zone);
    return acc;
  }, {});

  return (
    <div
      className={`absolute inset-0 pointer-events-none transition-opacity duration-300 ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      {Object.entries(groupedZones).map(([emotion, zones], groupIndex) => {
        const color = getEmotionColor(emotion);

        return (
          <div key={groupIndex} className="absolute inset-0">
            {zones.map((zone, zoneIndex) => {
              const isHovered = hoveredZone === zone;
              const isFrustration = zone.emotion === "frustration";

              return (
                <div
                  key={zoneIndex}
                  onClick={() => handleClick(zone)}
                  onMouseEnter={() => setHoveredZone(zone)}
                  onMouseLeave={() => setHoveredZone(null)}
                  className="absolute cursor-pointer pointer-events-auto transition-all duration-200"
                  style={{
                    left: `${(zone.x / 100) * 100}%`,
                    top: `${(zone.y / 100) * 100}%`,
                    width: `${zone.width}%`,
                    height: `${zone.height}%`,
                    backgroundColor: color.bg,
                    zIndex: 10 + groupIndex,
                    border: isHovered
                      ? `2px solid ${color.text}`
                      : `1px solid transparent`,
                    borderRadius: "4px",
                    animation: isFrustration ? "pulse-red 2s infinite" : "none",
                  }}
                >
                  {/* Zone label - show on hover */}
                  {isHovered && (
                    <div className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-[hsl(var(--popover))] text-[hsl(var(--popover-foreground))] px-2 py-1 rounded shadow-lg border border-[hsl(var(--border))] text-xs whitespace-nowrap z-20">
                      <div className="font-semibold">{zone.emotion}</div>
                      <div className="text-[hsl(var(--muted-foreground))]">
                        {zone.userCount} user{zone.userCount !== 1 ? "s" : ""}
                      </div>
                      <div className="text-[hsl(var(--muted-foreground))]">
                        Confidence: {(zone.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
