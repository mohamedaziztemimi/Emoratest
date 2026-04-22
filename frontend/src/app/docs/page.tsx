"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";

interface Section {
  id: string;
  title: string;
  subitems?: { id: string; title: string }[];
}

const sections: Section[] = [
  { id: "getting-started", title: "Getting Started" },
  { id: "installation", title: "Installation" },
  { id: "tracked-automatically", title: "What Gets Tracked Automatically" },
  { id: "tracking-conversions", title: "Tracking Conversions" },
  { id: "running-ab-tests", title: "Running A/B Tests" },
  { id: "ab-examples", title: "A/B Test Examples" },
  { id: "understanding-dashboard", title: "Understanding Your Dashboard" },
  { id: "sdk-reference", title: "SDK Reference" },
  { id: "troubleshooting", title: "Troubleshooting" },
];

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState("getting-started");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const sectionRefs = useRef<Record<string, HTMLElement>>({});

  useEffect(() => {
    const observers = sections.map((section) => {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && entry.intersectionRatio > 0.1) {
              setActiveSection(section.id);
            }
          });
        },
        { threshold: 0.1, rootMargin: "-80px 0px -80px 0px" }
      );

      const element = document.getElementById(section.id);
      if (element) {
        observer.observe(element);
        sectionRefs.current[section.id] = element;
      }

      return observer;
    });

    return () => observers.forEach((obs) => obs.disconnect());
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      const offset = 80;
      const top = element.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: "smooth" });
    }
  };

  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: "system-ui, -apple-system, sans-serif" }}>
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50" style={{ height: "64px" }}>
        <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
          <Link href="/" className="text-sm font-medium text-[#007BFF] hover:underline">
            ← Back to Home
          </Link>
          <h1 className="text-lg font-semibold text-gray-900">EmoraTest Documentation</h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto flex">
        {/* Left Sidebar - TOC */}
        <nav className="hidden md:block w-64 flex-shrink-0 sticky top-[64px] h-[calc(100vh-64px)] overflow-y-auto border-r border-gray-200 bg-white">
          <div className="p-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">On this page</p>
            <ul className="space-y-1">
              {sections.map((section) => (
                <li key={section.id}>
                  <button
                    onClick={() => scrollToSection(section.id)}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeSection === section.id
                        ? "bg-[#007BFF]/10 text-[#007BFF] font-medium"
                        : "text-gray-600 hover:bg-gray-100"
                    }`}
                  >
                    {section.title}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </nav>

        {/* Right Content Area */}
        <main className="flex-1 min-w-0 p-6 lg:p-8">
          <div className="max-w-3xl">
            {/* Hero */}
            <div className="mb-10">
              <h1 className="text-3xl font-bold text-gray-900 mb-3">SDK Documentation</h1>
              <p className="text-lg text-gray-600">
                Complete guide to installing and using EmoraTest on your website.
              </p>
            </div>

            {/* Getting Started */}
            <section id="getting-started" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Getting Started</h2>
              <p className="text-gray-600 mb-4 leading-relaxed">
                <strong>EmoraTest</strong> detects user emotions from behavior patterns and helps you optimize conversions.
                Add one script to your site to start tracking sessions, emotions, and run A/B tests.
              </p>
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                <p className="text-sm text-blue-800 font-medium mb-2">What you&apos;ll need:</p>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Your <strong>SDK Key</strong> — found in Settings → SDK after signing up</li>
                  <li>• Access to edit your website&apos;s HTML or JavaScript files</li>
                </ul>
              </div>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* Installation */}
            <section id="installation" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Installation</h2>
              <p className="text-gray-600 mb-4">
                Choose your platform below. The SDK loads from our CDN and initializes automatically.
              </p>

              {/* HTML Installation */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">HTML (Any Website)</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Add this before the closing <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">&lt;/head&gt;</code> tag:
                </p>
                <CodeBlock
                  id="install-html"
                  language="html"
                  code={`<script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
<script>
  EmoraTest.init({
    sdkKey: "YOUR_SDK_KEY",
    apiUrl: "https://emoratest.com"
  });
</script>`}
                  copiedId={copiedCode}
                  onCopy={copyToClipboard}
                />
              </div>

              {/* Next.js Installation */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Next.js 14 (App Router)</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Create a Client Component and add it to your root layout:
                </p>
                <CodeBlock
                  id="install-nextjs"
                  language="tsx"
                  code={`// src/components/EmoraTestScript.tsx
"use client";

import { useEffect } from "react";

export default function EmoraTestScript({ sdkKey }: { sdkKey: string }) {
  useEffect(() => {
    if (!sdkKey) return;

    // Prevent duplicate script
    if (document.querySelector('script[src*="emoratest.umd.js"]')) {
      if ((window as any).EmoraTest) {
        (window as any).EmoraTest.init({
          sdkKey,
          apiUrl: "https://emoratest.com"
        });
      }
      return;
    }

    const script = document.createElement("script");
    script.src = "https://emoratest.com/static/sdk/emoratest.umd.js";
    script.async = true;

    script.onload = () => {
      if ((window as any).EmoraTest) {
        (window as any).EmoraTest.init({
          sdkKey,
          apiUrl: "https://emoratest.com"
        });
      }
    };

    document.body.appendChild(script);
  }, [sdkKey]);

  return null;
}

// Then in app/layout.tsx:
import EmoraTestScript from "@/components/EmoraTestScript";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <EmoraTestScript sdkKey={process.env.NEXT_PUBLIC_EMORATEST_KEY} />
      </body>
    </html>
  );
}`}
                  copiedId={copiedCode}
                  onCopy={copyToClipboard}
                />
              </div>

              {/* React Installation */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">React (Vite, Create React App)</h3>
                <CodeBlock
                  id="install-react"
                  language="tsx"
                  code={`// In your root App component (App.tsx or index.tsx)
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    if (document.querySelector('script[src*="emoratest.umd.js"]')) {
      if ((window as any).EmoraTest) {
        (window as any).EmoraTest.init({
          sdkKey: "YOUR_SDK_KEY",
          apiUrl: "https://emoratest.com"
        });
      }
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://emoratest.com/static/sdk/emoratest.umd.js';
    script.async = true;

    script.onload = () => {
      if ((window as any).EmoraTest) {
        (window as any).EmoraTest.init({
          sdkKey: "YOUR_SDK_KEY",
          apiUrl: "https://emoratest.com"
        });
      }
    };

    document.body.appendChild(script);
  }, []);

  return <YourApp />;
}`}
                  copiedId={copiedCode}
                  onCopy={copyToClipboard}
                />
              </div>

              <div className="bg-yellow-50 border border-yellow-100 rounded-xl p-4 mt-4">
                <p className="text-sm text-yellow-800">
                  <strong>Important:</strong> Replace <code>YOUR_SDK_KEY</code> with your actual SDK key from the dashboard.
                  The <code>apiUrl</code> parameter is optional and defaults to <code>https://emoratest.com</code>.
                </p>
              </div>
              <p className="text-gray-600 mt-4 text-sm">
                The SDK automatically handles session persistence across pages — no additional code needed.
              </p>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* Tracked Automatically */}
            <section id="tracked-automatically" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">What Gets Tracked Automatically</h2>
              <p className="text-gray-600 mb-6">
                Once installed, the SDK automatically tracks all user behavior signals:
              </p>

              <div className="grid md:grid-cols-2 gap-4 mb-6">
                {[
                  { icon: "🖱️", title: "Mouse movements", desc: "Every cursor movement tracked for emotion analysis" },
                  { icon: "👆", title: "Clicks", desc: "All clicks with element targets and timestamps" },
                  { icon: "📜", title: "Scroll behavior", desc: "Scroll depth, velocity, and patterns" },
                  { icon: "😤", title: "Rage clicks", desc: "Rapid clicking indicates frustration" },
                  { icon: "🚪", title: "Exit intent", desc: "Cursor moving toward close button" },
                  { icon: "↕️", title: "Scroll retreats", desc: "Back-and-forth scrolling shows confusion" },
                  { icon: "⏱️", title: "Session duration", desc: "Time spent on each page" },
                  { icon: "📄", title: "Page URLs", desc: "Navigation tracking across pages" },
                ].map((item) => (
                  <div key={item.title} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
                    <span className="text-2xl">{item.icon}</span>
                    <div>
                      <p className="font-medium text-gray-900">{item.title}</p>
                      <p className="text-sm text-gray-500">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-green-50 border border-green-100 rounded-xl p-4">
                <p className="text-sm text-green-800">
                  <strong>No extra code needed!</strong> Just install and the dashboard will start showing session data, emotion predictions, and behavior signals within seconds.
                </p>
              </div>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* Tracking Conversions */}
            <section id="tracking-conversions" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Tracking Conversions</h2>
              <p className="text-gray-600 mb-4">
                To measure what matters, tell EmoraTest when a user converts (makes a purchase, signs up, completes a goal).
              </p>

              <CodeBlock
                id="conversion-tracking"
                language="javascript"
                code={`// Call this when a user completes your goal action

