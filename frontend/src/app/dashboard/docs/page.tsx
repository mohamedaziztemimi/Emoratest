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
                  EmoraTest detects 8 emotions from user behavior — frustration, confusion, delight,
                  anxiety, hesitation, focus, boredom, and satisfaction. Install the SDK to start
                  tracking sessions and get emotion insights.
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

                <h3 className="text-lg font-semibold mb-3 mt-6">HTML (Any website)</h3>
                <CodeBlock
                  code={`<script src="https://YOUR_DOMAIN/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "YOUR_SDK_KEY" });
</script>`}
                  onCopy={() => copyToClipboard(`<script src="https://YOUR_DOMAIN/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({ sdkKey: "YOUR_SDK_KEY" });
</script>`, "install-html")}
                  copied={copiedCode === "install-html"}
                />

                <h3 className="text-lg font-semibold mb-3 mt-6">React / Next.js</h3>
                <CodeBlock
                  code={`"use client";
import { useEffect } from "react";

export default function EmoraTracker() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://YOUR_DOMAIN/static/sdk/emoratest.umd.js";
    script.async = true;
    script.onload = () => {
      window.EmoraTest?.init({ sdkKey: "YOUR_SDK_KEY" });
    };
    document.body.appendChild(script);
    return () => { document.body.removeChild(script); };
  }, []);
  return null;
}`}
                  onCopy={() => copyToClipboard(`"use client";
import { useEffect } from "react";

export default function EmoraTracker() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://YOUR_DOMAIN/static/sdk/emoratest.umd.js";
    script.async = true;
    script.onload = () => {
      window.EmoraTest?.init({ sdkKey: "YOUR_SDK_KEY" });
    };
    document.body.appendChild(script);
    return () => { document.body.removeChild(script); };
  }, []);
  return null;
}`, "install-react")}
                  copied={copiedCode === "install-react"}
                />
                <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">
                  Then add <code className="bg-[hsl(var(--secondary))] px-1 rounded">&lt;EmoraTracker /&gt;</code> to your root layout.
                </p>

                <h3 className="text-lg font-semibold mb-3 mt-6">NPM Package (coming soon)</h3>
                <CodeBlock
                  code={`npm install emoratest
# Coming soon — use the script tag method for now`}
                  onCopy={() => copyToClipboard(`npm install emoratest`, "install-npm")}
                  copied={copiedCode === "install-npm"}
                />

                <div className="bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))] mt-4">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    <strong className="text-[hsl(var(--foreground))]">Note:</strong> Replace <code className="bg-[hsl(var(--secondary))] px-1 rounded">YOUR_DOMAIN</code> with your EmoraTest instance URL
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
                    No personal data is collected — only behavioral patterns.
                  </p>
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
                        <td className="py-3 px-4"><code className="text-[hsl(var(--primary))]">EmoraTest.init(&#123; sdkKey &#125;)</code></td>
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Initialize tracking. Call once.</td>
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
                        <td className="py-3 px-4 text-[hsl(var(--muted-foreground))]">Shorthand — returns variant string or null.</td>
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

                <div className="space-y-4">
                  <TroubleshootItem
                    problem="SDK not loading?"
                    solution="Check script URL, check browser console for errors."
                  />
                  <TroubleshootItem
                    problem="401 errors?"
                    solution="Invalid SDK key. Copy it again from Settings."
                  />
                  <TroubleshootItem
                    problem="Sessions not appearing?"
                    solution="Verify SDK loads: type window.EmoraTest in console."
                  />
                  <TroubleshootItem
                    problem="Emotion shows 'Analyzing...'?"
                    solution="Emotions are predicted after the session ends. Wait for the user to leave."
                  />
                  <TroubleshootItem
                    problem="A/B test shows same variant?"
                    solution="Correct behavior. Use incognito for other variant."
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
        <span className="text-[hsl(var(--muted-foreground))] text-sm ml-2">— {description}</span>
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
  solution: string;
}) {
  return (
    <div className="bg-[hsl(var(--card))] rounded-xl p-4 border border-[hsl(var(--border))]">
      <h4 className="font-semibold text-[hsl(var(--primary))] mb-2">Q: {problem}</h4>
      <p className="text-[hsl(var(--muted-foreground))] text-sm">→ {solution}</p>
    </div>
  );
}
