/* ────────────────────────────────────────────────────────
   Cookie Consent Banner - GDPR compliance
   ──────────────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";

const CONSENT_STORAGE_KEY = "emoratest_consent";

export type ConsentChoice = "accepted" | "rejected" | null;

interface CookieConsentBannerProps {
  /** Override the default storage key */
  storageKey?: string;
}

/** Get current consent choice from localStorage */
export function getConsentChoice(): ConsentChoice {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(CONSENT_STORAGE_KEY) as ConsentChoice;
  } catch {
    return null;
  }
}

/** Set consent choice in localStorage */
export function setConsentChoice(choice: "accepted" | "rejected"): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CONSENT_STORAGE_KEY, choice);
  } catch {
    // localStorage might be disabled
  }
}

/** Cookie consent banner with Accept/Reject buttons */
export function CookieConsentBanner({ storageKey = CONSENT_STORAGE_KEY }: CookieConsentBannerProps = {}) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user has already made a choice
    try {
      const existing = localStorage.getItem(storageKey);
      if (!existing) {
        setIsVisible(true);
      }
    } catch {
      setIsVisible(true);
    }
  }, [storageKey]);

  const handleAccept = () => {
    try {
      localStorage.setItem(storageKey, "accepted");
    } catch {
      // localStorage disabled, just hide banner
    }
    setIsVisible(false);
  };

  const handleReject = () => {
    try {
      localStorage.setItem(storageKey, "rejected");
    } catch {
      // localStorage disabled, just hide banner
    }
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div
      className="px-4 sm:px-6"
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        background: "rgba(255, 255, 255, 0.95)",
        backdropFilter: "blur(10px)",
        borderTop: "1px solid #E5E7EB",
        padding: "12px 16px",
        boxShadow: "0 -4px 20px rgba(0, 0, 0, 0.08)",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
          gap: "12px",
        }}
        className="sm:flex-row sm:items-center sm:gap-4"
      >
        <p
          style={{
            flex: 1,
            fontSize: "13px",
            color: "#374151",
            margin: 0,
            minWidth: "200px",
            lineHeight: "1.5",
          }}
          className="sm:text-sm"
        >
          We use essential cookies for authentication. By using EmoraTest, you agree to our{" "}
          <a href="/privacy" style={{ color: "#007BFF", textDecoration: "none" }}>
            Privacy Policy
          </a>
          .
        </p>

        <div style={{ display: "flex", gap: "8px", flexShrink: 0 }} className="sm:gap-3 w-full sm:w-auto">
          <button
            onClick={handleReject}
            className="flex-1 sm:flex-none"
            style={{
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: "500",
              color: "#374151",
              background: "white",
              border: "1px solid #E5E7EB",
              borderRadius: "8px",
              cursor: "pointer",
              transition: "all 150ms ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#F9FAFB";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "white";
            }}
          >
            Reject
          </button>
          <button
            onClick={handleAccept}
            className="flex-1 sm:flex-none"
            style={{
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: "500",
              color: "white",
              background: "linear-gradient(135deg, #007BFF, #7C3AED)",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              transition: "all 150ms ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = "0.9";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = "1";
            }}
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
