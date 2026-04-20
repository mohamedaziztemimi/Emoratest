/* ────────────────────────────────────────────────────────
   MiniDashboard - Interactive product dashboard preview
   ──────────────────────────────────────────────────────── */

"use client";

import { useState, useEffect, useRef } from "react";
import { GlassCard, StatCard, PulsingDot, EmotionBadge } from "../ui";

type DashboardPersona = "growth" | "pm" | "ux" | "cro";

interface EmotionTrendData {
  day: string;
  confusion: number;
  delight: number;
  frustration: number;
}

const EMOTION_TREND_DATA: EmotionTrendData[] = [
  { day: "Mon", confusion: 23, delight: 45, frustration: 12 },
  { day: "Tue", confusion: 28, delight: 52, frustration: 15 },
  { day: "Wed", confusion: 31, delight: 48, frustration: 18 },
  { day: "Thu", confusion: 25, delight: 55, frustration: 14 },
  { day: "Fri", confusion: 27, delight: 58, frustration: 13 },
  { day: "Sat", confusion: 22, delight: 62, frustration: 10 },
  { day: "Sun", confusion: 20, delight: 65, frustration: 8 },
];

const CONFUSION_ZONES = [
  { page: "/checkout", dropoff: 34 },
  { page: "/pricing", dropoff: 28 },
  { page: "/signup", dropoff: 41 },
];

const AI_SUGGESTIONS = [
  { text: "Simplify CTA on /checkout", lift: "+28%" },
  { text: "A/B test headline for confused segments", lift: null },
];

