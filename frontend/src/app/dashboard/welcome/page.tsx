/* ────────────────────────────────────────────────
   Welcome Page - Post-signup onboarding with SDK key
   ──────────────────────────────────────────────── */

"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

type TabType = "html" | "nextjs" | "react";

export default function WelcomePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [sdkCopied, setSdkCopied] = useState(false);
  const [codeCopied, setCodeCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>("nextjs");
  const [signalReceived, setSignalReceived] = useState(false);
  const [polling, setPolling] = useState(true);

  const sdkKey = searchParams.get("sdk_key") || "";
  const email = searchParams.get("email") || "";
  const domain = searchParams.get("domain") || "";
  const merchantId = searchParams.get("merchant_id") || "";

  // Redirect if no SDK key (user refreshing or direct access)
  useEffect(() => {
    if (!sdkKey) {
      router.replace("/dashboard");
      return;
    }
  }, [sdkKey, router]);

  // Mark onboarding as complete (no automatic redirect)
  useEffect(() => {
    if (!sdkKey) return;

    const completeOnboarding = async () => {
      try {
        await fetch(`${API_BASE}/api/v1/auth/onboarding-complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
      } catch (err) {
        // Silently fail - user can continue
      } finally {
        setLoading(false);
      }
    };

    completeOnboarding();
  }, [sdkKey]);

  // Poll for first session signal
  useEffect(() => {
    if (!sdkKey || signalReceived) return;

    const checkForSignal = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/sessions`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          if (data.count > 0 || (data.sessions && data.sessions.length > 0)) {
            setSignalReceived(true);
            setPolling(false);
          }
        }
      } catch (err) {
        // Silently fail - user may not have installed yet
      }
    };

    const interval = setInterval(checkForSignal, 5000);
    return () => clearInterval(interval);
  }, [sdkKey, signalReceived]);

  const copySdkKey = useCallback(() => {
    navigator.clipboard.writeText(sdkKey);
    setSdkCopied(true);
    setTimeout(() => setSdkCopied(false), 2000);
  }, [sdkKey]);

  const copyCode = useCallback((code: string) => {
    navigator.clipboard.writeText(code);
    setCodeCopied(true);
    setTimeout(() => setCodeCopied(false), 2000);
  }, []);

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          background: "white",
        }}
      >
        <div style={{ fontSize: "14px", color: "#6B7280" }}>Setting up your workspace...</div>
      </div>
    );
  }

  // Code snippets with actual SDK key - UPDATED URLs
  const codeSnippets: Record<TabType, string> = {
    html: `<!-- Add before closing </head> tag -->
<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  window.EmoraTest.init({
    sdkKey: "${sdkKey}",
    apiUrl: "https://emoratest.com"
  });
</script>`,
    nextjs: `// Create: src/components/EmoraTestScript.tsx
"use client";

import Script from "next/script";
import { useEffect, useState } from "react";

export default function EmoraTestScript({ sdkKey }: { sdkKey: string }) {
  const [shouldInit, setShouldInit] = useState(false);

  useEffect(() => {
    // Prevent duplicate initialization
    if ((window as any).EmoraTest?.isInitialized?.()) {
      return;
    }
    setShouldInit(true);
  }, []);

  if (!sdkKey || !shouldInit) return null;

  return (
    <>
      <Script
        src="https://emoratest.com/static/sdk/emoratest.umd.js"
        strategy="afterInteractive"
        onReady={() => {
          if ((window as any).EmoraTest) {
            (window as any).EmoraTest.init({
              sdkKey: "${sdkKey}",
              apiUrl: "https://emoratest.com"
            });
          }
        }}
      />
    </>
  );
}

// Then in app/layout.tsx:
import EmoraTestScript from "@/components/EmoraTestScript";

<EmoraTestScript sdkKey={"${sdkKey}"} />`,
    react: `// In your root App component (index.tsx or App.tsx)
import { useEffect, useState } from 'react';

function App() {
  const [shouldLoad, setShouldLoad] = useState(false);

  useEffect(() => {
    // Prevent duplicate script initialization
    if (window.EmoraTest?.isInitialized?.()) {
      return;
    }
    setShouldLoad(true);
  }, []);

  useEffect(() => {
    if (!shouldLoad) return;

    const script = document.createElement('script');
    script.src = 'https://emoratest.com/static/sdk/emoratest.umd.js';
    // IMPORTANT: Do NOT set async=true - it will break initialization
    // Script must load before we try to call init()

    script.onload = () => {
      if (window.EmoraTest) {
        window.EmoraTest.init({
          sdkKey: "${sdkKey}",
          apiUrl: "https://emoratest.com"
        });
      }
    };

    document.head.appendChild(script);
  }, [shouldLoad]);

  return <YourApp />;
}`,
  };

  const tabs = [
    { id: "html" as TabType, label: "HTML (Any Site)" },
    { id: "nextjs" as TabType, label: "Next.js 14" },
    { id: "react" as TabType, label: "React" },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "white",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div style={{ width: "100%", maxWidth: "700px" }}>

        {/* STEP 1 — Welcome Header */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            textAlign: "center",
            marginBottom: "32px",
          }}
        >
          {/* Green checkmark circle */}
          <div
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "50%",
              background: "#10B981",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "24px",
            }}
          >
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>

          <h1
            style={{
              fontSize: "28px",
              fontWeight: "700",
              color: "#111318",
              margin: "0 0 8px 0",
              letterSpacing: "-0.3px",
            }}
          >
            You&apos;re in! Welcome to EmoraTest
          </h1>
          <p
            style={{
              fontSize: "16px",
              color: "#6B7280",
              margin: 0,
            }}
          >
            Your account is ready. Install the SDK to start tracking emotions.
          </p>
        </div>

        {/* Warning Banner */}
        <div
          style={{
            background: "#FFFBEB",
            border: "1.5px solid #F59E0B",
            borderRadius: "10px",
            padding: "12px 16px",
            marginBottom: "20px",
            display: "flex",
            alignItems: "flex-start",
            gap: "12px",
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#F59E0B"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ flexShrink: 0, marginTop: "1px" }}
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <p
            style={{
              fontSize: "14px",
              color: "#92400E",
              margin: 0,
              lineHeight: "1.4",
            }}
          >
            <strong>Save your SDK key now</strong> — it will never be shown again for security reasons. You can always find it in Settings → SDK.
          </p>
        </div>

        {/* SDK Key Display */}
        <div style={{ marginBottom: "24px" }}>
          <p
            style={{
              fontSize: "14px",
              fontWeight: "600",
              color: "#374151",
              marginBottom: "8px",
            }}
          >
            Your SDK Key
          </p>
          <div
            style={{
              position: "relative",
              background: "#1E2130",
              borderRadius: "10px",
              padding: "16px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <code
              style={{
                fontFamily: "monospace",
                fontSize: "14px",
                color: "#10B981",
                letterSpacing: "0.5px",
                wordBreak: "break-all",
              }}
            >
              {sdkKey}
            </code>
            <button
              onClick={copySdkKey}
              style={{
                background: "rgba(16, 185, 129, 0.15)",
                color: "#10B981",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                borderRadius: "6px",
                padding: "8px 14px",
                fontSize: "13px",
                fontWeight: "500",
                cursor: "pointer",
                transition: "all 150ms ease",
                flexShrink: 0,
                marginLeft: "12px",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(16, 185, 129, 0.25)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(16, 185, 129, 0.15)";
              }}
            >
              {sdkCopied ? "✓ Copied!" : "Copy Key"}
            </button>
          </div>
        </div>

        {/* Installation Tabs */}
        <div style={{ marginBottom: "24px" }}>
          <p
            style={{
              fontSize: "15px",
              fontWeight: "600",
              color: "#374151",
              marginBottom: "12px",
            }}
          >
            Install the SDK
          </p>
          <p
            style={{
              fontSize: "13px",
              color: "#6B7280",
              marginBottom: "16px",
            }}
          >
            Choose your platform and add the code to your site:
          </p>

          <div
            style={{
              display: "flex",
              gap: "4px",
              borderBottom: "1px solid #E5E7EB",
              marginBottom: "16px",
            }}
          >
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: activeTab === tab.id ? "white" : "#F3F4F6",
                  borderBottom: activeTab === tab.id ? "2px solid #007BFF" : "none",
                  color: activeTab === tab.id ? "#111318" : "#6B7280",
                  border: "none",
                  borderRadius: activeTab === tab.id ? "8px 8px 0 0" : "8px",
                  padding: "10px 20px",
                  fontSize: "14px",
                  fontWeight: "500",
                  cursor: "pointer",
                  transition: "all 150ms ease",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div
            style={{
              position: "relative",
              background: "#1E2130",
              borderRadius: "10px",
              padding: "20px",
              overflow: "hidden",
            }}
          >
            <pre
              style={{
                margin: 0,
                fontFamily: "monospace",
                fontSize: "12px",
                color: "#E2E8F0",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                lineHeight: "1.5",
              }}
            >
              {codeSnippets[activeTab]}
            </pre>
            <button
              onClick={() => copyCode(codeSnippets[activeTab])}
              style={{
                position: "absolute",
                bottom: "12px",
                right: "12px",
                background: codeCopied ? "#10B981" : "rgba(255, 255, 255, 0.1)",
                color: "white",
                border: "none",
                borderRadius: "6px",
                padding: "6px 12px",
                fontSize: "12px",
                fontWeight: "500",
                cursor: "pointer",
                transition: "background 150ms ease",
              }}
              onMouseEnter={(e) => {
                if (!codeCopied) {
                  e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
                }
              }}
              onMouseLeave={(e) => {
                if (!codeCopied) {
                  e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)";
                }
              }}
            >
              {codeCopied ? "✓ Copied!" : "Copy Code"}
            </button>
          </div>

          <div
            style={{
              fontSize: "12px",
              color: "#6B7280",
              marginTop: "12px",
              padding: "12px",
              background: "#F9FAFB",
              borderRadius: "8px",
              border: "1px solid #E5E7EB",
            }}
          >
            <p style={{ margin: 0, lineHeight: "1.5" }}>
              <strong>Tip:</strong> After installing, visit your website and check back here. We&apos;ll automatically detect when the first session is recorded.
            </p>
          </div>
        </div>

        {/* Verification Status Card */}
        <div
          style={{
            background: "white",
            border: "1px solid #E5E7EB",
            borderRadius: "12px",
            padding: "20px 24px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          {polling && !signalReceived ? (
            <>
              {/* Pulsing dot */}
              <div
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  background: "#9CA3AF",
                  position: "relative",
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    borderRadius: "50%",
                    background: "#9CA3AF",
                    animation: "pulse 1.5s ease-in-out infinite",
                  }}
                />
              </div>
              <div>
                <p
                  style={{
                    fontSize: "15px",
                    fontWeight: "500",
                    color: "#374151",
                    margin: "0 0 4px 0",
                  }}
                >
                  Waiting for first signal...
                </p>
                <p
                  style={{
                    fontSize: "13px",
                    color: "#6B7280",
                    margin: 0,
                  }}
                >
                  Install the SDK and visit your website. We&apos;ll detect it automatically.
                </p>
              </div>
            </>
          ) : (
            <>
              {/* Green checkmark */}
              <div
                style={{
                  width: "24px",
                  height: "24px",
                  borderRadius: "50%",
                  background: "#10B981",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div style={{ flex: 1 }}>
                <p
                  style={{
                    fontSize: "15px",
                    fontWeight: "500",
                    color: "#374151",
                    margin: "0 0 4px 0",
                  }}
                >
                  SDK is working!
                </p>
                <p
                  style={{
                    fontSize: "13px",
                    color: "#6B7280",
                    margin: 0,
                  }}
                >
                  Your emotion data is flowing in. Go to your dashboard to see it.
                </p>
              </div>
              <a
                href="/dashboard"
                style={{
                  background: "linear-gradient(135deg, #007BFF, #7C3AED)",
                  color: "white",
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 20px",
                  fontSize: "14px",
                  fontWeight: "500",
                  textDecoration: "none",
                  display: "inline-block",
                  transition: "opacity 150ms ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.opacity = "0.88";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.opacity = "1";
                }}
              >
                Go to Dashboard →
              </a>
            </>
          )}
        </div>

        {/* Bottom CTA */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px",
            marginBottom: "16px",
          }}
        >
          <a
            href="/dashboard"
            style={{
              background: "linear-gradient(135deg, #007BFF, #7C3AED)",
              color: "white",
              border: "none",
              borderRadius: "10px",
              padding: "14px 32px",
              fontSize: "15px",
              fontWeight: "600",
              textDecoration: "none",
              display: "inline-block",
              transition: "opacity 150ms ease, transform 150ms ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = "0.88";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = "1";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            Go to Dashboard →
          </a>
          <a
            href="/docs"
            style={{
              fontSize: "13px",
              color: "#9CA3AF",
              textDecoration: "none",
            }}
          >
            Read the full documentation
          </a>
        </div>

        <p
          style={{
            fontSize: "12px",
            color: "#9CA3AF",
            textAlign: "center",
            margin: 0,
          }}
        >
          Need help? Email us at <a href="mailto:hello@emoratest.com" style={{ color: "#007BFF", textDecoration: "none" }}>hello@emoratest.com</a>
        </p>

        {/* Pulse animation keyframes */}
        <style jsx>{`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
              transform: scale(1);
            }
            50% {
              opacity: 0.5;
              transform: scale(1.5);
            }
          }
        `}</style>

      </div>
    </div>
  );
}
