"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

interface Section {
  id: string;
  title: string;
}

const sections: Section[] = [
  { id: "getting-started", title: "Getting Started" },
  { id: "installation", title: "Installation" },
  { id: "auto-tracking", title: "What Gets Tracked Automatically" },
  { id: "gdpr-consent", title: "GDPR Compliance (EU Only)" },
  { id: "conversions", title: "Tracking Conversions" },
  { id: "ab-testing", title: "Running A/B Tests" },
  { id: "sdk-reference", title: "SDK Reference" },
  { id: "troubleshooting", title: "Troubleshooting" },
];

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState("");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [sdkKey, setSdkKey] = useState<string | null>(null);
  const [copiedSdkKey, setCopiedSdkKey] = useState(false);
  const [sdkKeyLoading, setSdkKeyLoading] = useState(true);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 100;

      for (const section of sections) {
        const element = document.getElementById(section.id);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener("scroll", handleScroll);
    handleScroll();

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Try to get SDK key from localStorage (set by Settings page after regeneration)
  useEffect(() => {
    const storedKey = localStorage.getItem("emoratest_sdk_key");
    if (storedKey) {
      setSdkKey(storedKey);
    }
    setSdkKeyLoading(false);
  }, []);

  const copySdkKey = () => {
    if (sdkKey) {
      navigator.clipboard.writeText(sdkKey).then(() => {
        setCopiedSdkKey(true);
        setTimeout(() => setCopiedSdkKey(false), 2000);
      });
    }
  };

  const copyToClipboard = (code: string, sectionId: string) => {
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(sectionId);
      setTimeout(() => setCopiedCode(null), 2000);
    });
  };

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar TOC */}
          <aside className="lg:w-64 flex-shrink-0">
            <div className="lg:fixed lg:w-64 bg-[hsl(var(--card))] rounded-2xl p-4 border border-[hsl(var(--border))]">
              <h2 className="text-lg font-semibold mb-4">On this page</h2>
              <nav className="space-y-1">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => scrollToSection(section.id)}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeSection === section.id
                        ? "bg-[hsl(var(--primary))] text-white"
                        : "text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]"
                    }`}
                  >
                    {section.title}
                  </button>
                ))}
              </nav>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            <div className="max-w-3xl">
              <header className="mb-12">
                <h1 className="text-4xl font-bold mb-4">
                  EmoraTest SDK Documentation
                </h1>
                <p className="text-xl text-[hsl(var(--muted-foreground))]">
                  Learn how to integrate emotion tracking and A/B testing into your website.
                </p>
              </header>

              {/* Quick Start Card - SDK Key */}
              <div className="bg-gradient-to-r from-[hsl(var(--primary))]/10 to-[hsl(var(--primary))]/5 rounded-xl p-6 border border-[hsl(var(--primary))]/20 mb-12">
                <h3 className="text-lg font-semibold mb-2">Quick Start: Your SDK Key</h3>
                <div className="flex items-center gap-3 flex-wrap">
                  <code className="flex-1 min-w-0 bg-[hsl(var(--card))] px-4 py-2 rounded-lg font-mono text-sm border border-[hsl(var(--border))]">
                    {sdkKeyLoading ? (
                      "Loading..."
                    ) : sdkKey ? (
                      sdkKey
                    ) : (
                      <span className="text-[hsl(var(--muted-foreground))]">
                        Go to <a href="/dashboard/settings" className="text-[hsl(var(--primary))] hover:underline">Settings → SDK</a> to view
                      </span>
                    )}
                  </code>
                  {sdkKey && (
                    <button
                      onClick={copySdkKey}
                      className="px-4 py-2 bg-[hsl(var(--primary))] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                    >
                      {copiedSdkKey ? "✓ Copied!" : "Copy"}
                    </button>
                  )}
                </div>
              </div>

              {/* Getting Started */}
              <section id="getting-started" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">Getting Started</h2>
                <p className="text-[hsl(var(--muted-foreground))] mb-4">
                  EmoraTest detects 4 behavioral states from user behavior patterns: frustrated, confused, engaged, and disengaged. Install the SDK to start tracking sessions and get emotion insights.
                </p>
                <div className="bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))]">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-[hsl(var(--foreground))]">What you&apos;ll need:</strong>
                  </p>
                  <ul className="list-disc list-inside text-[hsl(var(--muted-foreground))] mt-2 space-y-1">
                    <li>Your SDK key (found in <a href="/dashboard/settings" className="text-[hsl(var(--primary))] hover:underline">Settings → SDK</a>)</li>
                    <li>Your EmoraTest instance URL</li>
                  </ul>
                </div>
              </section>

              <hr className="border-[hsl(var(--border))] mb-16" />

              {/* Installation */}
              <section id="installation" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">Installation</h2>

                <p className="text-[hsl(var(--muted-foreground))] mb-6">
                  Add the EmoraTest SDK to your website to start tracking user emotions and behavior.
                </p>

                <div className="bg-[hsl(var(--card))] rounded-xl p-5 border border-[hsl(var(--border))] mb-8">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-3">Choose your integration mode:</h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-4">
                      <div className="text-green-600 font-semibold mb-2">🚀 Quick Start (Recommended)</div>
                      <p className="text-sm text-[hsl(var(--muted-foreground))]">
                        Tracking starts immediately. Best for non-EU websites or internal tools.
                      </p>
                    </div>
                    <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4">
                      <div className="text-blue-600 font-semibold mb-2">🇪🇺 GDPR Compliance Mode</div>
                      <p className="text-sm text-[hsl(var(--muted-foreground))]">
                        Waits for user consent. Required for EU websites. See below.
                      </p>
                    </div>
                  </div>
                </div>

                <h3 className="text-lg font-semibold mb-3 mt-6">Quick Start — HTML (Any website)</h3>
                <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                  Add this snippet to your website's <code className="bg-[hsl(var(--secondary))] px-1 rounded">&lt;head&gt;</code> or before <code className="bg-[hsl(var(--secondary))] px-1 rounded">&lt;/body&gt;</code>:
                </p>
                <CodeBlock
                  code={`<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "YOUR_SDK_KEY" });
