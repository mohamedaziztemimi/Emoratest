"use client";

import { useEffect, useState } from "react";

interface Section {
  id: string;
  title: string;
}

const sections: Section[] = [
  { id: "getting-started", title: "Getting Started" },
  { id: "installation", title: "Installation" },
  { id: "what-gets-tracked", title: "What Gets Tracked Automatically" },
  { id: "tracking-conversions", title: "Tracking Conversions" },
  { id: "running-ab-tests", title: "Running A/B Tests" },
  { id: "ab-test-examples", title: "A/B Test Examples" },
  { id: "understanding-dashboard", title: "Understanding Your Dashboard" },
  { id: "sdk-reference", title: "SDK Reference" },
  { id: "troubleshooting", title: "Troubleshooting" },
];

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState("");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

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
    <div className="min-h-screen bg-[#0f0f1a] text-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar TOC */}
          <aside className="lg:w-64 flex-shrink-0">
            <div className="lg:fixed lg:w-64 bg-[#1a1a2e] rounded-2xl p-4 border border-gray-800">
              <h2 className="text-lg font-semibold text-white mb-4">On this page</h2>
              <nav className="space-y-1">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => scrollToSection(section.id)}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeSection === section.id
                        ? "bg-[#7C3AED] text-white"
                        : "text-gray-400 hover:text-white hover:bg-gray-800"
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
                <h1 className="text-4xl font-bold text-white mb-4">
                  EmoraTest SDK Documentation
                </h1>
                <p className="text-xl text-gray-400">
                  Learn how to integrate emotion tracking and A/B testing into your website.
                </p>
              </header>

              {/* Getting Started */}
              <section id="getting-started" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">Getting Started</h2>
                <p className="text-gray-300 mb-4">
                  EmoraTest detects user emotions from behavior patterns and helps you optimize
                  conversions. Add one script to your site to start tracking sessions, emotions, and
                  run A/B tests.
                </p>
                <div className="bg-[#1a1a2e] rounded-xl p-4 border border-gray-800">
                  <p className="text-sm text-gray-300">
                    <strong className="text-white">What you&apos;ll need:</strong>
                  </p>
                  <ul className="list-disc list-inside text-gray-400 mt-2 space-y-1">
                    <li>Your SDK key (found in the Settings page)</li>
                    <li>Your EmoraTest server URL</li>
                  </ul>
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* Installation */}
              <section id="installation" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">Installation</h2>
                <p className="text-gray-300 mb-4">
                  Add the following script tag before the <code className="bg-[#f1f5f9] px-1 rounded text-[#1e293b]">{"</body>"}</code> tag
                  on every page you want to track:
                </p>

                <CodeBlock
                  code={`<script src="https://YOUR_SERVER/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({
    sdkKey: "YOUR_SDK_KEY",
    apiUrl: "https://YOUR_SERVER"
  });
</script>`}
                  onCopy={() => copyToClipboard(`<script src="https://YOUR_SERVER/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({
    sdkKey: "YOUR_SDK_KEY",
    apiUrl: "https://YOUR_SERVER"
  });
</script>`, "installation")}
                  copied={copiedCode === "installation"}
                />

                <div className="bg-[#1a1a2e] rounded-xl p-4 border border-gray-800 mt-4">
                  <p className="text-sm text-gray-300">
                    <strong className="text-white">Note:</strong> Replace <code className="bg-[#f1f5f9] px-1 rounded text-[#1e293b]">YOUR_SDK_KEY</code> with
                    the key from your Settings page. Replace <code className="bg-[#f1f5f9] px-1 rounded text-[#1e293b]">YOUR_SERVER</code> with
                    your EmoraTest server URL. Add this to every page you want to track — the SDK
                    automatically handles session persistence across pages.
                  </p>
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* What Gets Tracked Automatically */}
              <section id="what-gets-tracked" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">What Gets Tracked Automatically</h2>
                <p className="text-gray-300 mb-4">
                  Once installed, the SDK automatically tracks:
                </p>

                <div className="grid gap-4 sm:grid-cols-2">
                  <TrackingItem icon="🖱️" title="Mouse movements, clicks, and scroll behavior" />
                  <TrackingItem icon="😤" title="Rage clicks (frustrated rapid clicking)" />
                  <TrackingItem icon="🚪" title="Exit intent (cursor moving to close/back button)" />
                  <TrackingItem icon="↕️" title="Scroll retreats (scrolling back and forth)" />
                  <TrackingItem icon="⏱️" title="Session duration and page URLs" />
                </div>

                <div className="bg-[#7C3AED]/10 border border-[#7C3AED]/30 rounded-xl p-4 mt-6">
                  <p className="text-sm text-gray-300">
                    <strong className="text-[#7C3AED]">No extra code needed</strong> — just install and the dashboard
                    will start showing session data, emotion predictions, and behavior signals.
                  </p>
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* Tracking Conversions */}
              <section id="tracking-conversions" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">Tracking Conversions</h2>
                <p className="text-gray-300 mb-4">
                  To measure what matters, tell EmoraTest when a user converts (makes a purchase,
                  signs up, completes a goal).
                </p>

                <CodeBlock
                  code={`// Call this when a user completes your goal action
// For example, after a purchase:
document.getElementById('buy-button').addEventListener('click', function() {
  EmoraTest.reportOutcome('purchase');
});

// For a signup:
document.getElementById('signup-form').addEventListener('submit', function() {
  EmoraTest.reportOutcome('purchase');
});`}
                  onCopy={() => copyToClipboard(`document.getElementById('buy-button').addEventListener('click', function() {
  EmoraTest.reportOutcome('purchase');
});`, "conversions")}
                  copied={copiedCode === "conversions"}
                />

                <div className="bg-[#1a1a2e] rounded-xl p-4 border border-gray-800 mt-4">
                  <p className="text-sm text-gray-300">
                    Use <code className="bg-[#f1f5f9] px-1 rounded text-[#1e293b]">reportOutcome(&apos;purchase&apos;)</code> for
                    e-commerce conversions. The outcome is recorded and linked to the session&apos;s
                    emotion data for analysis.
                  </p>
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* Running A/B Tests */}
              <section id="running-ab-tests" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">Running A/B Tests</h2>

                <div className="space-y-6">
                  <StepCard
                    step={1}
                    title="Create a Feature Flag"
                    description="Go to Feature Flags in the dashboard. Click New Flag. Give it a key (e.g., hero-headline), name, and add 2 variants: control (50%) and variant_b (50%). Activate it."
                  />

                  <StepCard
                    step={2}
                    title="Use the flag in your code"
                    description="On the page you want to test, evaluate the flag and show different content:"
                  >
                    <CodeBlock
                      code={`// Wait for the SDK to evaluate the flag
async function setupABTest() {
  const result = await EmoraTest.evaluateFlag('hero-headline');

  if (result.variant === 'control') {
    // Original version
    document.getElementById('headline').textContent = 'Welcome to Our Store';
  } else if (result.variant === 'variant_b') {
    // New version to test
    document.getElementById('headline').textContent = 'Shop the Best Deals Today';
  }
}

setupABTest();`}
                      onCopy={() => copyToClipboard(`async function setupABTest() {
  const result = await EmoraTest.evaluateFlag('hero-headline');

  if (result.variant === 'control') {
    document.getElementById('headline').textContent = 'Welcome to Our Store';
  } else if (result.variant === 'variant_b') {
    document.getElementById('headline').textContent = 'Shop the Best Deals Today';
  }
}

setupABTest();`, "abtest-step2")}
                      copied={copiedCode === "abtest-step2"}
                    />
                  </StepCard>

                  <StepCard
                    step={3}
                    title="Track conversions"
                    description="Make sure you have EmoraTest.reportOutcome('purchase') on your conversion page (see Tracking Conversions section)."
                  />

                  <StepCard
                    step={4}
                    title="Check results"
                    description="Go to Feature Flags in the dashboard, click View Results on your flag. You'll see how many visitors saw each variant and which one converts better."
                  />
                </div>

                <div className="bg-[#007BFF]/10 border border-[#007BFF]/30 rounded-xl p-4 mt-6">
                  <p className="text-sm text-gray-300">
                    <strong className="text-[#007BFF]">Each visitor automatically gets assigned one variant</strong> and
                    always sees the same one. The SDK handles this — you don't need to manage user assignments.
                  </p>
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* A/B Test Examples */}
              <section id="ab-test-examples" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">A/B Test Examples</h2>

                <div className="space-y-6">
                  <ExampleCard
                    title="Test button color"
                    description="Change the CTA button's appearance based on variant."
                  >
                    <CodeBlock
                      code={`const result = await EmoraTest.evaluateFlag('cta-button-color');
const button = document.getElementById('cta-button');

if (result.variant === 'variant_b') {
  button.style.backgroundColor = '#FF6B00';
  button.textContent = 'Buy Now — Free Shipping';
}`}
                      onCopy={() => copyToClipboard(`const result = await EmoraTest.evaluateFlag('cta-button-color');
const button = document.getElementById('cta-button');

if (result.variant === 'variant_b') {
  button.style.backgroundColor = '#FF6B00';
  button.textContent = 'Buy Now — Free Shipping';
}`, "example-button")}
                      copied={copiedCode === "example-button"}
                    />
                  </ExampleCard>

                  <ExampleCard
                    title="Test entire page sections"
                    description="Show different layouts or components based on variant."
                  >
                    <CodeBlock
                      code={`const result = await EmoraTest.evaluateFlag('pricing-layout');

if (result.variant === 'control') {
  document.getElementById('pricing-v1').style.display = 'block';
  document.getElementById('pricing-v2').style.display = 'none';
} else {
  document.getElementById('pricing-v1').style.display = 'none';
  document.getElementById('pricing-v2').style.display = 'block';
}`}
                      onCopy={() => copyToClipboard(`const result = await EmoraTest.evaluateFlag('pricing-layout');

if (result.variant === 'control') {
  document.getElementById('pricing-v1').style.display = 'block';
  document.getElementById('pricing-v2').style.display = 'none';
} else {
  document.getElementById('pricing-v1').style.display = 'none';
  document.getElementById('pricing-v2').style.display = 'block';
}`, "example-layout")}
                      copied={copiedCode === "example-layout"}
                    />
                  </ExampleCard>

                  <ExampleCard
                    title="Test with more than 2 variants"
                    description="Create a flag with 3 variants (control 34%, variant_b 33%, variant_c 33%) and use a switch statement."
                  >
                    <CodeBlock
                      code={`const result = await EmoraTest.evaluateFlag('headline-test');
const headline = document.getElementById('headline');

switch (result.variant) {
  case 'control':
    headline.textContent = 'Welcome to Our Store';
    break;
  case 'variant_b':
    headline.textContent = 'Shop the Best Deals';
    break;
  case 'variant_c':
    headline.textContent = 'Limited Time Offer';
    break;
}`}
                      onCopy={() => copyToClipboard(`const result = await EmoraTest.evaluateFlag('headline-test');
const headline = document.getElementById('headline');

switch (result.variant) {
  case 'control':
    headline.textContent = 'Welcome to Our Store';
    break;
  case 'variant_b':
    headline.textContent = 'Shop the Best Deals';
    break;
  case 'variant_c':
    headline.textContent = 'Limited Time Offer';
    break;
}`, "example-switch")}
                      copied={copiedCode === "example-switch"}
                    />
                  </ExampleCard>
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* Understanding Your Dashboard */}
              <section id="understanding-dashboard" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">Understanding Your Dashboard</h2>

                <div className="space-y-4">
                  <DashboardItem
                    icon="📊"
                    title="Sessions"
                    description="Every user visit. Shows emotion detected, friction score, abandonment risk, and user intent."
                  />
                  <DashboardItem
                    icon="🔍"
                    title="Why-Analysis"
                    description="Connects emotions to conversions. Shows which emotions lead to purchases and which cause drop-offs. Use this to understand WHY users leave."
                  />
                  <DashboardItem
                    icon="🔥"
                    title="Heatmap"
                    description="Visual display of where users click, scroll, and move. Shows dominant emotion per page element."
                  />
                  <DashboardItem
                    icon="🚩"
                    title="Feature Flags"
                    description="Your A/B tests. Create flags, assign variants, track which version performs better."
                  />
                  <DashboardItem
                    icon="😊"
                    title="Emotion Analysis"
                    description="Each session gets an emotion prediction (frustration, delight, confusion, anxiety, etc.) based on mouse behavior patterns. 86%+ accuracy."
                  />
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* SDK Reference */}
              <section id="sdk-reference" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">SDK Reference</h2>

                <div className="space-y-4">
                  <APIItem
                    name="EmoraTest.init({ sdkKey, apiUrl })"
                    description="Initialize the SDK. Call once per page."
                    returns="Promise<void>"
                  />
                  <APIItem
                    name="EmoraTest.evaluateFlag(flagKey)"
                    description="Get the assigned variant for an A/B test."
                    returns="Promise<{ variant: string, enabled: boolean }>"
                  />
                  <APIItem
                    name="EmoraTest.getVariant(flagKey)"
                    description="Convenience method to get just the variant string."
                    returns="Promise<string | null>"
                  />
                  <APIItem
                    name="EmoraTest.reportOutcome(outcome)"
                    description="Report a conversion outcome. Use 'purchase' for conversions."
                    returns="Promise<void>"
                  />
                  <APIItem
                    name="EmoraTest.getSessionId()"
                    description="Get the current session ID for correlation."
                    returns="string | null"
                  />
                  <APIItem
                    name="EmoraTest.isInitialized()"
                    description="Check if the SDK is currently initialized and tracking."
                    returns="boolean"
                  />
                  <APIItem
                    name="EmoraTest.destroy()"
                    description="Stop tracking and clean up all resources."
                    returns="Promise<void>"
                  />
                </div>
              </section>

              <hr className="border-gray-800 mb-16" />

              {/* Troubleshooting */}
              <section id="troubleshooting" className="mb-16 scroll-mt-8">
                <h2 className="text-2xl font-bold text-white mb-4">Troubleshooting</h2>

                <div className="space-y-4">
                  <TroubleshootItem
                    problem="SDK not loading"
                    solution="Check that the script src URL is correct and your server is running. Verify the URL includes /static/sdk/emoratest.umd.js"
                  />
                  <TroubleshootItem
                    problem="401 errors in console"
                    solution="Your SDK key is invalid. Go to Settings and copy the current key. Make sure you're not using an expired key."
                  />
                  <TroubleshootItem
                    problem="Sessions not appearing in dashboard"
                    solution="Check browser console for errors. Make sure apiUrl points to your EmoraTest server. Verify the SDK key matches your account."
                  />
                  <TroubleshootItem
                    problem="A/B test always shows the same variant"
                    solution="This is correct! Each visitor always gets the same variant. Open an incognito window to see the other variant."
                  />
                  <TroubleshootItem
                    problem="Emotion showing as 'Analyzing...'"
                    solution="The emotion model runs when the session ends. Wait for the user to leave the page or close the tab."
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
        className="absolute top-2 right-2 px-3 py-1 text-xs font-medium rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors opacity-0 group-hover:opacity-100"
      >
        {copied ? "Copied!" : "Copy"}
      </button>
      <pre className="bg-[#1a1a2e] text-white rounded-xl p-4 overflow-x-auto text-sm border border-gray-800">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function TrackingItem({ icon, title }: { icon: string; title: string }) {
  return (
    <div className="flex items-center gap-3 bg-[#1a1a2e] rounded-xl p-4 border border-gray-800">
      <span className="text-2xl">{icon}</span>
      <span className="text-gray-300">{title}</span>
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
    <div className="bg-[#1a1a2e] rounded-xl p-5 border border-gray-800">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-[#007BFF] to-[#7C3AED] flex items-center justify-center text-white font-bold">
          {step}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
          <p className="text-gray-400 mb-3">{description}</p>
          {children}
        </div>
      </div>
    </div>
  );
}

function ExampleCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[#1a1a2e] rounded-xl p-5 border border-gray-800">
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 mb-4">{description}</p>
      {children}
    </div>
  );
}

function DashboardItem({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-4 bg-[#1a1a2e] rounded-xl p-4 border border-gray-800">
      <span className="text-2xl flex-shrink-0">{icon}</span>
      <div>
        <h4 className="font-semibold text-white">{title}</h4>
        <p className="text-gray-400 text-sm">{description}</p>
      </div>
    </div>
  );
}

function APIItem({
  name,
  description,
  returns,
}: {
  name: string;
  description: string;
  returns: string;
}) {
  return (
    <div className="bg-[#1a1a2e] rounded-xl p-4 border border-gray-800">
      <code className="text-[#007BFF] font-mono text-sm">{name}</code>
      <p className="text-gray-400 text-sm mt-2">{description}</p>
      <p className="text-gray-500 text-xs mt-1">Returns: {returns}</p>
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
    <div className="bg-[#1a1a2e] rounded-xl p-4 border border-gray-800">
      <h4 className="font-semibold text-red-400 mb-2">&ldquo;{problem}&rdquo;</h4>
      <p className="text-gray-400 text-sm">→ {solution}</p>
    </div>
  );
}
