"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authCompleteOnboarding } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Platform = "html" | "react" | "vue" | "shopify" | "wordpress" | "gtm";

const STEPS = ["Welcome", "Your SDK Key", "Install SDK", "Verify", "Done"];

export default function OnboardingPage() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [completing, setCompleting] = useState(false);
  const [platform, setPlatform] = useState<Platform>("html");
  const [verifying, setVerifying] = useState(false);
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  const sdkKey = typeof window !== "undefined"
    ? localStorage.getItem("emoratest_sdk_key") || ""
    : "";

  const handleComplete = useCallback(async () => {
    setCompleting(true);
    try {
      await authCompleteOnboarding();
      await refresh();
      router.push("/dashboard");
    } catch {
      router.push("/dashboard");
    }
  }, [refresh, router]);

  const handleVerify = useCallback(async () => {
    setVerifying(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${apiUrl}/api/v1/dashboard/stats`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        if (data.total_sessions > 0) {
          setVerified(true);
          setTimeout(() => setStep(4), 1000);
        }
      }
    } catch {
      // Silent fail
    } finally {
      setVerifying(false);
    }
  }, []);

  if (loading || !user) return null;

  const codeSnippets: Record<Platform, string> = {
    html: `<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "${sdkKey}" });
</script>`,
    react: `"use client";
import { useEffect } from "react";

export default function EmoraTracker() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://emoratest.com/static/sdk/emoratest.umd.js";
    script.async = true;
    script.onload = () => {
      window.EmoraTest?.init({ sdkKey: "${sdkKey}" });
    };
    document.body.appendChild(script);
  }, []);
  return null;
}

