# EmoraTest — Legal, Pricing, Waitlist & Polish Playbook

## 16 Prompts — Run in order before launch

---

## RULES — Paste at the top of EVERY prompt:

```
RULES — Follow these strictly:
1. READ all relevant files BEFORE making any changes
2. Report what you found BEFORE writing code
3. "use client" only on components using hooks — NEVER on page.tsx or layout.tsx
4. All dashboard fetch calls use credentials: "include"
5. Never use X-SDK-Key in dashboard pages
6. Base URL: process.env.NEXT_PUBLIC_API_URL (no /api/v1 suffix in env var)
7. All API paths include /api/v1/ prefix
8. After changes, list EVERY file modified
9. Make surgical changes — don't rewrite working code
10. NEVER add hardcoded/fake data. If no data exists, show empty state.
11. NEVER use em dashes (—) anywhere in the UI. Use commas, periods, or rewrite the sentence.
12. Keep all copy short, direct, human. Avoid AI-sounding phrases.
```

---

## Prompt 1 — Cookie Consent Banner (GDPR Germany)

```
This is legally required for Germany and the EU. We track mouse
movements, clicks, and scrolls which counts as processing personal
data under GDPR. We MUST get consent before the SDK starts tracking.

READ:
- frontend/src/app/(landing)/layout.tsx
- frontend/src/app/layout.tsx
- sdk/src/ (all SDK source files)

CREATE a cookie consent banner component:
frontend/src/components/CookieConsent.tsx

"use client"

This banner appears at the bottom of EVERY page (landing + dashboard + auth)
for users who haven't consented yet.

Design:
- Fixed to bottom of viewport
- White background, subtle top border, rounded top corners
- Clean, minimal design matching the brand
- NOT a full-screen overlay. NOT annoying. Just a clean bottom bar.

Content (keep it simple and honest):
Left side text:
"We use cookies and behavioral tracking to analyze user experience.
By clicking Accept, you consent to the processing of behavioral data
(mouse movements, clicks, scrolls) as described in our Privacy Policy."

Right side buttons:
- "Accept" button (brand blue #007BFF, filled)
- "Reject" button (outlined, gray)
- "Privacy Policy" link (text link, goes to /privacy)

Behavior:
- On "Accept": set localStorage key 'emoratest_consent' = 'accepted'
  and set a cookie 'emoratest_consent=accepted; max-age=31536000; path=/'
  Then hide the banner.
- On "Reject": set localStorage key 'emoratest_consent' = 'rejected'
  and set cookie 'emoratest_consent=rejected; max-age=31536000; path=/'
  Hide the banner. SDK should NOT track.
- If already accepted/rejected (localStorage has value), don't show banner.
- Banner appears on first visit only. Decision persists for 1 year.

SDK INTEGRATION:
The SDK must check for consent before starting to track.
READ the SDK source and add this check in the init() function:

Before setting up ANY event listeners:
1. Check if cookie 'emoratest_consent' exists
2. If value is 'accepted' -> proceed with tracking normally
3. If value is 'rejected' -> do NOT set up event listeners,
   do NOT create a session, do NOT send any events.
   The SDK should be a no-op.
4. If cookie doesn't exist -> do NOT track (opt-in required in EU).
   Wait for consent.

After consent is given (user clicks Accept), the page may need to
reload or the SDK needs a method to start tracking:
Add: EmoraTest.enableTracking() — called after consent is given
This sets up the event listeners that were skipped during init().

IMPORTANT:
- The consent banner must appear on the CUSTOMER'S website too,
  not just on emoratest.com. Add a note in the docs:
  "If you operate in the EU, you must get user consent before
  EmoraTest starts tracking. The SDK respects the
  'emoratest_consent' cookie. Set it to 'accepted' after
  getting consent from your consent management tool."
- Do NOT use any third-party consent library
- Do NOT track anything before consent
- The banner text must NOT contain em dashes (—)

Report all files modified.
```

**Validation:**
```bash
cd frontend && npm run build
cd sdk && npm run build
cp sdk/dist/emoratest.umd.js backend/static/sdk/emoratest.umd.js
# Open landing page in incognito:
# 1. Consent banner should appear at bottom
# 2. Click "Reject" -> banner disappears, no tracking
# 3. Open new incognito -> click "Accept" -> banner disappears
# 4. Refresh -> banner should NOT reappear
# 5. Open test page with SDK -> check browser console Network tab:
#    If consent rejected: ZERO requests to /api/v1/sdk/*
#    If consent accepted: normal tracking requests appear
```

