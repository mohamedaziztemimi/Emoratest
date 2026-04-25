EmoraTest — Landing Page, Docs, Favicon & Dark Mode Fix Playbook
9 Prompts — Run in order, validate each before moving on.

RULES — Paste at the top of EVERY prompt:
RULES — Follow these strictly:
1. READ all relevant files BEFORE making any changes
2. Report what you found BEFORE writing code
3. "use client" only on components using hooks — NEVER on page.tsx
4. Never add "use client" to layout.tsx
5. metadata exports only in server components
6. viewport export separate from metadata
7. NO document.createElement at module level — must be inside useEffect
8. Never make API calls on landing page components
9. Never initialize isVisible as false (content disappears)
10. Never use LazySection wrappers on landing page
11. After changes, list EVERY file modified
12. Make surgical changes — don't rewrite working code
13. Landing page is at frontend/src/app/(landing)/page.tsx
14. Auth pages are at frontend/src/app/(auth)/
15. Dashboard is at frontend/src/app/dashboard/

✅ Prompt 1 — Fix the Favicon (too small in browser tab) — DONE
READ these files:
- frontend/src/app/layout.tsx
- frontend/src/app/favicon.ico (check if it exists and its size)
- frontend/public/ directory (list all files, check for favicon files)
- frontend/src/app/(landing)/page.tsx (check if it has metadata with icons)

Report:
1. Where is the current favicon located?
2. What size is it? (should be at least 32x32, ideally 48x48 or larger)
3. Is there a metadata export that references icons?
4. Are there multiple icon files (favicon.ico, icon.png, apple-touch-icon.png)?

Now fix the favicon:

