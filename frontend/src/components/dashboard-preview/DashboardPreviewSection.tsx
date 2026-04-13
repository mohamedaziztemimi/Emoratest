/* ────────────────────────────────────────────────────────
   DashboardPreviewSection - Interactive product preview section
   ──────────────────────────────────────────────────────── */

"use client";

import { useEffect, useState, useRef } from "react";
import { GradientButton } from "../ui";
import { MiniDashboard } from "./MiniDashboard";

const BULLET_POINTS = [
  "Real-time emotion detection on every session",
  "Auto-generated test variants powered by ML",
  "Statistically sound results with SRM protection",
];

// Check for UTM/referrer personalization
const getPersonalizedHeadline = (): { main: string; sub: string } => {
  if (typeof window === "undefined") {
    return {
      main: "Your Clarity Center. Live.",
      sub: "See what users feel, not just what they click.",
    };
  }

  const referrer = document.referrer.toLowerCase();

  if (referrer.includes("linkedin")) {
    return {
      main: "For Growth Teams: Bandit Tests + Emotion Insights",
      sub: "Turn every session into a conversion optimization opportunity.",
    };
  }

  if (referrer.includes("twitter") || referrer.includes("x.com")) {
    return {
      main: "A/B Testing, But It Actually Works",
      sub: "Emotion ML explains the why behind the drop-off.",
    };
  }

  if (referrer.includes("producthunt")) {
    return {
      main: "Product Hunt Exclusive: Try EmoraTest Free",
      sub: "First 100 teams get unlimited emotion heatmaps.",
    };
  }

  return {
    main: "Your Clarity Center. Live.",
    sub: "See what users feel, not just what they click.",
  };
};

export function DashboardPreviewSection() {
  const [isVisible, setIsVisible] = useState(false);
  const [personalization, setPersonalization] = useState(getPersonalizedHeadline());
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.2 }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      if (containerRef.current) {
        observer.unobserve(containerRef.current);
      }
    };
  }, []);

  return (
    <section className="py-24 bg-[var(--et-bg-900)] min-h-[500px] relative overflow-hidden">
      {/* Grid background pattern */}
      <div
        className="absolute inset-0 -z-10 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />

      <div className="container mx-auto px-4 light-mode text-[var(--et-text-primary)]">
        <div className="grid lg:grid-cols-12 gap-8 lg:gap-16 items-center">
          {/* Left side - Content (45%) */}
          <div className="lg:col-span-5">
            <h2 className="text-[clamp(28px,4vw,42px)] font-bold text-[var(--et-text-primary)] mb-4">
              {personalization.main}
            </h2>
            <p className="text-[18px] text-[var(--et-text-muted)] mb-8 leading-relaxed">
              {personalization.sub}
            </p>

            {/* Bullet points */}
            <div className="space-y-4 mb-8">
              {BULLET_POINTS.map((point, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3"
                  style={{
                    opacity: isVisible ? 1 : 0,
                    transform: isVisible ? "translateX(0)" : "translateX(-20px)",
                    transition: `opacity 0.4s ease-out ${index * 100}ms, transform 0.4s ease-out ${index * 100}ms`,
                  }}
                >
                  <div className="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-[var(--et-blue)] to-[var(--et-purple)] flex items-center justify-center mt-0.5">
                    <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-[15px] text-[var(--et-text-secondary)] leading-relaxed">
                    {point}
                  </span>
                </div>
              ))}
            </div>

            {/* CTA button */}
            <GradientButton variant="primary" size="lg" glow href="/dashboard">
              Explore Full Dashboard
            </GradientButton>
          </div>

          {/* Right side - MiniDashboard (55%) */}
          <div
            ref={containerRef}
            className="lg:col-span-7"
            style={{
              opacity: isVisible ? 1 : 0,
              transform: isVisible ? "translateX(0)" : "translateX(50px)",
              transition: "opacity 0.4s ease-out 200ms, transform 0.4s ease-out 200ms",
            }}
          >
            <MiniDashboard className="max-w-[680px] mx-auto shadow-glow-blue" />
          </div>
        </div>
      </div>
    </section>
  );
}
