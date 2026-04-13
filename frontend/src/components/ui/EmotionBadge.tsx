/* ────────────────────────────────────────────────────────
   EmotionBadge - Emotion type badge with score
   ──────────────────────────────────────────────────────── */

import { clsx } from "clsx";
import { EMOTION_CONFIG, getEmotionConfig } from "@/lib/theme";

export type EmotionType =
  | "confusion"
  | "frustration"
  | "delight"
  | "anxiety"
  | "satisfaction"
  | "hesitation"
  | "focus"
  | "boredom";

type BadgeSize = "sm" | "md";

interface EmotionBadgeProps {
  emotion: EmotionType | string;
  score?: number;
  size?: BadgeSize;
  pulse?: boolean;
}

const sizeClasses: Record<BadgeSize, { text: string; dot: string }> = {
  sm: { text: "text-[11px]", dot: "w-1.5 h-1.5" },
  md: { text: "text-[13px]", dot: "w-2 h-2" },
};

export function EmotionBadge({
  emotion,
  score,
  size = "md",
  pulse = false,
}: EmotionBadgeProps) {
  const config = getEmotionConfig(emotion);
  const sizeConfig = sizeClasses[size];

  return (
    <div className={clsx(
      "inline-flex items-center gap-2",
      sizeConfig.text
    )}>
      <div
        className={clsx(
          "rounded-full shrink-0",
          sizeConfig.dot,
          pulse && "animate-pulse-emotion"
        )}
        style={{ backgroundColor: config.color }}
      />
      <span
        className="font-medium"
        style={{ color: config.color }}
      >
        {config.label}
      </span>
      {score !== undefined && (
        <span className="text-[var(--et-text-muted)]">
          {score}%
        </span>
      )}
    </div>
  );
}