1. The current favicon is the "E" logo in a blue (#007BFF) rounded square.
   It appears tiny in the browser tab because the icon file is likely
   too small or not optimized for browser tabs.

2. Generate a new favicon set using a simple SVG approach. Create a
   file frontend/src/app/icon.svg with this content:

   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
     <rect width="48" height="48" rx="10" fill="#007BFF"/>
     <text x="24" y="33" text-anchor="middle" font-family="Arial, sans-serif"
           font-weight="700" font-size="30" fill="white">E</text>
   </svg>

3. Also create frontend/src/app/icon.tsx for Next.js dynamic icon generation:

   import { ImageResponse } from 'next/og'

   export const size = { width: 48, height: 48 }
   export const contentType = 'image/png'

   export default function Icon() {
     return new ImageResponse(
       (
         <div style={{
           fontSize: 30,
           background: '#007BFF',
           width: '100%',
           height: '100%',
           display: 'flex',
           alignItems: 'center',
           justifyContent: 'center',
           color: 'white',
           borderRadius: 10,
           fontWeight: 700,
           fontFamily: 'Arial, sans-serif',
         }}>
           E
         </div>
       ),
       { ...size }
     )
   }

4. Also create frontend/src/app/apple-icon.tsx with size 180x180
   using the same approach but with larger dimensions.

5. In the root layout.tsx, make sure the metadata includes:
   icons: {
     icon: '/icon.svg',
     apple: '/apple-icon.png',
   }

6. Delete the old tiny favicon.ico if it exists (Next.js will use
   the new icon.tsx instead).

Report all files created/modified/deleted.
Validation:
bashcd frontend && npm run build
# Open browser → check the tab icon
# It should be a clear blue square with white "E", not tiny/blurry
# Check in Chrome DevTools → Application → Manifest to verify icons load

✅ Prompt 2 — Fix Dark Mode: Remove duplicate toggle, fix the broken one — DONE (NO ISSUES FOUND)
READ these files and search for dark mode related code:

1. grep -r "dark" frontend/src/ --include="*.tsx" --include="*.ts" -l
2. grep -r "theme" frontend/src/ --include="*.tsx" --include="*.ts" -l
3. grep -r "darkMode\|dark-mode\|dark_mode\|setDark\|toggleDark\|useTheme" frontend/src/ --include="*.tsx" --include="*.ts" -l

Read ALL files returned by these searches.

Also read:
- frontend/src/app/layout.tsx
- frontend/src/app/dashboard/layout.tsx
- frontend/src/components/Sidebar.tsx (or wherever the sidebar is)
- The top navbar/header component in the dashboard

Report:
1. How many dark mode toggle buttons exist and WHERE are they?
   (I know there are 2 — one in the top navbar, one in the sidebar/bottom)
2. What mechanism do they use? (CSS class on html/body? React context?
   localStorage? next-themes?)
3. Which one works and which one doesn't?
4. Are there conflicting implementations?

DO NOT change anything yet. Just report.
Validation: Read the report carefully. Identify which toggle is the "real" one.

✅ Prompt 3 — Fix Dark Mode: Single working toggle — DONE (ALREADY WORKING)
Based on the audit from the previous prompt, fix the dark mode situation:

1. KEEP only ONE dark mode toggle button — the one in the top
   navbar/header of the dashboard (the moon/sun icon near the
   notifications bell and user avatar).

2. REMOVE the duplicate dark mode toggle from the sidebar/bottom.
   Delete the button/icon but DO NOT change the sidebar layout or
   break the sign-out button or user profile section.

3. Make sure the remaining toggle ACTUALLY WORKS:
   - It should toggle a 'dark' class on the <html> element
   - It should persist the choice in localStorage under key 'theme'
   - On page load, read localStorage and apply the correct class
   - Use Tailwind's dark mode (class strategy): make sure tailwind.config.ts
     has: darkMode: 'class'

4. If the project uses next-themes, use that consistently:
   - Wrap the root layout in <ThemeProvider attribute="class"
     defaultTheme="light" enableSystem={false}>
   - Use useTheme() hook in the toggle button component
   - Remove any manual document.documentElement.classList.toggle code

5. If the project does NOT use next-themes, implement it cleanly:
   - Install: npm install next-themes
   - Add ThemeProvider to frontend/src/app/layout.tsx
   - Create a single ThemeToggle component that uses useTheme()
   - Place it in the dashboard header only

IMPORTANT:
- The landing page should ALWAYS be light mode (no toggle there)
- Only the dashboard has the dark mode toggle
- Don't break the auth pages (login/signup)

Report all files modified.
Validation:
bashcd frontend && npm run build
# Open dashboard in browser:
# 1. Only ONE dark mode toggle should exist (in the top header bar)
# 2. Click it → entire dashboard should switch to dark mode
# 3. Refresh page → dark mode should persist
# 4. Click again → back to light mode
# 5. Navigate to landing page → should always be light
# 6. Check sidebar bottom → no duplicate toggle button

✅ Prompt 4 — Landing Page: Fix trust signals and production content — DONE (ALREADY CORRECT)
READ the landing page completely:
- frontend/src/app/(landing)/page.tsx
- Every component imported by the landing page
- frontend/src/app/(landing)/layout.tsx

Report the complete list of sections in order.

Now make these SURGICAL changes (do NOT rewrite the entire page,
only change the specific text/elements listed):

SECTION 1 — HERO:
Change the main headline from:
  "Know Exactly Why Users Leave."
To:
  "See What Your Users Actually Feel."

Change the subtitle from:
  "EmoraTest detects confusion and frustration in real-time. Most teams find their conversion killer within 2 hours."
To:
  "EmoraTest detects 8 emotions from mouse behavior — frustration, confusion, delight, and more. Find your conversion killer in hours, not weeks."

Change the primary CTA button from:
  "See Your Emotion Heatmap →"
To:
  "Start Free — No Credit Card"

Change the secondary CTA from:
  "Watch 2-min Demo"
To:
  "See How It Works"

REMOVE these fake social proof numbers from the hero:
  "2,400+ growth teams trust EmoraTest"
  "847 teams joined this month"
  These are lies. You have no customers yet.

REPLACE with honest early-stage trust signals:
  "Built for growth teams, PMs, and CRO leads at SaaS & e-commerce companies"
  (No fake numbers. Just describe who it's for.)

REMOVE the fake live ticker:
  "LIVE: 130 sessions analyzed, 5 frustration spikes, 1 test running"
  Replace with a STATIC visual showing a mini dashboard preview or
  remove it entirely. No fake live data.

KEEP the stat cards but change the text to be honest:
  "+32% Conversions" → "Detect 8 Emotions" with subtitle "From mouse behavior patterns"
  "40% Less Churn" → "80%+ Accuracy" with subtitle "XGBoost ML classifier"
  "85-95% Emotion Accuracy" → "Works Everywhere" with subtitle "One script tag. Any website."
  "2x Faster Winners" → "Real-Time Analysis" with subtitle "Insights in seconds, not days"

These are factual claims about your product capabilities, not fake customer metrics.

DO NOT change the layout, animations, colors, or structure.
Only change the TEXT CONTENT and remove fake numbers.

Report every text change made.
Validation:
bashcd frontend && npm run build
# Open landing page in browser
# Check: no fake customer numbers, no fake live ticker
# Hero text should be new version
# Stat cards should show product capabilities, not fake metrics
# Overall layout should look identical — just better text

✅ Prompt 5 — Landing Page: Fix features section and testimonials — DONE
READ the features section of the landing page.

FEATURES SECTION — Change feature card descriptions:

Card "Emotion Heatmaps":
  Rename to: "Page Insights"
  Description: "See which pages cause frustration, confusion, or delight.
  Every page ranked by emotional friction with actionable breakdowns."
  (We don't have visual heatmaps — don't promise them)

Card "8-Emotion ML Classifier":
  Keep the title. Change description to:
  "Our XGBoost model detects confusion, frustration, delight, anxiety,
  hesitation, focus, boredom, and satisfaction from mouse behavior
  with 80%+ accuracy. No cameras. No surveys. Just behavior."

Card "Why-Analysis":
  Rename to: "Automatic Diagnosis"
  Description: "EmoraTest automatically detects issues — rage clicks,
  hesitation spikes, high drop-offs — and tells you exactly why users
  struggle and what to fix."

Card "Session Replay":
  Rename to: "Session Explorer"
  Description: "Browse every user session with emotion labels. Filter
  by frustrated, confused, or satisfied sessions. Click into any
  session to see the full emotion breakdown and behavior signals."
  (We don't have video replay — don't call it replay)

Card "Funnel Analytics":
  Rename to: "Emotion Alerts"
  Description: "Get notified when frustration spikes on any page.
  Set thresholds, choose your channel (email or Slack), and never
  miss a conversion-killing issue."
  (We don't have funnel analytics — replace with what we're building)

Card "Real-time Alerts":
  Keep this but update description:
  "Configure alerts for any emotion on any page. Set thresholds
  like 'email me when frustration exceeds 30% on checkout.' Works
  with email and Slack."

TESTIMONIALS SECTION:
  REMOVE the fake testimonials entirely:
  - "Sarah K., Head of Growth @ Series B SaaS" — this is fake
  - "Marcus T., Senior PM @ E-commerce Platform" — this is fake
  - "$2.1M revenue recovered" — this is a lie
  - "40% faster shipping" — this is a lie

  REPLACE with a simple section:
  Title: "Built for teams who care about user experience"
  Show 3 use-case cards instead of fake quotes:
  1. "Growth Teams" — "Find the pages killing your conversion rate
     and fix them with data, not guesswork."
  2. "Product Managers" — "Understand why users drop off at every step
     of your funnel with emotion-level detail."
  3. "UX Researchers" — "Replace hours of user interviews with
     automated emotion detection on every session."

DO NOT change the layout structure. Only change text content
and replace fake testimonials with use-case cards.

Report every change made.
Validation:
bashcd frontend && npm run build
# Open landing page in browser
# Check: no fake testimonials, no fake customer names
# Features should describe REAL capabilities
# No mention of "Session Replay" (video), "Funnel Analytics", or "Emotion Heatmaps"

✅ Prompt 6 — Landing Page: Fix pricing and footer — DONE
READ the pricing section and footer of the landing page.

PRICING SECTION — Fix these issues:

The pricing tiers look okay but need these fixes:

STARTER (Free) plan:
  Change "Up to 5,000 sessions/month" → "Up to 1,000 sessions/month"
  (5,000 is too generous for free — people won't upgrade)
  Change "3 active experiments" → "1 active experiment"
  Change "Basic emotion heatmaps" → "Basic emotion detection"
  Keep: "A/B testing", "Email support"
  Add: "Community support"

GROWTH ($79/month) plan:
  Keep the price.
  Change "Up to 100,000 sessions/month" → "Up to 50,000 sessions/month"
  Keep: "Unlimited experiments", "Full emotion ML"
  Change "Multi-armed bandits" → "Automatic Diagnosis"
  Change "Why-analysis & revenue linking" → "Emotion alerts (email + Slack)"
  Keep: "Slack & Jira integrations", "Priority support"
  Add: "Page insights", "Session emotion filters"

ENTERPRISE plan:
  Keep "Custom pricing"
  Keep: "Unlimited sessions", "HIPAA & GDPR compliance", "SSO"
  Change "Snowflake / BigQuery sync" → "Data warehouse export"
  Keep: "SLA guarantee", "Dedicated success manager"
  Change "Custom ML training" → "Custom emotion models"

REMOVE these compliance badges from the pricing section:
  "GDPR Compliant" — keep (this is achievable)
  "HIPAA Ready" — REMOVE (you are NOT HIPAA compliant yet, this is
  a legal liability. Only add this when you actually are.)
  "99.9% Uptime SLA" — REMOVE from free/growth tiers (only Enterprise)

FOOTER:
  Remove "Careers" link (you're not hiring)
  Remove "Blog" link (you don't have a blog)
  Remove "Help Center" link (you don't have one — Docs is enough)
  Keep: Features, Pricing, Documentation, About, Contact,
        Privacy Policy, Terms of Service

  Change "2,400+ growth teams" in footer to:
  "Built for growth teams who care about user experience."

Report every change made.
Validation:
bashcd frontend && npm run build
# Open landing page → scroll to pricing
# Check: no HIPAA badge, adjusted session limits, no "Blog" or "Careers" links
# Footer should only link to pages that actually exist

✅ Prompt 7 — Landing Page: Fix the "How It Works" section — DONE (ALREADY CORRECT)
READ the "How It Works" section of the landing page (the 4-step section).

Change the steps to be more specific and honest:

Step 01: "Install the Snippet"
  Keep title. Change description to:
  "Add one script tag to your site. Works with HTML, React, Next.js,
  Vue, or any JavaScript framework. Takes 2 minutes."
  Keep "2 min setup" badge.

Step 02: "Emotion ML Activates"
  Change title to: "Behavior Tracking Starts"
  Change description to:
  "The SDK automatically tracks mouse movements, clicks, scroll patterns,
  rage clicks, and exit intent. No configuration needed."
  Change badge: "Instant, automatic" → "Zero config"

Step 03: "See the Why"
  Change title to: "Emotions Are Detected"
  Change description to:
  "Our XGBoost model analyzes behavior patterns and classifies each
  session into one of 8 emotions. Results appear on your dashboard
  within seconds of the session ending."
  Change badge: "Live dashboard" → "8 emotions detected"

Step 04: "Test and Win"
  Change title to: "Take Action"
  Change description to:
  "See which pages cause frustration, get automated diagnosis of issues,
  set up alerts, and create A/B tests — all from one dashboard."
  Change badge: "30-50% faster winners" → "Detect → Diagnose → Fix"

DO NOT change the layout, step numbers, or visual style.

Report every text change made.
Validation:
bashcd frontend && npm run build
# Open landing page → check "How It Works" section
# Steps should be factual, no fake percentage claims

✅ Prompt 8 — Rebuild the Documentation Page — DONE
READ the current docs page:
- frontend/src/app/dashboard/docs/page.tsx OR
- frontend/src/app/(landing)/docs/page.tsx OR
- wherever the docs page lives

Search for it: find frontend/src -name "*.tsx" -path "*doc*"

Report where it is and what it currently contains.

Now REPLACE the docs page content with this improved documentation.
Keep the same page shell/layout but replace the inner content:

The documentation should have these sections with IDs for anchor linking:

1. #getting-started — "Getting started"
   Brief intro: what EmoraTest does, what you need (SDK key from Settings)

2. #installation — "Installation"
   Three tabs/sections:

   HTML (Any website):
```html
   <script src="https://YOUR_DOMAIN/static/sdk/emoratest.umd.js"></script>
   <script>
     EmoraTest.init({ sdkKey: "YOUR_SDK_KEY" });
   </script>
```

   React / Next.js:
```jsx
   "use client";
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
   }
```
   Then add <EmoraTracker /> to your root layout.

   NPM Package (coming soon):
```bash
   npm install emoratest
   # Coming soon — use the script tag method for now
```

3. #auto-tracking — "What gets tracked automatically"
   Show a clean grid of 8 items:
   - Mouse movements (cursor position and velocity)
   - Clicks (element target, coordinates, timestamp)
   - Scroll behavior (depth, velocity, direction changes)
   - Rage clicks (3+ clicks within 500ms on same area)
   - Exit intent (cursor moving to browser chrome)
   - Scroll retreats (scrolling back up to re-read)
   - Dwell time (time spent on each page section)
   - Page navigation (URL changes across the session)

   Add a note: "All tracking is cookieless and GDPR-friendly.
   No personal data is collected — only behavioral patterns."

4. #conversions — "Tracking conversions"
   Show reportOutcome() with examples:
```javascript
   // After a purchase
   window.EmoraTest.reportOutcome('purchase');

   // After signup
   window.EmoraTest.reportOutcome('signup');

   // After booking a demo
   window.EmoraTest.reportOutcome('demo_booked');
```

   Available outcomes: purchase, signup, checkout_completed,
   demo_booked, lead_generated, trial_started

   Auto-detection note: EmoraTest auto-detects outcomes from common
   URL patterns like /success, /thank-you, /confirmation

5. #ab-testing — "Running A/B tests"

   Step 1: Create an experiment in the dashboard (Experiments → New)
   Step 2: Add the flag evaluation code:
```javascript
   const result = await EmoraTest.evaluateFlag('your-flag-key');

   if (result.variant === 'control') {
     // Show original version
   } else if (result.variant === 'variant_b') {
     // Show new version
   }
```
   Step 3: Report conversion with reportOutcome()
   Step 4: Check results in the Experiments dashboard

   Note: Each visitor always sees the same variant (deterministic hashing).
   Open an incognito window to test the other variant.

6. #sdk-reference — "SDK reference"
   Table of all methods:
   | Method | Description |
   | EmoraTest.init({ sdkKey }) | Initialize tracking. Call once. |
   | EmoraTest.reportOutcome(type) | Report conversion outcome. |
   | EmoraTest.evaluateFlag(key) | Get A/B test variant. Returns { variant, enabled }. |
   | EmoraTest.getVariant(key) | Shorthand — returns variant string or null. |
   | EmoraTest.getSessionId() | Current session ID. |
   | EmoraTest.getVisitorId() | Persistent visitor ID (survives page reload). |
   | EmoraTest.isInitialized() | Check if SDK is active. |
   | EmoraTest.destroy() | Clean up and end session. |

7. #troubleshooting — "Troubleshooting"
   Q: SDK not loading?
   → Check script URL, check browser console for errors

   Q: 401 errors?
   → Invalid SDK key. Copy it again from Settings.

   Q: Sessions not appearing?
   → Verify SDK loads: type window.EmoraTest in console

   Q: Emotion shows "Analyzing..."?
   → Emotions are predicted after the session ends. Wait for the user to leave.

   Q: A/B test shows same variant?
   → Correct behavior. Use incognito for other variant.

IMPORTANT DESIGN RULES:
- Use a clean left sidebar with section anchors (table of contents)
- Code blocks should have copy buttons
- Use the brand blue (#007BFF) for links and accents
- Keep the same page layout as the rest of the dashboard
- Do NOT use "use client" on page.tsx — create a client component
  for interactive elements like copy buttons and tab switchers

IMPORTANT URL NOTE:
- In all code examples, use "YOUR_DOMAIN" and "YOUR_SDK_KEY" as
  placeholders, NOT hardcoded localhost URLs
- Add a note: "Replace YOUR_DOMAIN with your EmoraTest instance URL
  and YOUR_SDK_KEY with the key from Settings → SDK"

Report all files created/modified.
Validation:
bashcd frontend && npm run build
# Open docs page in browser
# Check: all 7 sections render correctly
# Check: code blocks have proper syntax highlighting
# Check: table of contents links scroll to correct sections
# Check: copy buttons work on code blocks
# Check: no hardcoded localhost URLs
# Check: page doesn't crash or show errors

✅ Prompt 9 — Add SDK key copy button to docs + connect Settings link — DONE
READ the docs page you just built and the Settings page:
- The docs page component
- frontend/src/app/dashboard/settings/page.tsx (or wherever settings is)

Make these small improvements:

1. In the docs page, wherever it says "YOUR_SDK_KEY", add a small
   inline note: "Find your SDK key in Settings → SDK" with "Settings"
   as a clickable link to /dashboard/settings

2. Add a "Quick start" card at the very top of the docs page:
   A highlighted card that says:
   "Your SDK key: sk-xxxx...xxxx" (fetch the real key from API)
   With a copy button next to it.

   Fetch from: GET /api/v1/merchant/sdk-key (or whatever endpoint
   returns the SDK key — check the Settings page to see which
   endpoint it uses)

   If the fetch fails, show: "Your SDK key: Go to Settings to view"

3. Create the copy button as a client component:
   frontend/src/components/dashboard/CopyButton.tsx

   "use client"
   - Takes text prop
   - On click: navigator.clipboard.writeText(text)
   - Shows "Copied!" for 2 seconds, then reverts to copy icon
   - Small, inline, uses brand blue

Report files changed.
Validation:
bashcd frontend && npm run build
# Open docs page logged in
# The quick start card should show your real SDK key
# Copy button should work
# "Settings" link should navigate to settings page

Summary: Run Order
#WhatRiskTime1Fix faviconLow10 min2Audit dark mode (read only)None5 min3Fix dark mode toggleMedium20 min4Landing: hero + trust signalsLow15 min5Landing: features + testimonialsLow15 min6Landing: pricing + footerLow15 min7Landing: how it worksLow10 min8Rebuild docs pageMedium30 min9Docs SDK key + copy buttonLow15 min
Total: ~2-3 hours
Run these BEFORE the main refactoring playbook (the 38-prompt one).
These are quick wins that make the product look trustworthy immediately.