---

## Prompt 2 — Create Legal Pages (Impressum + Privacy Policy + Terms)

```
Germany REQUIRES an Impressum (legal disclosure) on every commercial website.
GDPR requires a Privacy Policy. We also need Terms of Service.

CREATE these three pages:

1. frontend/src/app/(landing)/impressum/page.tsx

Content (replace the placeholders with real info):
Title: "Impressum"

"Angaben gemäß § 5 TMG

[Your Full Legal Name]
[Your Street Address]
[Your City, Postal Code]
Germany

Kontakt:
E-Mail: hello@emoratest.com
[Phone number if you have one — required if you have one]

Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV:
[Your Full Name]
[Your Address]

EU-Streitschlichtung:
Die Europäische Kommission stellt eine Plattform zur
Online-Streitbeilegung (OS) bereit:
https://ec.europa.eu/consumers/odr

Haftungsausschluss:
Trotz sorgfältiger inhaltlicher Kontrolle übernehmen wir keine
Haftung für die Inhalte externer Links. Für den Inhalt der
verlinkten Seiten sind ausschließlich deren Betreiber verantwortlich."

NOTE: Add a comment at the top of the file:
// TODO: Replace placeholder values with real legal information
// This is required by German law (TMG § 5)

2. frontend/src/app/(landing)/privacy/page.tsx

Title: "Privacy Policy"
Last updated: [current date]

Section 1 — Who we are:
"EmoraTest is operated by [Your Name/Company], [Address], Germany.
Contact: hello@emoratest.com"

Section 2 — What data we collect:
"When you use our dashboard:
We collect your email address and account information to provide
our service. We store this data on servers in [Germany/EU].

When our SDK is installed on a website:
We collect anonymous behavioral data from website visitors:
mouse movements, clicks, scroll patterns, and page URLs.
We do NOT collect: names, email addresses, IP addresses (hashed
immediately), keystrokes, form inputs, screenshots, or camera/
microphone data.

All behavioral data is processed to detect emotional patterns
(frustration, confusion, satisfaction, etc.) using machine learning.
No individual identification is possible from this data."

Section 3 — Legal basis (GDPR Article 6):
"For dashboard users: Contract performance (Art. 6(1)(b) GDPR)
For website visitors tracked by SDK: Consent (Art. 6(1)(a) GDPR).
Website operators using EmoraTest must obtain visitor consent
before the SDK begins tracking."

Section 4 — Data retention:
"Session data is retained for 90 days, then automatically deleted.
Account data is retained until you delete your account."

Section 5 — Your rights:
"Under GDPR, you have the right to:
access your data, correct your data, delete your data,
restrict processing, data portability, and object to processing.
To exercise these rights, contact hello@emoratest.com"

Section 6 — Data processing location:
"All data is processed and stored on servers within the European
Union (Hetzner, Germany)."

Section 7 — Cookies:
"EmoraTest uses essential cookies for authentication (session
management). Our tracking SDK uses a consent cookie
(emoratest_consent) to remember your tracking preference.
We do not use advertising or third-party tracking cookies."

Section 8 — Changes:
"We may update this policy. The latest version is always
available at this URL."

3. frontend/src/app/(landing)/terms/page.tsx

Title: "Terms of Service"
Last updated: [current date]

Keep it short and clear:

Section 1 — Service:
"EmoraTest provides emotion detection and A/B testing tools
for websites. The service is currently in beta."

Section 2 — Beta disclaimer:
"EmoraTest is currently in beta. The service is provided as-is
without warranty. Features may change, and we cannot guarantee
uptime during the beta period."

Section 3 — Your responsibilities:
"You are responsible for obtaining proper consent from your
website visitors before using EmoraTest's tracking SDK,
especially if your visitors are in the EU/EEA.
You must display a cookie/tracking consent notice."

Section 4 — Data:
"You retain ownership of your data. We process it solely
to provide the service. See our Privacy Policy for details."

Section 5 — Acceptable use:
"Do not use EmoraTest to track users without consent,
on websites containing illegal content, or in ways that
violate applicable laws."

Section 6 — Termination:
"You can delete your account at any time. We can suspend
accounts that violate these terms."

Section 7 — Liability:
"To the maximum extent permitted by law, our liability is
limited to the amount you paid us in the last 12 months."

Section 8 — Governing law:
"These terms are governed by German law. Place of jurisdiction
is [Your City], Germany."

DESIGN for all three pages:
- Same layout as landing page (navbar + footer)
- Clean, readable text layout
- Max width 700px, centered
- Good typography, line-height 1.8
- Section headings in brand blue
- No em dashes (—) anywhere

IMPORTANT:
- These are NOT inside the dashboard. They are public pages
  accessible without login.
- Add these to the footer links:
  Privacy Policy -> /privacy
  Terms of Service -> /terms
  Impressum -> /impressum
- The pages must have proper metadata for SEO

Report all files created and footer changes.
```

