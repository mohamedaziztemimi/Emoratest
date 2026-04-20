/* ────────────────────────────────────────────────
   Auth Layout - Clean centered design
   ──────────────────────────────────────────────── */

import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: {
    default: "EmoraTest",
    template: "%s | EmoraTest",
  },
  icons: {
    icon: "/logo2.png",
    shortcut: "/logo2.png",
    apple: "/logo2.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#7C3AED",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* DM Sans Font */}
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap"
        rel="stylesheet"
      />

      <div
        style={{
          minHeight: "100vh",
          background: "#F5F5F7",
          fontFamily: "'DM Sans', sans-serif",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px",
          position: "relative",
        }}
      >
        {/* Subtle radial glow at top center */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "500px",
            background:
              "radial-gradient(ellipse 800px 400px at 50% -100px, rgba(124,58,237,0.07) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />
        {children}
      </div>
    </>
  );
}