</script>`}
                  onCopy={() => copyToClipboard(`<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "YOUR_SDK_KEY" });
</script>`, "install-html")}
                  copied={copiedCode === "install-html"}
                />

                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 mt-4">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-green-700 dark:text-green-400">✓ Done!</strong> The SDK will start tracking immediately.
                    Sessions appear in your dashboard within seconds. Events are sent every 2 seconds.
                  </p>
                </div>

                <h3 className="text-lg font-semibold mb-3 mt-6">React / Next.js</h3>
                <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                  Create a client component and add it to your root layout:
                </p>
                <CodeBlock
                  code={`"use client";
import { useEffect } from "react";

export default function EmoraTracker() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://emoratest.com/static/sdk/emoratest.umd.js";
    script.async = true;
    script.onload = () => {
      window.EmoraTest?.init({ sdkKey: "YOUR_SDK_KEY" });
    };
    document.body.appendChild(script);
    // No cleanup .  let SDK persist across route changes
  }, []);
  return null;
}`}
                  onCopy={() => copyToClipboard(`"use client";
import { useEffect } from "react";

export default function EmoraTracker() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://emoratest.com/static/sdk/emoratest.umd.js";
    script.async = true;
    script.onload = () => {
      window.EmoraTest?.init({ sdkKey: "YOUR_SDK_KEY" });
    };
    document.body.appendChild(script);
  }, []);
  return null;
}`, "install-react")}
                  copied={copiedCode === "install-react"}
                />
                <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">
                  Then add <code className="bg-[hsl(var(--secondary))] px-1 rounded">&lt;EmoraTracker /&gt;</code> to your root layout.
                </p>

                <h3 className="text-lg font-semibold mb-3 mt-6">NPM Package</h3>
                <div className="bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))]">
                  <p className="text-[hsl(var(--muted-foreground))]">
                    NPM package coming soon. Use the script tag method for now.
                  </p>
                </div>

                <div className="bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))] mt-4">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-[hsl(var(--foreground))]">Note:</strong> Replace <code className="bg-[hsl(var(--secondary))] px-1 rounded">emoratest.com</code> with your EmoraTest instance URL
                    and <code className="bg-[hsl(var(--secondary))] px-1 rounded">YOUR_SDK_KEY</code> with the key from <a href="/dashboard/settings" className="text-[hsl(var(--primary))] hover:underline">Settings → SDK</a>.
                  </p>
                </div>
              </section>

              <hr className="border-[hsl(var(--border))] mb-16" />

              {/* Auto Tracking */}
              <section id="auto-tracking" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">What Gets Tracked Automatically</h2>
                <p className="text-[hsl(var(--muted-foreground))] mb-6">
                  Once installed, the SDK automatically tracks these behaviors:
                </p>

                <div className="grid gap-3 sm:grid-cols-2">
                  <TrackingItem title="Mouse movements" description="Cursor position and velocity" />
                  <TrackingItem title="Clicks" description="Element target, coordinates, timestamp" />
                  <TrackingItem title="Scroll behavior" description="Depth, velocity, direction changes" />
                  <TrackingItem title="Rage clicks" description="3+ clicks within 500ms on same area" />
                  <TrackingItem title="Exit intent" description="Cursor moving to browser chrome" />
                  <TrackingItem title="Scroll retreats" description="Scrolling back up to re-read" />
                  <TrackingItem title="Dwell time" description="Time spent on each page section" />
                  <TrackingItem title="Page navigation" description="URL changes across the session" />
                </div>

                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mt-6">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-[hsl(var(--primary))]">Privacy-first:</strong> All tracking is cookieless and GDPR-friendly.
                    No personal data is collected. Only behavioral patterns.
                  </p>
                </div>
              </section>

              <hr className="border-[hsl(var(--border))] mb-16" />

              {/* GDPR Consent */}
              <section id="gdpr-consent" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">GDPR Compliance Mode (EU Websites)</h2>
                <p className="text-[hsl(var(--muted-foreground))] mb-6">
                  If your website serves users in the European Union, you must obtain user consent before tracking.
                  Use the <code className="bg-[hsl(var(--secondary))] px-1 rounded">requireConsent: true</code> option.
                </p>

                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mb-6">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-[hsl(var(--primary))]">🇪🇺 EU Website?</strong> Follow the steps below. <strong className="text-[hsl(var(--primary))]">Not in EU?</strong> Use the Quick Start above — no consent needed.
                  </p>
                </div>

                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Step 1: Initialize with requireConsent</h3>
                    <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                      Pass <code className="bg-[hsl(var(--secondary))] px-1 rounded">requireConsent: true</code>. The SDK will load but wait for consent:
                    </p>
                    <CodeBlock
                      code={`<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({
    sdkKey: "YOUR_SDK_KEY",
    requireConsent: true  // SDK waits for user consent
  });