**Validation:**
```bash
cd frontend && npm run build
# Open /privacy, /terms, /impressum — all should load
# Footer links should work
# No em dashes anywhere on these pages
```

---

## Prompt 3 — Favicon: Use logo2 file

```
READ:
- Find the logo2 file: find frontend/ -name "logo2*" -o -name "Logo2*"
- Also check: find frontend/public -name "logo*"
- Also check: find frontend/src -name "logo*"
- ls frontend/public/

Report: where is the logo2 file and what format/size is it?

Now use this logo2 file as the favicon:

1. If logo2 is an SVG:
   - Copy it to frontend/src/app/icon.svg
   - Make sure the viewBox is at least 48x48
   - If the SVG is too small/complex, create a simplified version
     that looks clear at 32x32 pixels

2. If logo2 is a PNG/JPG:
   - Copy it to frontend/public/favicon.png
   - Create frontend/src/app/icon.tsx that renders it at 48x48:

   import { ImageResponse } from 'next/og'

   export const size = { width: 48, height: 48 }
   export const contentType = 'image/png'

   export default function Icon() {
     return new ImageResponse(
       (<img src="/favicon.png" width="48" height="48" />),
       { ...size }
     )
   }

   If ImageResponse can't load local images, use a different approach:
   just copy the logo2 file directly as:
   frontend/src/app/favicon.ico (if ICO format)
   or frontend/public/favicon.png and reference in metadata

3. Also create apple-touch-icon (180x180) from the same logo

4. Update metadata in frontend/src/app/layout.tsx:
   metadata.icons = {
     icon: '/favicon.png', // or whatever the file is
     apple: '/apple-icon.png',
   }

5. Delete any old favicon files that are no longer referenced

The logo should be CLEARLY visible in the browser tab.
Not tiny, not blurry.

Report files modified.
```

**Validation:**
```bash
cd frontend && npm run build
# Open browser — tab should show the logo2 icon, clear and visible
# Check on multiple pages (landing, dashboard, auth)
```

---

## Prompt 4 — Session Limits: Add to database and enforce

```
READ:
- backend/app/models/ — find the merchant/user model
- backend/app/api/sdk.py — where sessions are created
- backend/app/api/auth.py — where accounts are created

We need to limit how many sessions each account can have per month.

BACKEND CHANGES:

1. Add fields to the merchant/user model:
   plan = Column(String, default='free')           # 'free', 'growth', 'enterprise'
   monthly_session_limit = Column(Integer, default=500)  # free plan default
   sessions_this_month = Column(Integer, default=0)
   session_month = Column(Integer)                 # current month (1-12) for reset
   session_year = Column(Integer)                  # current year for reset

2. When creating a new account (signup endpoint):
   Set plan = 'free'
   Set monthly_session_limit = 500
   Set sessions_this_month = 0
   Set session_month = current month
   Set session_year = current year

3. When creating a new session (SDK session creation endpoint):
   BEFORE creating the session:
   a. Check if session_month/year matches current month/year
      If not -> reset sessions_this_month to 0, update month/year
   b. Check if sessions_this_month >= monthly_session_limit
      If yes -> return 429 Too Many Requests with body:
      { "error": "session_limit_reached",
        "message": "Monthly session limit reached",
        "limit": 500,
        "used": 500 }
      The SDK should handle this gracefully (stop tracking, no crash)
   c. If under limit -> create session, increment sessions_this_month

4. Create an endpoint to check usage:
   GET /api/v1/account/usage
   Returns:
   {
     "plan": "free",
     "sessions_used": 342,
     "sessions_limit": 500,
     "reset_date": "2025-06-01"  // first of next month
   }

5. Run the migration to add these columns.

SDK CHANGES:
In the SDK, handle 429 responses from session creation:
- If 429 received -> log a console.warn("EmoraTest: Session limit reached")
- Do NOT crash, do NOT retry
- Stop all tracking for this page load
- EmoraTest.isInitialized() should return false

Report all files modified.
```

