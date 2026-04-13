/* ────────────────────────────────────────────────────────
   ScrollProgressBar - Top scroll progress indicator
   ──────────────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";

export function ScrollProgressBar() {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      setScrollProgress(Math.min(progress, 100));
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div
      className="fixed top-0 left-0 right-0 h-[2px] z-[100] transition-all duration-150"
      style={{
        background: `linear-gradient(90deg, var(--et-blue), var(--et-purple), transparent)`,
        width: `${scrollProgress}%`,
      }}
    />
  );
}