</script>`}
                      onCopy={() => copyToClipboard(`<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({
    sdkKey: "YOUR_SDK_KEY",
    requireConsent: true
  });
</script>`, "gdpr-step1")}
                      copied={copiedCode === "gdpr-step1"}
                    />
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 mt-3">
                      <p className="text-sm text-[hsl(var(--muted-foreground))]">
                        <strong>⚠️ Important:</strong> With <code className="bg-[hsl(var(--secondary))] px-1 rounded">requireConsent: true</code>, tracking will NOT start until the user accepts and you call <code className="bg-[hsl(var(--secondary))] px-1 rounded">enableTracking()</code>.
                      </p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-3">Step 2: Create a consent banner</h3>
                    <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                      Add a consent banner to your website. When user accepts:
                    </p>
                    <CodeBlock
                      code={`<!-- Simple HTML consent banner example -->
<div id="consent-banner" style="position:fixed;bottom:0;left:0;right:0;padding:20px;background:white;border-top:1px solid #ccc;display:flex;justify-content:space-between;align-items:center;z-index:9999;">
  <p>We use behavioral tracking to improve your experience. <a href="/privacy">Privacy Policy</a></p>
  <div>
    <button onclick="rejectConsent()">Reject</button>
    <button onclick="acceptConsent()" style="background:#007BFF;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Accept</button>
  </div>
</div>

<script>
function acceptConsent() {
  // 1. Hide banner
  document.getElementById('consent-banner').style.display = 'none';

  // 2. Set consent cookie (required by SDK)
  document.cookie = 'emoratest_consent=accepted; max-age=31536000; path=/';

  // 3. Start tracking
  if (window.EmoraTest) {
    window.EmoraTest.enableTracking();
  }
}

function rejectConsent() {
  document.getElementById('consent-banner').style.display = 'none';
  document.cookie = 'emoratest_consent=rejected; max-age=31536000; path=/';
}