**Validation:**
```bash
docker-compose restart backend
# Check the migration ran:
docker-compose exec postgres psql -U postgres -d emoratest -c \
  "SELECT plan, monthly_session_limit, sessions_this_month FROM merchants LIMIT 5;"

# Test usage endpoint:
curl -b "auth_token=YOUR_TOKEN" http://localhost:8000/api/v1/account/usage

# Test session limit by temporarily setting limit to 1:
docker-compose exec postgres psql -U postgres -d emoratest -c \
  "UPDATE merchants SET monthly_session_limit = 1, sessions_this_month = 1;"
# Open test page -> SDK should get 429, console shows warning
# Reset: UPDATE merchants SET monthly_session_limit = 500, sessions_this_month = 0;
```

---

## Prompt 5 — Show usage in dashboard Settings page

```
READ the Settings page:
- frontend/src/app/dashboard/settings/page.tsx
- All components it imports

ADD a "Usage" section to the Settings page (above the SDK key section):

Fetch from: GET /api/v1/account/usage

Display:
- Plan name: "Free Beta" with a badge
- Session usage bar:
  "342 / 500 sessions this month"
  with a visual progress bar (brand blue fill)
  If > 80% used, bar turns amber
  If = 100%, bar turns red with text "Limit reached"
- Reset date: "Resets on June 1, 2025"
- "Need more sessions?" link -> opens upgrade/waitlist modal

IMPORTANT:
- credentials: "include" on fetch
- Loading skeleton while fetching
- If API fails, show "Unable to load usage data"

Report files modified.
```

**Validation:**
```bash
cd frontend && npm run build
# Open Settings page -> usage section shows real numbers
# Progress bar matches the actual session count
```

---

## Prompt 6 — Waitlist instead of payment

```
We are NOT accepting payments yet. This is a beta.
When users want to upgrade, we add them to a waiting list.

BACKEND:

1. Create model: backend/app/models/waitlist.py

   class WaitlistEntry(Base):
       __tablename__ = "waitlist"
       id = Column(UUID, primary_key=True, default=uuid4)
       email = Column(String, nullable=False)
       company_name = Column(String, nullable=True)
       plan_interest = Column(String, default='growth')  # which plan they want
       current_sessions_monthly = Column(Integer, nullable=True)  # how many they need
       message = Column(Text, nullable=True)
       created_at = Column(DateTime, default=func.now())
       status = Column(String, default='pending')  # pending, contacted, converted

2. Create endpoints: backend/app/api/waitlist.py

   POST /api/v1/waitlist
   Body: { email, company_name?, plan_interest?, current_sessions_monthly?, message? }
   No auth required (public endpoint, but rate-limited)
   Returns: { "success": true, "message": "You're on the list!" }
   Prevent duplicates: if email already exists, return success
   (don't reveal that they're already on the list)

   GET /api/v1/admin/waitlist (protected, admin only)
   Returns all waitlist entries sorted by created_at DESC
   (We'll use this later to manage the list)

3. Run migration to create the table.

FRONTEND:

4. Create a waitlist modal component:
   frontend/src/components/WaitlistModal.tsx

   "use client"

   Modal with:
   - Title: "Join the waiting list"
   - Subtitle: "We're in beta and opening paid plans soon.
     Leave your details and we'll reach out when ready."
   - Form fields:
     Email (required, pre-fill from logged-in user if available)
     Company name (optional)
     Plan interested in (dropdown: Growth, Enterprise)
     Message (optional textarea, placeholder: "Tell us about your needs")
   - "Join waitlist" button
   - On success: show "You're on the list! We'll be in touch."
     with a checkmark animation
   - On error: show error message

5. Replace ALL "upgrade", "buy", "subscribe", or pricing CTAs:

   In the Settings page "Need more sessions?" link:
   -> opens the waitlist modal

   In the landing page pricing section:
   - Free plan button: "Start Free" -> links to /signup
   - Growth plan button: change from "Start Free Trial" to
     "Join Waiting List" -> opens waitlist modal (or goes to
     /waitlist page if not logged in)
   - Enterprise plan button: change from "Book a Demo" to
     "Join Waiting List" -> same

   In the landing page hero CTA:
   - Keep "Start Free" -> links to /signup

6. If there's any Stripe, payment, or billing code -> DELETE IT.
   We are not processing payments.
   Search: grep -r "stripe\|Stripe\|payment\|billing\|subscribe\|checkout" frontend/src/ --include="*.tsx" --include="*.ts"
   Delete anything found.

Report all files modified.
```

