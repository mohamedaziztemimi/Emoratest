/* ────────────────────────────────────────────────────────
   StatCard - Stats display with animated counter
   ──────────────────────────────────────────────────────── */

"use client";

import { clsx } from "clsx";
import { ReactNode, useEffect, useState } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  delta?: string;
  deltaPositive?: boolean;
  icon?: ReactNode;
  animate?: boolean;
  className?: string;
}

// Animated counter hook
function useAnimatedCounter(
  target: number,
  duration: number = 1200,
  start: number = 0
) {
  const [current, setCurrent] = useState(start);

  useEffect(() => {
    if (target === start) {
      setCurrent(target);
      return;
    }

    let startTime: number | null = null;
    let animationFrameId: number;

    const animate = (timestamp: number) => {
      if (startTime === null) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const newValue = start + (target - start) * easeOut;

      setCurrent(newValue);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [target, duration, start]);

  return current;
}

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  start?: number;
  className?: string;
}

function AnimatedCounter({
  value,
  duration = 1200,
  start = 0,
  className,
}: AnimatedCounterProps) {
  const current = useAnimatedCounter(value, duration, start);

  return (
    <span className={className}>
      {Math.round(current).toLocaleString()}
    </span>
  );
}

export function StatCard({
  label,
  value,
  delta,
  deltaPositive,
  icon,
  animate = true,
  className,
}: StatCardProps) {
  const isNumeric = typeof value === "number";

  return (
    <div className={clsx(
      "bg-[var(--et-glass-bg)]",
      "backdrop-blur-[var(--et-glass-blur)]",
      "border border-[var(--et-glass-border)]",
      "rounded-[var(--et-radius-lg)]",
      "p-4",
      className
    )}>
      {/* Label + Icon */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-[12px] text-[var(--et-text-muted)] font-medium">
          {label}
        </span>
        {icon && <div className="text-[var(--et-text-secondary)]">{icon}</div>}
      </div>

      {/* Value */}
      <div className="text-[32px] font-bold text-[var(--et-text-primary)] mb-1">
        {isNumeric && animate ? (
          <AnimatedCounter value={value} />
        ) : (
          value
        )}
      </div>

      {/* Delta Badge */}
      {delta && (
        <div
          className={clsx(
            "inline-flex items-center px-2 py-0.5 rounded-[var(--et-radius-sm)] text-[12px] font-medium",
            deltaPositive
              ? "bg-[var(--et-satisfaction)]/20 text-[var(--et-satisfaction)]"
              : "bg-[var(--et-frustration)]/20 text-[var(--et-frustration)]"
          )}
        >
          {deltaPositive && "↑"}
          {!deltaPositive && "↓"}
          {delta}
        </div>
      )}
    </div>
  );
}

export { AnimatedCounter, useAnimatedCounter };