// Check if user already decided
if (document.cookie.includes('emoratest_consent=')) {
  document.getElementById('consent-banner').style.display = 'none';
}
</script>`}
                      onCopy={() => copyToClipboard(`<div id="consent-banner" style="position:fixed;bottom:0;left:0;right:0;padding:20px;background:white;border-top:1px solid #ccc;display:flex;justify-content:space-between;align-items:center;z-index:9999;">
  <p>We use behavioral tracking to improve your experience.</p>
  <div>
    <button onclick="rejectConsent()">Reject</button>
    <button onclick="acceptConsent()" style="background:#007BFF;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Accept</button>
  </div>
</div>
<script>
function acceptConsent() {
  document.getElementById('consent-banner').style.display = 'none';
  document.cookie = 'emoratest_consent=accepted; max-age=31536000; path=/';
  if (window.EmoraTest) {
    window.EmoraTest.enableTracking();
  }
}
function rejectConsent() {
  document.getElementById('consent-banner').style.display = 'none';
  document.cookie = 'emoratest_consent=rejected; max-age=31536000; path=/';
}
if (document.cookie.includes('emoratest_consent=')) {
  document.getElementById('consent-banner').style.display = 'none';
}
</script>`, "gdpr-step2")}
                      copied={copiedCode === "gdpr-step2"}
                    />
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-3">Integrating with Consent Management Platforms</h3>
                    <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                      If you use a consent management platform (Cookiebot, OneTrust, Usercentrics, etc.),
                      you can hook into their callbacks:
                    </p>
                    <CodeBlock
                      code={`// Example with Cookiebot
window.addEventListener('CookiebotOnConsentReady', function() {
  if (Cookiebot.consent.statistics) {
    document.cookie = 'emoratest_consent=accepted; max-age=31536000; path=/';
    if (window.EmoraTest) {
      window.EmoraTest.enableTracking();
    }
  }
});

// Example with OneTrust
OneTrust.OnConsentChanged(function() {
  const activeGroups = OneTrust.GetDomainData().Groups;
  if (activeGroups.some(g => g.CustomGroupId === 'C0002')) {  // Performance cookies
    document.cookie = 'emoratest_consent=accepted; max-age=31536000; path=/';
    if (window.EmoraTest) {
      window.EmoraTest.enableTracking();
    }
  }
});`}
                      onCopy={() => copyToClipboard(`window.addEventListener('CookiebotOnConsentReady', function() {
  if (Cookiebot.consent.statistics) {
    document.cookie = 'emoratest_consent=accepted; max-age=31536000; path=/';
    if (window.EmoraTest) {
      window.EmoraTest.enableTracking();
    }
  }
});`, "gdpr-cmp")}
                      copied={copiedCode === "gdpr-cmp"}
                    />
                  </div>

                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
                    <h4 className="text-sm font-semibold text-amber-700 dark:text-amber-400 mb-2">What data we collect</h4>
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">
                      <strong>Collected:</strong> Mouse movements, clicks, scroll patterns, and page URLs.
                    </p>
                    <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
                      <strong>NOT collected:</strong> Names, emails, IP addresses (hashed immediately),
                      keystrokes, form inputs, screenshots, or passwords.
                    </p>
                  </div>
                </div>
              </section>

              <hr className="border-[hsl(var(--border))] mb-16" />

              {/* Conversions */}
              <section id="conversions" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">Tracking Conversions</h2>
                <p className="text-[hsl(var(--muted-foreground))] mb-4">
                  Report conversion outcomes to understand which emotions lead to purchases.
                </p>

                <CodeBlock
                  code={`// After a purchase
window.EmoraTest.reportOutcome('purchase');

// After signup
window.EmoraTest.reportOutcome('signup');

// After booking a demo
window.EmoraTest.reportOutcome('demo_booked');

// After lead generation
window.EmoraTest.reportOutcome('lead_generated');

// After trial start
window.EmoraTest.reportOutcome('trial_started');`}
                  onCopy={() => copyToClipboard(`window.EmoraTest.reportOutcome('purchase');