**Validation:**
```bash
docker-compose restart backend
cd frontend && npm run build

# Test waitlist submission:
curl -X POST -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","company_name":"TestCo","plan_interest":"growth"}' \
  http://localhost:8000/api/v1/waitlist
# Should return success

# Check DB:
docker-compose exec postgres psql -U postgres -d emoratest -c \
  "SELECT email, plan_interest, created_at FROM waitlist;"

# Open landing page -> pricing -> "Join Waiting List" button
# should open modal or work as expected
# No "Start Free Trial" or "Book a Demo" buttons anymore
```

---

## Prompt 7 — Fix pricing section content

```
READ the landing page pricing section.

Replace the current pricing with this EXACT content:

PLAN 1: FREE
Title: "Free"
Subtitle: "Get started with emotion tracking"
Price: "$0 / month"
Features:
- Up to 500 sessions per month
- 1 active experiment
- Basic emotion detection (8 emotions)
- Session explorer with filters
- Email support
Button: "Start Free" -> links to /signup
Badge: none

PLAN 2: GROWTH
Title: "Growth"
Badge: "Coming Soon" (small, blue)
Subtitle: "For teams serious about conversion"
Price: "$29 / month"
Features:
- Up to 10,000 sessions per month
- Unlimited experiments
- Full emotion detection
- Automatic diagnosis
- Emotion alerts (email)
- Page insights
- Priority support
Button: "Join Waiting List" -> opens waitlist modal
Note under button: "We're in beta. Join the list for early access."

PLAN 3: SCALE
Title: "Scale"
Badge: "Coming Soon" (small, blue)  
Subtitle: "For growing companies"
Price: "$79 / month"
Features:
- Up to 50,000 sessions per month
- Everything in Growth
- Slack integration
- Data export (CSV)
- Team members (up to 5)
- Dedicated support
Button: "Join Waiting List" -> opens waitlist modal

REMOVE:
- The old Enterprise plan entirely (not needed for beta)
- "HIPAA Ready" badge
- "99.9% Uptime SLA" badge
- Keep only "GDPR Compliant" badge
- The "All plans include a 14-day free trial" line ->
  change to "Free plan available now. Paid plans coming soon."

IMPORTANT:
- No em dashes (—) anywhere
- Feature list should use checkmarks, not bullet points
- Prices should feel reasonable for a beta product
- $29 is the entry point, not $79

Report all text changes made.
```

**Validation:**
```bash
cd frontend && npm run build
# Open landing page -> pricing section:
# Free plan: $0, 500 sessions
# Growth: $29, "Coming Soon" badge, "Join Waiting List" button
# Scale: $79, "Coming Soon" badge
# No Enterprise plan
# No HIPAA badge
# No em dashes
```

---

## Prompt 8 — Remove ALL em dashes from landing page

```
READ the entire landing page:
- frontend/src/app/(landing)/page.tsx
- Every component imported by the landing page

Search for em dashes:
grep -n "—" frontend/src/app/\(landing\)/page.tsx
grep -rn "—" frontend/src/components/ --include="*.tsx"

Also search for the HTML entity:
grep -rn "&mdash;\|&#8212;" frontend/src/ --include="*.tsx"

For EVERY em dash found, replace it with a period, comma,
or rewrite the sentence to not need it.

Examples of what to fix:
BAD:  "Complete emotion intelligence platform — see what users feel"
GOOD: "Complete emotion intelligence platform. See what users feel."

BAD:  "Insights in hours. Revenue lift in days — guaranteed."
GOOD: "Insights in hours. Revenue lift in days."

BAD:  "From confusion to conversion — in 4 steps"
GOOD: "From confusion to conversion in 4 steps"

BAD:  "No credit card — cancel anytime"
GOOD: "No credit card. Cancel anytime."

Replace EVERY instance. No em dashes should remain on the landing page
or in any component used by the landing page.

Also check the dashboard pages for em dashes:
grep -rn "—" frontend/src/app/dashboard/ --include="*.tsx"
Fix those too.

Report every replacement made.
```

