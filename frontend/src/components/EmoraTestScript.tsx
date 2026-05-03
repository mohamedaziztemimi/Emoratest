"use client";

import { useEffect } from "react";

export default function EmoraTestScript({ sdkKey }: { sdkKey: string }) {
  useEffect(() => {
    if (!sdkKey) return;

    // Prevent duplicate script
    if (document.querySelector('script[src*="emoratest.umd.js"]')) {
      if ((window as any).EmoraTest) {
        (window as any).EmoraTest.init({
          sdkKey,
          apiUrl: "https://emoratest.com",
          requireConsent: true, // Wait for user to accept consent banner
        });
      }
      return;
    }

    const script = document.createElement("script");
    script.src = "https://emoratest.com/static/sdk/emoratest.umd.js";
    script.async = true;

    script.onload = () => {
      if ((window as any).EmoraTest) {
        (window as any).EmoraTest.init({
          sdkKey,
          apiUrl: "https://emoratest.com",
          requireConsent: true, // Wait for user to accept consent banner
        });
      }
    };

    document.body.appendChild(script);

    return () => {
      // optional cleanup (keep script if you want persistence)
    };
  }, [sdkKey]);

  return null;
}