window.EmoraTest.reportOutcome('signup');
window.EmoraTest.reportOutcome('demo_booked');
window.EmoraTest.reportOutcome('lead_generated');
window.EmoraTest.reportOutcome('trial_started');`, "conversions")}
                  copied={copiedCode === "conversions"}
                />

                <div className="bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))] mt-4">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-[hsl(var(--foreground))]">Available outcomes:</strong> purchase, signup, checkout_completed,
                    demo_booked, lead_generated, trial_started.
                  </p>
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">
                    <strong className="text-[hsl(var(--primary))]">Auto-detection:</strong> EmoraTest auto-detects outcomes from common
                    URL patterns like /success, /thank-you, /confirmation.
                  </p>
                </div>
              </section>

              <hr className="border-[hsl(var(--border))] mb-16" />

              {/* A/B Testing */}
              <section id="ab-testing" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">Running A/B Tests</h2>

                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[13px] text-amber-800 mb-6">
                  <strong>Early Beta:</strong> The experiment management UI is available, but automatic SDK-side variant assignment is under development. Currently, you can create experiment definitions and track emotion differences between page variants you set up manually. Full A/B testing with automatic variant assignment is coming soon.
                </div>

                <div className="space-y-6">
                  <StepCard
                    step={1}
                    title="Create an experiment"
                    description="Go to Experiments → New in the dashboard. Give your experiment a name and flag key."
                  />

                  <StepCard
                    step={2}
                    title="Add flag evaluation code"
                    description="Evaluate the flag and show different content based on variant:"
                  >
                    <CodeBlock
                      code={`const result = await EmoraTest.evaluateFlag('your-flag-key');

if (result.variant === 'control') {
  // Show original version
} else if (result.variant === 'variant_b') {
  // Show new version
}`}
                      onCopy={() => copyToClipboard(`const result = await EmoraTest.evaluateFlag('your-flag-key');

