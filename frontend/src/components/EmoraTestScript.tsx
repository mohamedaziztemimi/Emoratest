"use client";

import Script from "next/script";

export default function EmoraTestScript({ sdkKey }: { sdkKey: string }) {
  if (!sdkKey) return null;

  return (
    <Script
      src="https://emoratest.com/static/sdk/emoratest.umd.js"
      strategy="afterInteractive"
      onLoad={() => {
        if (typeof window !== "undefined" && (window as any).EmoraTest) {
          (window as any).EmoraTest.init({
            sdkKey,
            apiUrl: "https://emoratest.com",
          });
        }
      }}
    />
  );
}
