/* ────────────────────────────────────────────────
   LazySection - Simple fade-in on scroll (fixed - content never disappears)
   ──────────────────────────────────────────────── */

"use client";

import { useEffect, useRef, useState } from "react";

export interface LazySectionProps {
  children: React.ReactNode;
  className?: string;
  threshold?: number;
}

export function LazySection({
  children,
  className = "",
  threshold = 0.1,
}: LazySectionProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [hasAnimated, setHasAnimated] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, [threshold, hasAnimated]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        opacity: 1,
        transform: hasAnimated ? "translateY(0)" : "translateY(16px)",
        transition: hasAnimated ? "opacity 500ms ease, transform 500ms ease" : "none",
      }}
    >
      {children}
    </div>
  );
}
