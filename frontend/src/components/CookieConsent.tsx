"use client";

import { useEffect, useState } from "react";

const CONSENT_KEY = "emoratest_consent";
const CONSENT_COOKIE_NAME = "emoratest_consent";

type ConsentStatus = "accepted" | "rejected" | null;

function setConsentCookie(value: "accepted" | "rejected") {
  const maxAge = 31536000; // 1 year
  document.cookie = `${CONSENT_COOKIE_NAME}=${value}; max-age=${maxAge}; path=/`;
  localStorage.setItem(CONSENT_KEY, value);
}

export function getConsentStatus(): ConsentStatus {
  // Check localStorage first (faster)
  const stored = localStorage.getItem(CONSENT_KEY);
  if (stored === "accepted" || stored === "rejected") {
    return stored;
  }

  // Fall back to checking cookie
  const cookies = document.cookie.split(";").map((c) => c.trim());
  const consentCookie = cookies.find((c) => c.startsWith(`${CONSENT_COOKIE_NAME}=`));
  if (consentCookie) {
    const value = consentCookie.split("=")[1] as ConsentStatus;
    if (value === "accepted" || value === "rejected") {
      localStorage.setItem(CONSENT_KEY, value);
      return value;
    }
  }

  return null;
}

export function CookieConsent() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Only show if no consent decision exists
    const status = getConsentStatus();
    if (!status) {
      setIsVisible(true);
    }
  }, []);

  if (!isVisible) return null;

  const handleAccept = () => {
    setConsentCookie("accepted");
    setIsVisible(false);

    // Enable SDK tracking if it loaded but was waiting for consent
    if (typeof window !== "undefined" && (window as any).EmoraTest) {
      (window as any).EmoraTest.enableTracking?.();
    }
  };

  const handleReject = () => {
    setConsentCookie("rejected");
    setIsVisible(false);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 rounded-t-2xl shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <p className="text-sm text-gray-600 flex-1">
            We use cookies and behavioral tracking to analyze user experience.
            By clicking Accept, you consent to the processing of behavioral data
            (mouse movements, clicks, scrolls) as described in our{" "}
            <a href="/privacy" className="text-[#007BFF] hover:underline">
              Privacy Policy
            </a>
            .
          </p>
          <div className="flex items-center gap-3 flex-shrink-0">
            <a
              href="/privacy"
              className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2"
            >
              Privacy Policy
            </a>
            <button
              onClick={handleReject}
              className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Reject
            </button>
            <button
              onClick={handleAccept}
              className="px-4 py-2 text-sm font-medium text-white bg-[#007BFF] rounded-lg hover:bg-[#0069D9] transition-colors"
            >
              Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