// Add <EmoraTracker /> to your root layout.`,
    vue: `<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  const script = document.createElement('script');
  script.src = 'https://emoratest.com/static/sdk/emoratest.umd.js';
  script.async = true;
  script.onload = () => {
    window.EmoraTest?.init({ sdkKey: '${sdkKey}' });
  };
  document.body.appendChild(script);
});
</script>`,
    shopify: `<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "${sdkKey}" });
</script>`,
    wordpress: `// Option A: Use WPCode plugin
// Go to Code Snippets → Add New → paste HTML snippet → "Site Wide Footer"

// Option B: Add to functions.php
function emoratest_tracking() { ?>
  <script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
  <script>EmoraTest.init({ sdkKey: "${sdkKey}" });</script>
<?php }
add_action('wp_footer', 'emoratest_tracking');`,
    gtm: `<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "${sdkKey}" });
</script>`,
  };

  const platformInstructions: Record<Platform, { title: string; description: string; location?: string }> = {
    html: {
      title: "HTML (Any Website)",
      description: "Add this before the closing </body> tag in your HTML.",
    },
    react: {
      title: "React / Next.js",
      description: "Create a client component and add it to your root layout.",
    },
    vue: {
      title: "Vue.js",
      description: "Use the onMounted hook in your setup script.",
    },
    shopify: {
      title: "Shopify",
      description: "Go to Online Store → Themes → Edit code, open theme.liquid, and paste before the closing </body> tag.",
      location: "theme.liquid",
    },
    wordpress: {
      title: "WordPress",
      description: "Use the WPCode plugin or add to your theme's functions.php file.",
    },
    gtm: {
      title: "Google Tag Manager",
      description: "Go to Tags → New → Custom HTML, paste the snippet, set trigger to 'All Pages', then publish.",
    },
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] px-4 py-8">
      <div className="w-full max-w-2xl space-y-8">
        {/* Progress bar */}
        <div className="flex items-center gap-2">
          {STEPS.map((label, i) => (
            <div key={label} className="flex-1">
              <div className={`h-1.5 rounded-full transition-colors ${i <= step ? "bg-indigo-500" : "bg-[hsl(var(--border))]"}`} />
              <p className={`mt-1 text-center text-[10px] font-medium ${i <= step ? "text-indigo-500" : "text-[hsl(var(--muted-foreground))]"}`}>
                {label}
              </p>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-sm">
          {/* Step 0: Welcome */}
          {step === 0 && (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600">
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-[hsl(var(--foreground))]">Welcome to EmoraTest!</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Let&apos;s get your store set up with AI-powered behavioral intelligence.
                This will only take a minute.
              </p>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Site: <span className="font-semibold text-[hsl(var(--foreground))]">{user.shop_domain || "your website"}</span>
              </p>
            </div>
          )}

          {/* Step 1: SDK Key */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-[hsl(var(--foreground))]">Your SDK Key</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                This key authenticates your website with EmoraTest. Copy it — you&apos;ll need it in the next step.
              </p>
              <div className="rounded-xl bg-[hsl(var(--secondary))] p-4">
                <code className="block break-all font-mono text-xs text-[hsl(var(--foreground))]">
                  {sdkKey || "Key was shown at registration. Check Settings to manage your key."}
                </code>
              </div>
              <button
                onClick={() => { if (sdkKey) navigator.clipboard.writeText(sdkKey); }}
                className="rounded-xl border border-[hsl(var(--border))] px-4 py-2 text-sm font-medium text-[hsl(var(--foreground))] transition-colors hover:bg-[hsl(var(--accent))]"
              >
                Copy to clipboard
              </button>
            </div>
          )}

          {/* Step 2: Install SDK */}
          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-[hsl(var(--foreground))]">Install the SDK</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Choose your platform and follow the instructions below.
              </p>

              {/* Platform selector */}
              <div className="flex flex-wrap gap-2">
                {[
                  { key: "html" as Platform, label: "HTML" },
                  { key: "react" as Platform, label: "React" },
                  { key: "vue" as Platform, label: "Vue.js" },
                  { key: "shopify" as Platform, label: "Shopify" },
                  { key: "wordpress" as Platform, label: "WordPress" },
                  { key: "gtm" as Platform, label: "GTM" },
                ].map((p) => (
                  <button
                    key={p.key}
                    onClick={() => setPlatform(p.key)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      platform === p.key
                        ? "bg-indigo-500 text-white"
                        : "bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]"
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              <div className="rounded-xl bg-gray-900 p-4 relative">
                <button
                  onClick={() => navigator.clipboard.writeText(codeSnippets[platform])}
                  className="absolute top-2 right-2 text-gray-400 hover:text-white text-xs flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-800 transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy
                </button>
                <pre className="overflow-x-auto text-xs text-green-400 whitespace-pre-wrap">
                  {codeSnippets[platform]}
                </pre>
              </div>

              <div className="rounded-xl bg-blue-50 border border-blue-100 p-3">
                <p className="text-xs text-blue-700">
                  <strong>Instructions:</strong> {platformInstructions[platform].description}
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Verify */}
          {step === 3 && (
            <div className="space-y-4 text-center">
              <h2 className="text-xl font-bold text-[hsl(var(--foreground))]">Verify Installation</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Visit your website in a new tab and click around for 30 seconds. Then click the button below to verify data is flowing.
              </p>

              {verified ? (
                <div className="rounded-xl bg-green-50 border border-green-100 p-6">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 mb-3">
                    <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  </div>
                  <p className="text-sm font-medium text-green-700">Installation verified!</p>
                  <p className="text-xs text-green-600 mt-1">Redirecting to dashboard...</p>
                </div>
              ) : (
                <>
                  <button
                    onClick={handleVerify}
                    disabled={verifying}
                    className="rounded-xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow-md transition-all hover:shadow-lg disabled:opacity-50"
                  >
                    {verifying ? "Checking..." : "Verify Installation"}
                  </button>
                  <button
                    onClick={() => setStep(4)}
                    className="block w-full text-sm text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] underline"
                  >
                    Skip verification
                  </button>
                </>
              )}
            </div>
          )}

          {/* Step 4: Done */}
          {step === 4 && (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                <svg className="h-8 w-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-[hsl(var(--foreground))]">You&apos;re all set!</h2>

              <div className="rounded-xl bg-gray-50 p-4 text-left">
                <p className="text-sm font-medium text-gray-900 mb-3">What happens next:</p>
                <ul className="text-sm text-gray-600 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>Within 60 seconds of installing, you&apos;ll start seeing sessions in your dashboard</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>Each session gets a behavioral prediction after it ends (minimum 10 seconds)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>Check Page Insights to see which pages cause the most friction</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>Check Diagnosis for automatic UX issue detection and recommendations</span>
                  </li>
                </ul>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="mt-8 flex justify-between">
            {step > 0 ? (
              <button
                onClick={() => setStep(step - 1)}
                className="rounded-xl border border-[hsl(var(--border))] px-5 py-2.5 text-sm font-medium text-[hsl(var(--foreground))] transition-colors hover:bg-[hsl(var(--accent))]"
              >
                Back
              </button>
            ) : (
              <div />
            )}

            {step < STEPS.length - 1 ? (
              <button
                onClick={() => setStep(step + 1)}
                className="rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md transition-all hover:shadow-lg"
              >
                Continue
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={completing}
                className="rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md transition-all hover:shadow-lg disabled:opacity-50"
              >
                {completing ? "Loading..." : "Go to Dashboard"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
