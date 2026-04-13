/* ────────────────────────────────────────────────────────
   StickyAuditBar - Fixed bottom CTA bar with dismiss
   ──────────────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "et_audit_dismissed";

export function StickyAuditBar() {
  const [isVisible, setIsVisible] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Check if previously dismissed
    const dismissed = localStorage.getItem(STORAGE_KEY) === "true";
    setIsDismissed(dismissed);

    // Check if mobile
    setIsMobile(window.innerWidth < 640);

    // Show after 2.5s delay
    const showTimer = setTimeout(() => {
      if (!dismissed) {
        setIsVisible(true);
      }
    }, 2500);

    // Handle resize
    const handleResize = () => {
      setIsMobile(window.innerWidth < 640);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      clearTimeout(showTimer);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem(STORAGE_KEY, "true");
    // Re-allow showing after 7 days
    setTimeout(() => {
      localStorage.removeItem(STORAGE_KEY);
    }, 7 * 24 * 60 * 60 * 1000);
  };

  if (isDismissed || !isVisible) {
    return null;
  }

  return (
    <div
      className={`
        fixed bottom-0 left-0 right-0 z-40 h-14
        bg-gradient-to-r from-[#007BFF] to-[#7C3AED]
        transition-transform duration-300 ease-out
        ${isVisible ? "translate-y-0" : "translate-y-full"}
      `}
    >
      <div className="container mx-auto px-4 h-full">
        <div className="flex items-center justify-between h-full max-w-5xl mx-auto">
          {/* Text content */}
          <div className="flex items-center gap-3">
            <span className="text-base">{/* Search emoji */}🔍</span>
            {isMobile ? (
              <span className="text-white text-sm font-medium">
                Free Emotion Audit
              </span>
            ) : (
              <span className="text-white text-sm">
                Get Your Free Emotion Audit — See What's Killing Your Conversions
              </span>
            )}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* CTA button */}
            <a
              href="/audit"
              className={`
                px-4 py-2 rounded-full text-sm font-medium text-[#007BFF]
                bg-white hover:bg-white/90 transition-colors duration-200
                ${isMobile ? "hidden sm:inline-block" : "inline-block"}
              `}
            >
              Start Free →
            </a>

            {/* Dismiss button */}
            <button
              onClick={handleDismiss}
              className="w-8 h-8 rounded-full flex items-center justify-center text-white/80 hover:text-white hover:bg-white/10 transition-colors duration-200"
              aria-label="Dismiss"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
