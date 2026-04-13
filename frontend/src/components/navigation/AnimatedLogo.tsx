/* ────────────────────────────────────────────────
   AnimatedLogo - EmoraTest "E" logo with animations
   ──────────────────────────────────────────────── */

interface AnimatedLogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function AnimatedLogo({ className = "", size = "md" }: AnimatedLogoProps) {
  const sizes = {
    sm: "w-8 h-8 text-base",
    md: "w-9 h-9 text-lg",
    lg: "w-10 h-10 text-xl",
  };

  return (
    <div className={`relative ${sizes[size]} ${className}`}>
      {/* Animated gradient background */}
      <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 animate-gradient-shift" />

      {/* Rotating border ring */}
      <div className="absolute -inset-1 rounded-lg bg-gradient-to-r from-blue-400 via-purple-500 to-blue-400 opacity-60 animate-spin-slow blur-[2px]" />

      {/* Letter E */}
      <div className="relative w-full h-full rounded-lg flex items-center justify-center text-white font-bold">
        E
      </div>
    </div>
  );
}
