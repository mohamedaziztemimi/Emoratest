/* ────────────────────────────────────────────────────────
   BeforeAfterSlide - Two-panel comparison for problem/solution
   ──────────────────────────────────────────────────────── */

"use client";

import { clsx } from "clsx";
import { ReactNode } from "react";

export interface SlideContent {
  title: string;
  description: string;
  mockImage?: ReactNode;
  stats?: string[];
}

type PersonaType = "growth" | "pm" | "ux" | "cro";

interface BeforeAfterSlideProps {
  before: SlideContent;
  after: SlideContent;
  className?: string;
}

// Default mockups for each state
function BeforeMockup() {
  return (
    <div className="relative w-full h-48 bg-[var(--et-bg-800)] rounded-lg overflow-hidden">
      {/* Bland line chart */}
      <svg className="absolute inset-0 w-full h-full p-4" viewBox="0 0 200 100">
        <line
          x1="10" y1="70"
          x2="190" y2="70"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="0.5"
        />
        <line
          x1="10" y1="50"
          x2="190" y2="50"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="0.5"
        />
        <line
          x1="10" y1="30"
          x2="190" y2="30"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="0.5"
        />
        <text x="10" y="20" fill="rgba(255,255,255,0.3)" fontSize="6">
          Conversion Rate
        </text>
        <path
          d="M 10 60 Q 50 55 90 65 T 190 50"
          fill="none"
          stroke="rgba(255,255,255,0.3)"
          strokeWidth="1"
        />
      </svg>
      {/* Muted overlay */}
      <div className="absolute inset-0 bg-black/20" />
    </div>
  );
}

function AfterMockup() {
  return (
    <div className="relative w-full h-48 bg-[var(--et-bg-800)] rounded-lg overflow-hidden border border-[var(--et-glass-border)]">
      {/* Funnel with emotion overlays */}
      <svg className="absolute inset-0 w-full h-full p-4" viewBox="0 0 200 100">
        {/* Funnel trapezoids */}
        <path
          d="M 20 10 L 180 10 L 160 40 L 40 40 Z"
          fill="rgba(0,123,255,0.1)"
          stroke="var(--et-blue)"
          strokeWidth="0.5"
        />
        <path
          d="M 45 45 L 155 45 L 140 70 L 60 70 Z"
          fill="rgba(124,58,237,0.1)"
          stroke="var(--et-purple)"
          strokeWidth="0.5"
        />
        <path
          d="M 65 75 L 135 75 L 120 95 L 80 95 Z"
          fill="rgba(16,185,129,0.1)"
          stroke="var(--et-delight)"
          strokeWidth="0.5"
        />

        {/* Emotion badges */}
        <circle cx="100" cy="25" r="4" fill="#EF4444" opacity="0.7">
          <animate attributeName="opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite" />
        </circle>
        <circle cx="80" cy="57" r="4" fill="#F59E0B" opacity="0.7" />
        <circle cx="120" cy="82" r="4" fill="#10B981" opacity="0.7" />
      </svg>

      {/* AI suggestion chip */}
      <div className="absolute top-12 right-3 bg-gradient-to-r from-[var(--et-blue)] to-[var(--et-purple)] text-[8px] text-white px-2 py-0.5 rounded-full">
        Fix CTA Confusion → +28%
      </div>
    </div>
  );
}

export function BeforeAfterSlide({
  before,
  after,
  className,
}: BeforeAfterSlideProps) {
  return (
    <div className={clsx("flex items-stretch gap-4", className)}>
      {/* BEFORE panel */}
      <div className="flex-1 bg-[var(--et-bg-700)] rounded-lg p-4 border border-[var(--et-border)]">
        <div className="flex items-center gap-2 mb-3">
          <span className="px-2 py-0.5 text-[10px] font-bold rounded text-[#EF4444] bg-[#EF4444]/10">
            BEFORE
          </span>
        </div>
        {before.mockImage || <BeforeMockup />}
        <h3 className="mt-3 text-sm font-semibold text-[var(--et-text-secondary)]">
          {before.title}
        </h3>
        <p className="mt-1 text-[13px] text-[var(--et-text-muted)] leading-relaxed">
          {before.description}
        </p>
        {before.stats && (
          <div className="mt-3 space-y-1">
            {before.stats.map((stat, i) => (
              <div key={i} className="flex items-center gap-2 text-[12px] text-[var(--et-text-muted)]">
                <div className="w-1 h-1 rounded-full bg-[var(--et-border)]" />
                {stat}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Divider with arrow */}
      <div className="flex items-center justify-center w-8 shrink-0">
        <div className="flex flex-col items-center gap-2">
          <div className="w-px h-12 bg-[var(--et-border)]" />
          <div className="text-[var(--et-text-muted)]">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
          <div className="w-px h-12 bg-[var(--et-border)]" />
        </div>
      </div>

      {/* AFTER panel */}
      <div
        className={clsx(
          "flex-1 bg-[var(--et-bg-800)] rounded-lg p-4 border transition-all duration-300",
          "border-[var(--et-glass-border)]",
          "hover:border-[var(--et-blue)]/50 hover:shadow-[0_0_20px_rgba(0,123,255,0.2)]"
        )}
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="px-2 py-0.5 text-[10px] font-bold rounded text-[#10B981] bg-[#10B981]/10">
            AFTER
          </span>
        </div>
        {after.mockImage || <AfterMockup />}
        <h3 className="mt-3 text-sm font-semibold text-[var(--et-text-primary)]">
          {after.title}
        </h3>
        <p className="mt-1 text-[13px] text-[var(--et-text-muted)] leading-relaxed">
          {after.description}
        </p>
        {after.stats && (
          <div className="mt-3 space-y-1">
            {after.stats.map((stat, i) => (
              <div key={i} className="flex items-center gap-2 text-[12px] text-[var(--et-satisfaction)]">
                <div className="w-1 h-1 rounded-full bg-[var(--et-satisfaction)]" />
                {stat}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