**Validation:**
```bash
grep -rn "—" frontend/src/ --include="*.tsx" --include="*.ts"
# Should return ZERO results
# If any remain, they were missed — fix them
```

---

## Prompt 9 — Remove AI-sounding copy from landing page

```
READ the entire landing page and fix copy that sounds AI-generated.

AI-generated copy patterns to fix:
- Buzzword stacking: "Unlock emotions, win tests" (keep as tagline but
  make sure body copy doesn't stack buzzwords)
- Vague superlatives: "Complete", "Full-featured", "Deep insights"
- False urgency: "Start winning today", "Don't miss out"
- Generic SaaS phrases: "Everything you need", "Scale as you grow"

Go through the ENTIRE landing page and fix these specific patterns:

1. "Everything You Need to Win" (features section title)
   -> "What you get"

2. "Complete emotion intelligence platform"
   -> "Track emotions. Find problems. Fix them."

3. Any instance of "powerful" -> remove or replace with specific claim

4. Any instance of "seamlessly" -> remove

5. Any instance of "cutting-edge" or "state-of-the-art" -> remove

6. "Simple, Transparent Pricing" -> "Pricing"

7. "Questions We Get Asked Every Day" -> "FAQ"

8. "Ready to See What Your Users Actually Feel?" (CTA section)
   -> "Start tracking emotions for free"

9. "Join X growth teams who stopped guessing" -> remove fake numbers,
   change to "Stop guessing why users leave"

10. "Get Weekly Emotion Insights" (newsletter section)
    If no newsletter exists -> DELETE the entire newsletter section.
    A signup form that goes nowhere is fake UI.

11. Any remaining "growth teams" count -> remove the number

12. Review EVERY heading and subtitle. If it sounds like ChatGPT
    wrote it, rewrite it to be direct and human.

The tone should be: a smart friend explaining their product.
Not: a marketing template.

Report every text change.
```

**Validation:**
```bash
cd frontend && npm run build
# Read through the entire landing page out loud
# If any sentence sounds like it came from a "SaaS landing page generator"
# -> it needs rewriting
```

---

## Prompt 10 — Add "Beta" badge to the product

```
READ:
- The landing page navbar
- The dashboard sidebar (logo area)
- The landing page hero section

Add a small "Beta" badge next to the EmoraTest logo in THREE places:

1. Landing page navbar: next to "EmoraTest" text
   Small badge: "Beta" in a rounded pill
   Style: background #E0E7FF, color #3730A3, font-size 10px,
   padding 2px 8px, border-radius 10px, font-weight 500

2. Dashboard sidebar: next to "EmoraTest" text in the logo area
   Same badge style as above

3. Landing page hero: add under the main headline
   "Currently in free beta. No credit card required."

Being transparent about beta status builds trust.
People know what to expect and are more forgiving of rough edges.

Report files modified.
```

**Validation:**
```bash
cd frontend && npm run build
# Landing page: "EmoraTest Beta" badge visible in navbar
# Dashboard: "EmoraTest Beta" badge visible in sidebar
# Hero section: beta mention visible
```

---

## Prompt 11 — Fix the footer links

```
READ the landing page footer.

The footer should ONLY link to pages that actually exist.

KEEP these links:
- Privacy Policy -> /privacy
- Terms of Service -> /terms
- Impressum -> /impressum (required by German law)
- Documentation -> /dashboard/docs (or wherever docs live)

REMOVE these links (pages don't exist):
- Blog (no blog exists)
- Careers (not hiring)
- Help Center (no help center)
- About (no about page)
- Any social media links UNLESS you actually have those accounts

If you have real social media accounts, keep those links.
If the social links go to "#" or non-existent profiles -> REMOVE them.

Change footer text from anything with fake numbers to:
"EmoraTest. Emotion tracking for websites."

Add: "Made in Germany" (builds trust, reflects data processing location)

Report all changes.
```

