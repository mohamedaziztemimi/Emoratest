/* ────────────────────────────────────────────────
   AnimatedLogo - EmoraTest logo with pulse animation
   ──────────────────────────────────────────────── */

interface AnimatedLogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function AnimatedLogo({ className = "", size = "md" }: AnimatedLogoProps) {
  const sizes = {
    sm: "w-8 h-8",
    md: "w-9 h-9",
    lg: "w-10 h-10",
  };

  return (
    <div className={`relative ${sizes[size]} ${className}`}>
      {/* Logo image */}
      <img
        src="/logo.png"
        alt="EmoraTest"
        className="w-full h-full object-contain"
      />

      {/* Pulse animation ring */}
      <div className="absolute inset-0 rounded-full animate-ping-slow">
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-[#007BFF] to-[#7C3AED] opacity-20 blur-md" />
      </div>
    </div>
  );
}