// Example 1: After a purchase button click
document.getElementById('buy-button').addEventListener('click', function() {
  EmoraTest.track('purchase', { value: 49.99, currency: 'USD' });
});

// Example 2: After form submission
document.getElementById('signup-form').addEventListener('submit', function() {
  EmoraTest.track('signup', { plan: 'premium' });
});

// Example 3: Custom conversion event
document.getElementById('contact-form').addEventListener('submit', function() {
  EmoraTest.track('contact', { source: 'landing_page' });
});

// Example 4: In React/Next.js
const handlePurchase = () => {
  // Your purchase logic
  completeOrder();

  // Track conversion
  if (window.EmoraTest) {
    window.EmoraTest.track('purchase', { value: orderTotal });
  }
};`}
                copiedId={copiedCode}
                onCopy={copyToClipboard}
              />

              <p className="text-gray-600 mt-4 text-sm">
                The first argument is the event name. Common events: <code className="bg-gray-100 px-1 rounded">&apos;purchase&apos;</code>, <code className="bg-gray-100 px-1 rounded">&apos;signup&apos;</code>, <code className="bg-gray-100 px-1 rounded">&apos;lead&apos;</code>.
                You can use any name for custom goals and include additional properties as an optional second argument.
              </p>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* Running A/B Tests */}
            <section id="running-ab-tests" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Running A/B Tests</h2>
              <p className="text-gray-600 mb-6">
                EmoraTest includes a full-featured A/B testing platform. Create flags, assign variants, and track which version performs better.
              </p>

              <div className="space-y-6">
                {/* Step 1 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Step 1: Create a Feature Flag</h3>
                  <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                    <li>Go to <strong>Feature Flags</strong> in the dashboard</li>
                    <li>Click <strong>New Flag</strong></li>
                    <li>Enter a key (e.g., <code>hero-headline</code>) and name</li>
                    <li>Add 2 variants: <code>control (50%)</code> and <code>variant_b (50%)</code></li>
                    <li>Click <strong>Activate</strong></li>
                  </ol>
                </div>

                {/* Step 2 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Step 2: Use the Flag in Your Code</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    On the page you want to test, evaluate the flag and show different content:
                  </p>
                  <CodeBlock
                    id="ab-test-code"
                    language="javascript"
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

setupABTest();

// In React/Next.js:
import { useEffect, useState } from 'react';

function Headline() {
  const [headline, setHeadline] = useState('Loading...');

  useEffect(() => {
    EmoraTest.evaluateFlag('hero-headline').then(result => {
      if (result.variant === 'control') {
        setHeadline('Welcome to Our Store');
      } else {
        setHeadline('Shop the Best Deals Today');
      }
    });
  }, []);

  return <h1>{headline}</h1>;
}`}
                    copiedId={copiedCode}
                    onCopy={copyToClipboard}
                  />
                </div>

                {/* Step 3 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Step 3: Track Conversions</h3>
                  <p className="text-sm text-gray-600">
                    Make sure you have <code className="bg-gray-100 px-1 rounded">EmoraTest.track(&apos;purchase&apos;)</code> on your conversion page (see Section 4 above).
                  </p>
                </div>

                {/* Step 4 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Step 4: Check Results</h3>
                  <p className="text-sm text-gray-600">
                    Go to <strong>Feature Flags</strong> → click <strong>View Results</strong> on your flag. You&apos;ll see how many visitors saw each variant and which one converts better.
                  </p>
                </div>
              </div>

              <div className="bg-purple-50 border border-purple-100 rounded-xl p-4 mt-6">
                <p className="text-sm text-purple-800">
                  <strong>How it works:</strong> Each visitor automatically gets assigned one variant and always sees the same one.
                  The SDK handles this deterministically using stable hashing — you don&apos;t need to manage user assignments.
                </p>
              </div>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* A/B Test Examples */}
            <section id="ab-examples" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">A/B Test Examples</h2>

              <div className="space-y-6">
                {/* Example 1 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Test Button Color</h3>
                  <CodeBlock
                    id="example-button-color"
                    language="javascript"
                    code={`const result = await EmoraTest.evaluateFlag('cta-button-color');
const button = document.getElementById('cta-button');

if (result.variant === 'control') {
  // Original: Blue button
  button.style.backgroundColor = '#007BFF';
  button.textContent = 'Buy Now';
} else {
  // Variant: Orange with urgency
  button.style.backgroundColor = '#FF6B00';
  button.textContent = 'Buy Now — Free Shipping';
}`}
                    copiedId={copiedCode}
                    onCopy={copyToClipboard}
                  />
                </div>

                {/* Example 2 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Test Entire Page Sections</h3>
                  <CodeBlock
                    id="example-section-toggle"
                    language="javascript"
                    code={`const result = await EmoraTest.evaluateFlag('pricing-layout');

if (result.variant === 'control') {
  document.getElementById('pricing-v1').style.display = 'block';
  document.getElementById('pricing-v2').style.display = 'none';
} else {
  document.getElementById('pricing-v1').style.display = 'none';
  document.getElementById('pricing-v2').style.display = 'block';
}`}
                    copiedId={copiedCode}
                    onCopy={copyToClipboard}
                  />
                </div>

                {/* Example 3 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Test with More Than 2 Variants</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Create a flag with 3 variants (control 34%, variant_b 33%, variant_c 33%) and use a switch statement:
                  </p>
                  <CodeBlock
                    id="example-multivariate"
                    language="javascript"
                    code={`const result = await EmoraTest.evaluateFlag('hero-variant');
const hero = document.getElementById('hero');

switch (result.variant) {
  case 'control':
    hero.innerHTML = '<h1>Welcome</h1><p>Start your journey</p>';
    break;
  case 'variant_b':
    hero.innerHTML = '<h1>Join 10,000+ Customers</h1><p>Limited time offer</p>';
    break;
  case 'variant_c':
    hero.innerHTML = '<h1>Free Shipping Today</h1><p>Use code: FREESHIP</p>';
    break;
}`}
                    copiedId={copiedCode}
                    onCopy={copyToClipboard}
                  />
                </div>
              </div>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* Understanding Dashboard */}
            <section id="understanding-dashboard" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Understanding Your Dashboard</h2>
              <p className="text-gray-600 mb-6">
                The EmoraTest dashboard gives you deep insights into user behavior and emotions.
              </p>

              <div className="space-y-4">
                {[
                  {
                    title: "Sessions",
                    desc: "Every user visit. Shows emotion detected, friction score, abandonment risk, and user intent. Real-time updates.",
                    color: "blue",
                  },
                  {
                    title: "Why-Analysis",
                    desc: "Connects emotions to conversions. Shows which emotions lead to purchases and which cause drop-offs. Use this to understand WHY users leave.",
                    color: "purple",
                  },
                  {
                    title: "Heatmap",
                    desc: "Visual display of where users click, scroll, and move. Shows dominant emotion per page element with color gradients.",
                    color: "green",
                  },
                  {
                    title: "Feature Flags",
                    desc: "Your A/B tests. Create flags, assign variants, track which version performs better with statistical significance.",
                    color: "orange",
                  },
                  {
                    title: "Emotion Analysis",
                    desc: "Each session gets an emotion prediction (frustration, delight, confusion, anxiety, boredom, focus) based on mouse behavior patterns. 86%+ accuracy.",
                    color: "red",
                  },
                ].map((item) => (
                  <div key={item.title} className="flex items-start gap-4 p-4 bg-white rounded-lg border border-gray-200">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                      style={{
                        backgroundColor: item.color === "blue" ? "#DBEAFE" :
                                       item.color === "purple" ? "#EDE9FE" :
                                       item.color === "green" ? "#D1FAE5" :
                                       item.color === "orange" ? "#FED7AA" : "#FEE2E2",
                      }}
                    >
                      <span className="text-lg">📊</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{item.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* SDK Reference */}
            <section id="sdk-reference" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">SDK Reference</h2>
              <p className="text-gray-600 mb-6">Complete reference of all available EmoraTest SDK methods.</p>

              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-4 py-3 font-semibold text-gray-900">Method</th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-900">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {[
                      {
                        method: "EmoraTest.init({ sdkKey, apiUrl })",
                        desc: "Initialize the SDK. Call once per page load. apiUrl defaults to https://emoratest.com.",
                      },
                      {
                        method: "await EmoraTest.evaluateFlag(flagKey)",
                        desc: "Get assigned variant for an A/B test. Returns { variant: string, enabled: boolean }.",
                      },
                      {
                        method: "EmoraTest.track(eventName, properties?)",
                        desc: "Track a custom event like purchase, signup, etc. Optional properties object for metadata.",
                      },
                      {
                        method: "EmoraTest.getSessionId()",
                        desc: "Get the current session ID (changes on each page visit).",
                      },
                      {
                        method: "EmoraTest.getVisitorId()",
                        desc: "Get the persistent visitor ID (same across sessions for the same browser).",
                      },
                      {
                        method: "EmoraTest.destroy()",
                        desc: "Clean up the SDK instance. Useful for single-page apps.",
                      },
                    ].map((item) => (
                      <tr key={item.method}>
                        <td className="px-4 py-3">
                          <code className="text-xs bg-gray-100 px-2 py-1 rounded text-[#007BFF]">
                            {item.method}
                          </code>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{item.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <hr className="border-gray-200 my-10" />

            {/* Troubleshooting */}
            <section id="troubleshooting" className="mb-12 scroll-mt-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Troubleshooting</h2>
              <p className="text-gray-600 mb-6">Common issues and how to fix them.</p>

              <div className="space-y-4">
                {[
                  {
                    q: "SDK not loading / window.EmoraTest is undefined",
                    a: "Check that the script src URL is correct: https://emoratest.com/static/sdk/emoratest.umd.js. Open browser DevTools Console to see error messages. For Next.js, make sure your component has 'use client' directive.",
                  },
                  {
                    q: "401 Unauthorized errors in console",
                    a: "Your SDK key is invalid. Go to Settings → SDK in the dashboard and copy the current key. Make sure you didn't accidentally include extra spaces.",
                  },
                  {
                    q: "Sessions not appearing in dashboard",
                    a: "Verify the SDK is loaded by typing window.EmoraTest in the browser console. Check that apiUrl points to https://emoratest.com. If using localhost, ensure your backend is running.",
                  },
                  {
                    q: "A/B test always shows the same variant",
                    a: "This is correct! Each visitor always gets the same variant for consistency. Open an incognito window to see the other variant. The SDK uses stable hashing based on visitor ID.",
                  },
                  {
                    q: "Emotion showing as 'Analyzing...'",
                    a: "The emotion model runs when the session ends or after sufficient data is collected. Wait for the user to leave the page or spend more time on the page. Results appear within 30 seconds.",
                  },
                  {
                    q: "Content Security Policy (CSP) errors",
                    a: "Add https://emoratest.com to your CSP script-src directive. For Next.js, update next.config.js headers() to include 'https://emoratest.com' in script-src.",
                  },
                ].map((item, i) => (
                  <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
                    <h4 className="font-semibold text-gray-900 mb-1">{item.q}</h4>
                    <p className="text-sm text-gray-600">{item.a}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Footer */}
            <div className="mt-16 pt-8 border-t border-gray-200 text-center">
              <p className="text-sm text-gray-500">
                Questions? Email <a href="mailto:hello@emoratest.com" className="text-[#007BFF] hover:underline">hello@emoratest.com</a>
              </p>
            </div>
          </div>
        </main>
      </div>

      {/* Mobile TOC Dropdown */}
      <div className="md:hidden fixed bottom-4 right-4 z-50">
        <select
          className="bg-white border border-gray-200 rounded-lg px-4 py-2 text-sm shadow-lg"
          onChange={(e) => scrollToSection(e.target.value)}
          defaultValue=""
        >
          <option value="" disabled>Jump to section...</option>
          {sections.map((section) => (
            <option key={section.id} value={section.id}>{section.title}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

function CodeBlock({
  id,
  language,
  code,
  copiedId,
  onCopy,
}: {
  id: string;
  language: string;
  code: string;
  copiedId: string | null;
  onCopy: (code: string, id: string) => void;
}) {
  return (
    <div className="relative group mb-4">
      <div
        className="rounded-xl overflow-hidden"
        style={{ backgroundColor: "#1a1a2e" }}
      >
        <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
          <span className="text-xs text-gray-400 uppercase">{language}</span>
          <button
            onClick={() => onCopy(code, id)}
            className="text-xs text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors"
          >
            {copiedId === id ? (
              <>✓ Copied!</>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy
              </>
            )}
          </button>
        </div>
        <pre className="bg-[#1a1a2e] text-gray-300 rounded-xl p-4 overflow-x-auto text-sm border border-gray-800">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}
