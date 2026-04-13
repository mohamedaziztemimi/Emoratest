"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authCompleteOnboarding } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const STEPS = ["Welcome", "Your SDK Key", "Install SDK", "Done"];

export default function OnboardingPage() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [completing, setCompleting] = useState(false);

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

  if (loading || !user) return null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] px-4">
      <div className="w-full max-w-lg space-y-8">
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
                Shop: <span className="font-semibold text-[hsl(var(--foreground))]">{user.shop_domain}</span>
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
                Add this script tag to your website&apos;s {"<head>"} section:
              </p>
              <div className="rounded-xl bg-gray-900 p-4">
                <pre className="overflow-x-auto text-xs text-green-400">
{`<script src="https://cdn.emoratest.com/sdk.js"></script>
<script>
  EmoraTest.init({
    sdkKey: "${sdkKey ? sdkKey.slice(0, 12) + "..." : "YOUR_SDK_KEY"}",
    trackClicks: true,
    trackScroll: true,
    trackMouse: true,
  });
</script>`}
                </pre>
              </div>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                Or install via npm: <code className="rounded bg-[hsl(var(--secondary))] px-1.5 py-0.5 font-mono">npm install @emoratest/sdk</code>
              </p>
            </div>
          )}

          {/* Step 3: Done */}
          {step === 3 && (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                <svg className="h-8 w-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-[hsl(var(--foreground))]">You&apos;re all set!</h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Your dashboard is ready. As visitors browse your store, you&apos;ll see real-time behavioral intelligence, friction detection, and intervention recommendations.
              </p>
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
