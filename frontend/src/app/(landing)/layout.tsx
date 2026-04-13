/* ────────────────────────────────────────────────────────
   Landing Page Layout - Navbar + AuditBar (no html/body tags)
   ──────────────────────────────────────────────────────── */

"use client";

import { Inter, Figtree } from "next/font/google";
import "../../styles/emoratest-tokens.css";
import { Navbar } from "@/components/navigation/Navbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const figtree = Figtree({
  subsets: ["latin"],
  variable: "--font-figtree",
  display: "swap",
});

// UTM capture component
function UTMCapture() {
  if (typeof window === "undefined") return null;

  const urlParams = new URLSearchParams(window.location.search);
  const utmParams: Record<string, string> = {};

  ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"].forEach(
    (param) => {
      const value = urlParams.get(param);
      if (value) {
        utmParams[param] = value;
      }
    }
  );

  if (Object.keys(utmParams).length > 0) {
    // Store in sessionStorage for personalization
    try {
      const existing = JSON.parse(sessionStorage.getItem("et_utm") || "{}");
      sessionStorage.setItem("et_utm", JSON.stringify({ ...existing, ...utmParams }));
    } catch {
      // SessionStorage not available
    }
  }

  // Store referrer
  if (document.referrer) {
    try {
      sessionStorage.setItem("et_referrer", document.referrer);
    } catch {
      // SessionStorage not available
    }
  }

  return null;
}

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={`${inter.variable} ${figtree.variable} font-sans bg-white text-[#111318] min-h-screen`}>
      <UTMCapture />
      <Navbar />
      <main className="min-h-screen">
        {children}
      </main>
    </div>
  );
}