**Validation:**
```bash
cd frontend && npm run build
# Click every footer link -> each should go to a real page
# No dead links, no 404s
```

---

## Prompt 12 — SDK consent integration for customer websites

```
READ the SDK source code and the docs page.

Add a section to the docs page about GDPR consent integration:

Title: "GDPR Consent (Required for EU)"

Content:

"If your website serves users in the EU, you must get consent
before EmoraTest starts tracking. The SDK checks for a consent
cookie before collecting any data.

Option 1: Use our built-in consent check

The SDK automatically looks for a cookie named 'emoratest_consent'.
If the value is 'accepted', tracking starts. If 'rejected' or
missing, no data is collected.

Set this cookie from your consent banner:

```javascript
// When user accepts tracking in your consent banner
document.cookie = 'emoratest_consent=accepted; max-age=31536000; path=/';

// Optionally, start tracking immediately without page reload
if (window.EmoraTest) {
  window.EmoraTest.enableTracking();
}
```

Option 2: Integrate with your existing consent tool

If you use a consent management platform (Cookiebot, OneTrust,
Usercentrics, etc.), load the EmoraTest SDK only after consent
is granted:

```javascript
// Example with a generic consent callback
onConsentGranted('analytics', function() {
  const script = document.createElement('script');
  script.src = 'https://YOUR_DOMAIN/static/sdk/emoratest.umd.js';
  script.onload = function() {
    EmoraTest.init({ sdkKey: 'YOUR_SDK_KEY' });
  };
  document.body.appendChild(script);
});
```

What data we collect:
Mouse movements, clicks, scroll patterns, and page URLs.
We do NOT collect: names, emails, IP addresses, keystrokes,
form inputs, screenshots, or passwords."

IMPORTANT:
- No em dashes in the docs
- Use YOUR_DOMAIN and YOUR_SDK_KEY placeholders
- Place this section after "What Gets Tracked" and before "Tracking Conversions"

Report files modified.
```

**Validation:**
```bash
cd frontend && npm run build
# Open docs page -> GDPR section should be visible
# Code examples should be correct
# No hardcoded domains
```

---

## Prompt 13 — Dashboard: show session limit warning

```
READ the dashboard overview page.

Add a session limit warning banner that appears when the user is
close to or has hit their monthly session limit.

Fetch from: GET /api/v1/account/usage (already created in Prompt 4)

Logic:
- If sessions_used >= sessions_limit (100%):
  Show a RED banner at the top of the overview:
  "You've reached your monthly session limit (500 sessions).
  New sessions are not being tracked. Join our waiting list
  for higher limits."
  Button: "Join Waiting List" -> opens waitlist modal

- If sessions_used >= 80% of sessions_limit:
  Show an AMBER banner:
  "You've used 423 of 500 sessions this month.
  Need more? Join our waiting list."
  Button: "Join Waiting List" -> opens waitlist modal

- If under 80%: no banner

The banner should be dismissible (X button) but reappear on next visit
if the condition is still true.

IMPORTANT:
- credentials: "include" on fetch
- No em dashes in the text
- Banner appears above the stat cards

Report files modified.
```

**Validation:**
```bash
cd frontend && npm run build
# Set sessions close to limit:
docker-compose exec postgres psql -U postgres -d emoratest -c \
  "UPDATE merchants SET sessions_this_month = 450, monthly_session_limit = 500;"
docker-compose restart backend
# Open dashboard -> amber warning should appear
# Set to limit:
docker-compose exec postgres psql -U postgres -d emoratest -c \
  "UPDATE merchants SET sessions_this_month = 500;"
# Refresh -> red warning should appear
# Reset: UPDATE merchants SET sessions_this_month = 0;
```

---

## Prompt 14 — Signup flow: set proper defaults

```
READ:
- Backend signup endpoint
- Frontend signup page

When a new account is created, ensure these defaults are set:

1. plan = 'free'
2. monthly_session_limit = 500
3. sessions_this_month = 0
4. session_month = current month
5. session_year = current year

Also update the welcome/onboarding page after signup:

- Show: "Welcome to EmoraTest (Free Beta)"
- Show the SDK key with copy button
- Show: "Your free plan includes 500 sessions per month"
- Show a quick start checklist:
  1. Copy your SDK key
  2. Add the tracking script to your website
  3. Visit your site to generate your first session
  4. Check back here to see emotion data

Remove any mention of "trial" or "upgrade" from the welcome page.
This is a free beta, not a trial.

Report files modified.
```