if (result.variant === 'control') {
  // Show original version
} else if (result.variant === 'variant_b') {
  // Show new version
}`, "abtest-step2")}
                      copied={copiedCode === "abtest-step2"}
                    />
                  </StepCard>

                  <StepCard
                    step={3}
                    title="Report conversions"
                    description="Call reportOutcome() when users convert to measure which variant performs better."
                  />

                  <StepCard
                    step={4}
                    title="Check results"
                    description="View results in the Experiments dashboard to see which variant wins."
                  />
                </div>

                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mt-6">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-[hsl(var(--primary))]">Deterministic:</strong> Each visitor always sees the same variant (deterministic hashing).
                    Open an incognito window to test the other variant.
                  </p>
                </div>
              </section>

              <hr className="border-[hsl(var(--border))] mb-16" />

              {/* SDK Reference */}
              <section id="sdk-reference" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">SDK Reference</h2>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <th className="text-left py-3 px-4 font-semibold">Method</th>
                        <th className="text-left py-3 px-4 font-semibold">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.init(&#123; sdkKey, requireConsent &#125;)</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Initialize tracking. Set requireConsent: true for GDPR compliance.</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.enableTracking()</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Start tracking after consent (only when requireConsent: true).</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.reportOutcome(type)</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Report conversion outcome.</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.evaluateFlag(key)</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Get A/B test variant. Returns &#123; variant, enabled &#125;.</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.getVariant(key)</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Shorthand .  returns variant string or null.</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.getSessionId()</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Current session ID.</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.getVisitorId()</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Persistent visitor ID (survives page reload).</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.isInitialized()</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Check if SDK is active.</td>
                      </tr>
                      <tr className="border-b border-[hsl(var(--border))]">
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.destroy()</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Clean up and end session.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-[hsl(var(--border))] mb-16" />

              {/* Troubleshooting */}
              <section id="troubleshooting" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold mb-4">Troubleshooting</h2>

                <div className="bg-[hsl(var(--card))] rounded-xl p-5 border border-[hsl(var(--border))] mb-8">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-3">🔍 Quick Debug Checklist</h3>
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                    Open your browser's Developer Console (F12) and run these commands:
                  </p>
                  <ol className="text-sm text-[hsl(var(--muted-foreground))] space-y-2 list-decimal list-inside">
                    <li><code className="bg-[hsl(var(--secondary))] px-1 rounded">typeof window.EmoraTest</code> → Should be <code className="bg-green-500/20 text-green-700 px-1 rounded">'object'</code></li>
                    <li><code className="bg-[hsl(var(--secondary))] px-1 rounded">window.EmoraTest.isInitialized()</code> → Should be <code className="bg-green-500/20 text-green-700 px-1 rounded">true</code></li>
                    <li><code className="bg-[hsl(var(--secondary))] px-1 rounded">window.EmoraTest.getSessionId()</code> → Should return a session ID string</li>
                    <li><code className="bg-[hsl(var(--secondary))] px-1 rounded">document.cookie</code> → Check for <code className="bg-[hsl(var(--secondary))] px-1 rounded">emoratest_consent=accepted</code></li>
                  </ol>
                  <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">
                      <strong>Tip:</strong> Open the Network tab in DevTools, filter by "events" or "sessions" to see API calls being made. Events are sent every 2 seconds.
                    </p>
                  </div>
                </div>

                <h3 className="text-lg font-semibold mb-4">Common Issues</h3>
                <div className="space-y-4">
                  <TroubleshootItem
                    problem="Sessions not appearing in dashboard?"
                    solution={
                      <span>
                        1) Check <code className="bg-[hsl(var(--secondary))] px-1 rounded">window.EmoraTest.isInitialized()</code> returns true.<br/>
                        2) Open Network tab → look for requests to <code className="bg-[hsl(var(--secondary))] px-1 rounded">/api/v1/sdk/sessions</code> and <code className="bg-[hsl(var(--secondary))] px-1 rounded">/api/v1/sdk/events</code>.<br/>
                        3) If using <code className="bg-[hsl(var(--secondary))] px-1 rounded">requireConsent: true</code>, make sure user accepted consent and cookie is set.
                      </span>
                    }
                  />
                  <TroubleshootItem
                    problem="'EmoraTest is not defined' error?"
                    solution="SDK script hasn't loaded yet. Make sure the script src URL is correct and you're calling init() after the page loads."
                  />
                  <TroubleshootItem
                    problem="401 Unauthorized errors?"
                    solution="Invalid SDK key. Copy it again from Settings → SDK. Make sure there are no extra spaces at the start/end."
                  />
                  <TroubleshootItem
                    problem="Events only appear after I close the tab?"
                    solution="Normal behavior! Events batch every 2 seconds. Session data (including emotion prediction) is finalized when the session ends (tab close or navigation away)."
                  />
                  <TroubleshootItem
                    problem="Very few events being captured?"
                    solution="Default mouse throttle is 100ms. If you need higher resolution, pass mouseMoveThrottleMs: 50 to init()."
                  />
                  <TroubleshootItem
                    problem="enableTracking() not working?"
                    solution="Make sure: 1) init() was called with requireConsent: true, 2) emoratest_consent cookie is set to 'accepted', 3) init() completed before calling enableTracking()."
                  />
                  <TroubleshootItem
                    problem="A/B test always shows same variant?"
                    solution="Correct behavior! Each visitor always sees the same variant (deterministic hashing). Use incognito mode to test other variants."
                  />
                </div>
              </section>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

// ── Subcomponents ─────────────────────────────────────────────────────────────

function CodeBlock({
  code,
  onCopy,
  copied,
}: {
  code: string;
  onCopy: () => void;
  copied: boolean;
}) {
  return (
    <div className="relative group">
      <button
        onClick={onCopy}
        className="absolute top-2 right-2 px-3 py-1 text-xs font-medium rounded-lg bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--accent))] transition-colors opacity-0 group-hover:opacity-100"
      >
        {copied ? "Copied!" : "Copy"}
      </button>
      <pre className="bg-[hsl(var(--card))] text-[hsl(var(--foreground))] rounded-xl p-4 overflow-x-auto text-sm border border-[hsl(var(--border))]">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function TrackingItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex items-center gap-3 bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))]">
      <span className="text-[hsl(var(--primary))] text-lg">✓</span>
      <div>
        <span className="text-[hsl(var(--foreground))] font-medium">{title}</span>
        <span className="text-[hsl(var(--muted-foreground))] text-sm ml-2">.  {description}</span>
      </div>
    </div>
  );
}

function StepCard({
  step,
  title,
  description,
  children,
}: {
  step: number;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="bg-[hsl(var(--card))] rounded-xl p-5 border border-[hsl(var(--border))]">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-[hsl(var(--primary))] to-[hsl(var(--primary))] flex items-center justify-center text-white font-bold">
          {step}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold mb-2">{title}</h3>
          <p className="text-[hsl(var(--muted-foreground))] mb-3">{description}</p>
          {children}
        </div>
      </div>
    </div>
  );
}

function TroubleshootItem({
  problem,
  solution,
}: {
  problem: string;
  solution: string | React.ReactNode;
}) {
  return (
    <div className="bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))]">
      <h4 className="font-semibold text-[hsl(var(--primary))] mb-2">Q: {problem}</h4>
      <div className="text-[hsl(var(--muted-foreground))] text-sm">→ {solution}</div>
    </div>
  );
}
