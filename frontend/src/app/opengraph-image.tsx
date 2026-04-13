/* ────────────────────────────────────────────────────────
   OpenGraph Image - Dynamic OG image for social sharing
   ──────────────────────────────────────────────────────── */

import { ImageResponse } from "next/og";

export const runtime = "edge";

export const size = {
  width: 1200,
  height: 630,
};

export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          width: "100%",
          height: "100%",
          backgroundColor: "#0A0B0F",
          fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        }}
      >
        {/* Top section: Logo + Main text */}
        <div style={{ padding: "60px 60px 40px" }}>
          {/* Logo */}
          <div
            style={{
              fontSize: "24px",
              fontWeight: "700",
              color: "#FFFFFF",
              marginBottom: "40px",
            }}
          >
            EmoraTest
          </div>

          {/* Main text */}
          <div
            style={{
              fontSize: "56px",
              fontWeight: "700",
              lineHeight: 1.1,
              marginBottom: "16px",
            }}
          >
            <span style={{ color: "#FFFFFF" }}>Unlock Emotions,</span>
            <br />
            <span
              style={{
                background: "linear-gradient(135deg, #007BFF 0%, #7C3AED 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Win Tests
            </span>
          </div>

          {/* Subtext */}
          <div
            style={{
              fontSize: "24px",
              color: "#9CA3B8",
              marginTop: "16px",
            }}
          >
            Emotion ML + A/B Testing Platform
          </div>
        </div>

        {/* Right side: Simplified heatmap graphic */}
        <div
          style={{
            position: "absolute",
            right: "60px",
            top: "50%",
            transform: "translateY(-50%)",
            width: "320px",
            height: "240px",
            backgroundColor: "#1E2130",
            borderRadius: "16px",
            border: "1px solid rgba(255,255,255,0.1)",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          {/* Mock header */}
          <div
            style={{
              width: "100%",
              height: "20px",
              backgroundColor: "#111318",
              borderRadius: "8px",
              marginBottom: "8px",
            }}
          />

          {/* Heatmap dots - simplified representation */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {Array.from({ length: 36 }).map((_, i) => {
              const colors = ["#007BFF", "#7C3AED", "#F59E0B", "#10B981"];
              const color = colors[Math.floor(Math.random() * colors.length)];
              return (
                <div
                  key={i}
                  style={{
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    backgroundColor: color,
                    opacity: 0.6 + Math.random() * 0.4,
                  }}
                />
              );
            })}
          </div>

          {/* Stats bar */}
          <div
            style={{
              marginTop: "auto",
              height: "40px",
              backgroundColor: "rgba(0, 123, 255, 0.15)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#007BFF",
              fontSize: "14px",
              fontWeight: "600",
            }}
          >
            +32% conversion lift
          </div>
        </div>

        {/* Bottom stats */}
        <div
          style={{
            padding: "40px 60px 60px",
            display: "flex",
            gap: "40px",
          }}
        >
          {[
            { label: "85-95%", sub: "Accuracy" },
            { label: "40%", sub: "Less Churn" },
            { label: "30-50%", sub: "Faster Winners" },
          ].map((stat, i) => (
            <div key={i} style={{ display: "flex", flexDirection: "column" }}>
              <div
                style={{
                  fontSize: "28px",
                  fontWeight: "700",
                  background: "linear-gradient(135deg, #007BFF 0%, #7C3AED 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {stat.label}
              </div>
              <div style={{ fontSize: "14px", color: "#9CA3B8", marginTop: "4px" }}>
                {stat.sub}
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}
