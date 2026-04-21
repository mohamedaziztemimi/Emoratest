/* ────────────────────────────────────────────────
   GlassCard - Simple card component for light mode
   ──────────────────────────────────────────────── */

import { clsx } from "clsx";
import { ReactNode } from "react";

type GlowType = "blue" | "purple" | "none";
type PaddingSize = "sm" | "md" | "lg";

export interface GlassCardProps {
  children: ReactNode;
  className?: string;
  glow?: GlowType;
  hover?: boolean;
  padding?: PaddingSize;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
}

const paddingClasses: Record<PaddingSize, string> = {
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
};

const glowClasses: Record<GlowType, string> = {
  blue: "hover:shadow-[0_8px_30px_rgba(0,123,255,0.15)]",
  purple: "hover:shadow-[0_8px_30px_rgba(124,58,237,0.15)]",
  none: "",
};

export function GlassCard({
  children,
  className,
  glow = "none",
  hover = true,
  padding = "md",
  onClick,
}: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        "bg-white",
        "border border-gray-200",
        "rounded-2xl",
        "transition-all duration-200",
        hover && [
          "hover:-translate-y-[2px]",
          "hover:shadow-lg",
          glowClasses[glow],
        ],
        paddingClasses[padding],
        className
      )}
    >
      {children}
    </div>
  );
}