function EmotionSparkline() {
  const [hoverX, setHoverX] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const width = 600;
  const height = 180;
  const padding = { top: 20, right: 30, bottom: 30, left: 40 };

  const xScale = (i: number) => padding.left + (i / (EMOTION_TREND_DATA.length - 1)) * (width - padding.left - padding.right);
  const yScale = (val: number) => height - padding.bottom - (val / 100) * (height - padding.top - padding.bottom);

  // Line path generator
  const linePath = (emotion: "confusion" | "delight" | "frustration") => {
    return EMOTION_TREND_DATA.map((d, i) => {
      const x = xScale(i);
      const y = yScale(d[emotion]);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    }).join(" ");
  };

  const colors = { confusion: "#F59E0B", delight: "#10B981", frustration: "#EF4444" };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const chartX = Math.max(padding.left, Math.min(width - padding.right, x));
    setHoverX(chartX);
  };

  const handleMouseLeave = () => setHoverX(null);

  // Find closest data point
  let hoveredData: EmotionTrendData | null = null;
  if (hoverX !== null) {
    const totalWidth = width - padding.left - padding.right;
    const relativeX = hoverX - padding.left;
    const index = Math.round((relativeX / totalWidth) * (EMOTION_TREND_DATA.length - 1));
    hoveredData = EMOTION_TREND_DATA[index];
  }

  return (
    <div className="relative">
      <h3 className="text-sm font-semibold text-[var(--et-text-secondary)] mb-3">
        7-Day Emotion Trend
      </h3>
      <div className="relative">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          className="w-full h-[180px]"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((val) => {
            const y = yScale(val);
            return (
              <g key={val}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="rgba(255,255,255,0.05)"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 5}
                  y={y + 3}
                  fill="rgba(255,255,255,0.3)"
                  fontSize="9"
                  textAnchor="end"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* X-axis labels */}
          {EMOTION_TREND_DATA.map((d, i) => (
            <text
              key={d.day}
              x={xScale(i)}
              y={height - 5}
              fill="rgba(255,255,255,0.4)"
              fontSize="9"
              textAnchor="middle"
            >
              {d.day}
            </text>
          ))}

          {/* Emotion lines */}
          <path
            d={linePath("confusion")}
            fill="none"
            stroke={colors.confusion}
            strokeWidth="2"
            opacity="0.8"
          />
          <path
            d={linePath("delight")}
            fill="none"
            stroke={colors.delight}
            strokeWidth="2"
            opacity="0.8"
          />
          <path
            d={linePath("frustration")}
            fill="none"
            stroke={colors.frustration}
            strokeWidth="2"
            opacity="0.8"
          />

          {/* Hover cursor line */}
          {hoverX !== null && (
            <line
              x1={hoverX}
              y1={padding.top}
              x2={hoverX}
              y2={height - padding.bottom}
              stroke="rgba(255,255,255,0.3)"
              strokeWidth="1"
              strokeDasharray="4 4"
            />
          )}

          {/* Data points on hover */}
          {hoveredData && hoverX !== null && (
            <>
              <circle cx={hoverX} cy={yScale(hoveredData.confusion ?? 0)} r="4" fill={colors.confusion} />
              <circle cx={hoverX} cy={yScale(hoveredData.delight ?? 0)} r="4" fill={colors.delight} />
              <circle cx={hoverX} cy={yScale(hoveredData.frustration ?? 0)} r="4" fill={colors.frustration} />
            </>
          )}
        </svg>

        {/* Tooltip */}
        {hoveredData && (
          <div
            className="absolute pointer-events-none bg-[var(--et-bg-card)] border border-[var(--et-glass-border)] rounded px-3 py-2 text-[11px] shadow-lg"
            style={{
              left: hoverX ? `${hoverX + 10}px` : "50%",
              top: "10px",
            }}
          >
            <div className="font-semibold text-[var(--et-text-primary)] mb-1">
              {hoveredData.day}
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#F59E0B]" />
                <span className="text-[var(--et-text-muted)]">
                  Confusion: <span className="text-[var(--et-text-primary)]">{hoveredData.confusion}%</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#10B981]" />
                <span className="text-[var(--et-text-muted)]">
                  Delight: <span className="text-[var(--et-text-primary)]">{hoveredData.delight}%</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#EF4444]" />
                <span className="text-[var(--et-text-muted)]">
                  Frustration: <span className="text-[var(--et-text-primary)]">{hoveredData.frustration}%</span>
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-[#F59E0B]" />
          <span className="text-[11px] text-[var(--et-text-muted)]">Confusion</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-[#10B981]" />
          <span className="text-[11px] text-[var(--et-text-muted)]">Delight</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-[#EF4444]" />
          <span className="text-[11px] text-[var(--et-text-muted)]">Frustration</span>
        </div>
      </div>
    </div>
  );
}

interface MiniDashboardProps {
  persona?: DashboardPersona;
  className?: string;
}

export function MiniDashboard({ persona = "growth", className }: MiniDashboardProps) {
  const [activePersona, setActivePersona] = useState<DashboardPersona>(persona);
  const [isVisible, setIsVisible] = useState(false);

  // Animated counter for sessions
  const [sessionCount, setSessionCount] = useState(0);

  useEffect(() => {
    setIsVisible(true);
    // Animate session counter
    const target = 2847;
    const duration = 1200;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setSessionCount(Math.round(target * eased));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    animate();
  }, []);

  // Persona-specific view rendering
  const renderPersonaView = () => {
    switch (activePersona) {
      case "growth":
        return (
          <div className="bg-[var(--et-bg-700)]/50 rounded-lg p-4 border border-[var(--et-border)]">
            <h4 className="text-sm font-semibold text-[var(--et-text-secondary)] mb-3">
              Conversion Lift This Week
            </h4>
            <div className="flex items-end gap-3">
              <span className="text-3xl font-bold text-[var(--et-satisfaction)]">
                +12.4%
              </span>
              <span className="text-[12px] text-[var(--et-text-muted)] mb-1">
                vs baseline
              </span>
            </div>
            <div className="mt-3 h-2 bg-[var(--et-bg-800)] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[var(--et-blue)] to-[var(--et-purple)] transition-all duration-1000"
                style={{ width: `${isVisible ? "68%" : "0%"}` }}
              />
            </div>
          </div>
        );
      case "pm":
        return (
          <div className="bg-[var(--et-bg-700)]/50 rounded-lg p-4 border border-[var(--et-border)]">
            <h4 className="text-sm font-semibold text-[var(--et-text-secondary)] mb-3">
              Retention Risk
            </h4>
            <div className="flex gap-3">
              <div className="flex-1">
                <span className="text-2xl font-bold text-[var(--et-text-primary)]">
                  8.2%
                </span>
                <div className="text-[11px] text-[var(--et-text-muted)]">
                  at-risk users
                </div>
              </div>
              <div className="flex-1">
                <span className="text-2xl font-bold text-[var(--et-frustration)]">
                  3
                </span>
                <div className="text-[11px] text-[var(--et-text-muted)]">
                  critical alerts
                </div>
              </div>
            </div>
          </div>
        );
      case "ux":
        return (
          <div className="bg-[var(--et-bg-700)]/50 rounded-lg p-4 border border-[var(--et-border)]">
            <h4 className="text-sm font-semibold text-[var(--et-text-secondary)] mb-3">
              Session Replay
            </h4>
            <div className="flex gap-3">
              <div className="w-20 h-14 bg-[var(--et-bg-800)] rounded border border-[var(--et-border)] flex items-center justify-center">
                <svg className="w-6 h-6 text-[var(--et-text-muted)]" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="text-xs text-[var(--et-text-muted)] mb-1">Valence-Arousal</div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] bg-[#10B981]/20 text-[#10B981]">
                    +0.6
                  </span>
                  <span className="text-[10px] text-[var(--et-text-muted)]">
                    positive engagement
                  </span>
                </div>
              </div>
            </div>
          </div>
        );
      case "cro":
        return (
          <div className="bg-[var(--et-bg-700)]/50 rounded-lg p-4 border border-[var(--et-border)]">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-[var(--et-text-secondary)]">
                SRM Status
              </h4>
              <span className="px-2 py-0.5 rounded text-[10px] bg-[#10B981]/20 text-[#10B981]">
                No Mismatch
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
              <div>
                <div className="text-lg font-bold text-[var(--et-text-primary)]">
                  3
                </div>
                <div className="text-[10px] text-[var(--et-text-muted)]">
                  segments
                </div>
              </div>
              <div>
                <div className="text-lg font-bold text-[var(--et-text-primary)]">
                  99.2%
                </div>
                <div className="text-[10px] text-[var(--et-text-muted)]">
                  power
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={className}>
      <GlassCard padding="lg" glow="blue">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--et-blue)] to-[var(--et-purple)] flex items-center justify-center">
              <span className="text-white font-bold text-sm">E</span>
            </div>
            <div>
              <div className="text-sm font-semibold text-[var(--et-text-primary)]">
                EmoraTest Dashboard
              </div>
              <PulsingDot color="#10B981" size={4} label="LIVE" />
            </div>
          </div>

          {/* Persona switcher */}
          <div className="flex gap-1 bg-[var(--et-bg-700)] rounded-lg p-1">
            {(["growth", "pm", "ux", "cro"] as DashboardPersona[]).map((p) => (
              <button
                key={p}
                onClick={() => setActivePersona(p)}
                className={`
                  px-3 py-1.5 rounded text-xs font-medium capitalize transition-all duration-250
                  ${activePersona === p
                    ? "bg-[var(--et-bg-card)] text-[var(--et-text-primary)] shadow-sm"
                    : "text-[var(--et-text-muted)] hover:text-[var(--et-text-secondary)]"
                  }
                `}
              >
                {p === "growth" && "Growth"}
                {p === "pm" && "PM"}
                {p === "ux" && "UX"}
                {p === "cro" && "CRO"}
              </button>
            ))}
          </div>
        </div>

        {/* Stat cards row */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <StatCard
            label="Sessions Today"
            value={sessionCount.toLocaleString()}
            delta="+18%"
            deltaPositive={true}
            animate={false}
          />
          <StatCard
            label="Active Tests"
            value={3}
            delta="2 pending"
            deltaPositive={true}
            animate={false}
          />
          <StatCard
            label="Frustration Alerts"
            value={2}
            delta="-15%"
            deltaPositive={false}
            animate={false}
          />
        </div>

        {/* Emotion trend chart */}
        <div className="mb-6">
          <EmotionSparkline />
        </div>

        {/* Confusion zones list */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-[var(--et-text-secondary)] mb-3">
            Top Confusion Zones
          </h3>
          <div className="space-y-2">
            {CONFUSION_ZONES.map((zone, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg border border-[var(--et-border)] hover:border-[var(--et-blue)]/50 hover:bg-[var(--et-bg-700)]/30 transition-all duration-200 group"
              >
                <div className="flex items-center gap-3">
                  <EmotionBadge emotion="confusion" size="sm" />
                  <span className="text-sm text-[var(--et-text-primary)]">
                    {zone.page}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[var(--et-frustration)]">
                    ↓ {zone.dropoff}% drop-off
                  </span>
                  <a
                    href="#"
                    className="text-xs text-[var(--et-blue)] group-hover:translate-x-1 transition-transform duration-200 flex items-center gap-1"
                  >
                    View Heatmap
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Persona-specific view */}
        <div className="mb-6">
          {renderPersonaView()}
        </div>

        {/* AI suggestions */}
        <div>
          <h3 className="text-sm font-semibold text-[var(--et-text-secondary)] mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-[var(--et-confusion)]" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233 2.178.894.894 1.233-2.177a1 1 0 111.79.894l-1.582 3.954H17a1 1 0 110 2h-2.677l1.582 3.954a1 1 0 11-1.79.894l-1.233-2.178-.894.894 1.233 2.178a1 1 0 01-1.79-.894l-1.599-.8L11 16.677V18a1 1 0 11-2 0v-1.323l-3.954-1.582-1.599.8a1 1 0 11-.894-1.79l1.233-2.178-.894-.894-1.233 2.178a1 1 0 11-1.79-.894l1.582-3.954H3a1 1 0 110-2h2.677l-1.582-3.954a1 1 0 111.79-.894l1.233 2.178.894-.894-1.233-2.178a1 1 0 111.79.894l1.599.8L9 3.323V3a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            AI Suggestions
          </h3>
          <div className="flex flex-wrap gap-2">
            {AI_SUGGESTIONS.map((suggestion, index) => (
              <button
                key={index}
                className="px-3 py-2 rounded-lg border border-[var(--et-glass-border)] bg-[var(--et-bg-700)]/30 text-left text-xs hover:border-[var(--et-blue)]/50 transition-all duration-200"
              >
                <div className="flex items-center gap-2 mb-1">
                  <svg className="w-3 h-3 text-[var(--et-blue)]" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                  </svg>
                  <span className="font-medium text-[var(--et-text-secondary)]">
                    {suggestion.text}
                  </span>
                </div>
                {suggestion.lift && (
                  <div className="text-[10px] text-[var(--et-satisfaction)]">
                    {suggestion.lift} est. lift
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
