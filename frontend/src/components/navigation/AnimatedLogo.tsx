/* ────────────────────────────────────────────────
   AnimatedLogo - Simple "E" logo with subtle animation
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
    <div className={`${sizes[size]} ${className}`}>
      <div className="w-full h-full rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold animate-bounce-slight">
        E
      </div>
    </div>
  );
}