**Validation:**
```bash
# Create a new account (in incognito)
# Check the DB:
docker-compose exec postgres psql -U postgres -d emoratest -c \
  "SELECT email, plan, monthly_session_limit FROM merchants ORDER BY created_at DESC LIMIT 1;"
# Should show: plan=free, monthly_session_limit=500
# Welcome page should show beta messaging, not trial
```

---

## Prompt 15 — Final landing page polish

```
READ the entire landing page one more time.

Check for and fix these final issues:

1. HERO SECTION:
   - Primary CTA should be: "Start Free" (links to /signup)
   - Secondary should be: "View Documentation" (links to docs)
   - No fake numbers, no fake live ticker
   - "Currently in free beta" should be visible

2. FEATURES SECTION:
   - 6 feature cards max
   - Each title under 4 words
   - Each description under 20 words
   - No buzzwords: "powerful", "seamless", "cutting-edge"

3. HOW IT WORKS:
   - 4 steps, each under 15 words description
   - Step badges should be factual, not promotional

4. PRICING:
   - 3 plans: Free ($0), Growth ($29, coming soon), Scale ($79, coming soon)
   - Paid plans have "Join Waiting List" buttons
   - "GDPR Compliant" badge only (no HIPAA, no SLA)

5. FAQ:
   - Check that ALL FAQ answers are accurate
   - No claims about features that don't exist
   - No fake customer numbers
   - If FAQ has "How is EmoraTest different from Hotjar?" ->
     make sure the answer is honest and doesn't overclaim

6. CTA SECTION (bottom):
   - "Start tracking emotions for free"
   - Button: "Create Free Account"
   - No fake urgency

7. OVERALL:
   - No em dashes (—) ANYWHERE
   - No fake numbers ANYWHERE
   - No dead links ANYWHERE
   - Professional but honest tone
   - Mobile responsive (check on narrow viewport)

Report every fix made.
```

**Validation:**
```bash
cd frontend && npm run build
# Full review of landing page:
grep -n "—" frontend/src/app/\(landing\)/ -r --include="*.tsx"
# Zero results

# Check for fake numbers:
grep -n "2,400\|847\|2.1M\|10,000+" frontend/src/app/\(landing\)/ -r --include="*.tsx"
# Zero results

# Click every link on the page -> none should 404
# Resize browser to mobile width -> everything should be readable
```

---

## Prompt 16 — Add "Made with care in Germany" to footer

```
READ the landing page footer.

Add at the very bottom, after all links:

A small line:
"Made with care in Germany"
Font size 12px, color gray-400, centered

This is a trust signal. German engineering, German data hosting,
GDPR compliance. It matters for EU customers.

Also verify:
- Footer has: Privacy Policy, Terms, Impressum, Docs links
- Footer does NOT have dead links
- Copyright year is current: "2025 EmoraTest"

Report files modified.
```

---

## Summary: Run order

| # | What | Time |
|---|------|------|
| 1 | Cookie consent banner + SDK consent check | 30 min |
| 2 | Legal pages (Impressum, Privacy, Terms) | 20 min |
| 3 | Favicon with logo2 | 10 min |
| 4 | Session limits backend | 25 min |
| 5 | Usage display in Settings | 15 min |
| 6 | Waitlist system (backend + frontend) | 30 min |
| 7 | Fix pricing section | 15 min |
| 8 | Remove all em dashes | 10 min |
| 9 | Fix AI-sounding copy | 15 min |
| 10 | Add Beta badge | 10 min |
| 11 | Fix footer links | 10 min |
| 12 | GDPR section in docs | 15 min |
| 13 | Session limit warning in dashboard | 15 min |
| 14 | Signup defaults | 15 min |
| 15 | Final landing page polish | 20 min |
| 16 | Footer "Made in Germany" | 5 min |

**Total: ~4-5 hours**

Run these AFTER the "Make It Real" playbook (the 52-prompt one).
These are the final touches that make it launchable.