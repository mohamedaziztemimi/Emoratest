/* ────────────────────────────────────────────────────────
   PulsingDot - Live indicator with concentric ring animations
   ──────────────────────────────────────────────────────── */

import { clsx } from "clsx";

interface PulsingDotProps {
  color: string;
  size?: number;
  label?: string;
  className?: string;
}

export function PulsingDot({
  color,
  size = 8,
  label,
  className,
}: PulsingDotProps) {
  const ringSize = size * 3;

  return (
    <div className={clsx("inline-flex items-center gap-2", className)}>
      <div className="relative flex items-center justify-center">
        {/* Inner solid dot */}
        <div
          className="rounded-full z-10 relative"
          style={{
            backgroundColor: color,
            width: `${size}px`,
            height: `${size}px`,
          }}
        />

        {/* Ring 1 */}
        <div
          className="absolute rounded-full animate-ping"
          style={{
            backgroundColor: color,
            width: `${ringSize}px`,
            height: `${ringSize}px`,
            opacity: 0.3,
            animationDuration: "2s",
          }}
        />

        {/* Ring 2 - Staggered */}
        <div
          className="absolute rounded-full animate-ping"
          style={{
            backgroundColor: color,
            width: `${ringSize}px`,
            height: `${ringSize}px`,
            opacity: 0.15,
            animationDelay: "1s",
            animationDuration: "2s",
          }}
        />
      </div>

      {label && (
        <span
          className="text-[12px] font-medium uppercase tracking-wider"
          style={{ color }}
        >
          {label}
        </span>
      )}
    </div>
  );
}
