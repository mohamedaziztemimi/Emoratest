# Dashboard Fixes Prompt for AI Agent

Copy and paste everything below this line to your AI coding agent:

---

## Task: Fix EmoraTest Dashboard — Show Real Data Only, Fix Tracking, Improve Design

The EmoraTest dashboard currently has major issues: it shows fake/hardcoded data, doesn't track pages or session duration properly, and has design issues. Fix everything below, test, and push.

---

### 1. CRITICAL: Remove ALL Fake/Hardcoded Data

The Overview page currently shows hardcoded numbers like:
- Emotion Score: 72
- Sessions Today: 1,247
- Frustration Alerts: 3
- Active Experiments: 2
- "Users rage-clicking on Unknown — 73% of users affected"

**ALL of this is fake.** Remove every hardcoded value. Every number on the dashboard must come from real database queries. If there's no data, show "0" or "No data yet" — never fake numbers.

Check every dashboard page (Overview, Sessions, Page Insights, Diagnosis, Experiments) and remove any hardcoded/demo data. The demo data is misleading and makes the product look broken when a real user sees fake sessions they didn't generate.

The only exception: keep a "View Demo" button on the Diagnosis page that explicitly shows sample data when clicked (clearly labeled as demo data).

---

### 2. Fix Page URL Tracking — No More "unknown"

Currently all sessions show page as "unknown". The SDK must track which page the user is visiting.

**Backend fix:**
- The `sessions` table and `emotion_events` table must store the page URL (or path)
- When receiving events from the SDK, extract and store the page URL from the event data
- If the SDK sends a `page_url` or `url` field, store it. If not, check the `Referer` header

**Frontend SDK fix (if applicable):**
- The JavaScript SDK snippet that runs on customer websites must send `window.location.pathname` or `window.location.href` with every event batch
- Add `page_url` to the event payload sent to `/api/v1/events/batch`

**Dashboard fix:**
- Sessions page: show the actual page path instead of "unknown"
- Page Insights: group and display sessions by actual page URL
- Overview "Pages needing attention": show real page URLs

---

### 3. Track Session Duration

Sessions currently show duration as "." or "--" or "0s".

**Fix:**
- Track session start time (first event received) and session end time (last event received)
- Calculate duration = end_time - start_time
- Store duration in the sessions table (or calculate on the fly)
- Display duration in human-readable format: "2m 34s", "45s", "12m 5s"
- Show duration in: Sessions list, Page Insights (avg duration), Overview

---

### 4. Track Visitor IP Address

The Sessions page should show the visitor's IP address (or at least country/region).

**Backend fix:**
- When receiving events at `/api/v1/events/batch`, extract the visitor's IP from:
  - `X-Forwarded-For` header (since we're behind Cloudflare/Caddy)
  - `CF-Connecting-IP` header (Cloudflare provides this)
  - Fall back to the request's remote address
- Store the IP in the sessions table
- Optionally: do a simple GeoIP lookup to store country/city (use a free GeoIP database or Cloudflare's `CF-IPCountry` header)

**Dashboard fix:**
- Sessions page: show IP address (or country flag + country name) in the VISITOR column
- Keep the anonymous visitor ID (b37687f5...) but add the IP/location next to it

**Privacy note:** Add a note in the privacy policy that IP addresses are collected. Since we're GDPR compliant, store IPs in hashed/anonymized form or provide an option to disable IP tracking.

---

### 5. Fix the Diagnosis Page — Real Data Only

The Diagnosis page currently shows hardcoded fake data:
- "Users are clicking furiously on broken elements" — FAKE
- "23% of users affected on Checkout" — FAKE
- "Estimated impact: ~$1,200/week" — FAKE
- Rage clicks 23%, Hesitation 45%, Drop off 38% — ALL FAKE

**Fix:**
- Query real session data to generate diagnoses
- Only show diagnosis cards when there's enough real data to make a meaningful analysis
- Diagnosis logic should be:
  - If frustration rate > 50% on a page → "High frustration detected on [page]"
  - If rage click count is high → "Users are rage-clicking on [page]"
  - If bounce rate is high on a page → "High bounce rate on [page]"
  - If sessions have very short duration → "Users are leaving [page] quickly"
- If there's not enough data, show: "Not enough data yet. We need at least 50 sessions to generate meaningful diagnoses."
- Remove the fake "Estimated impact: ~$1,200/week" — don't show revenue estimates unless the user has configured their average order value
- Keep the "View Demo" button that shows example diagnosis data (clearly labeled)

---

### 6. Make the Search Bar Work

The search bar at the top of every dashboard page currently does nothing.

**Fix:**
- Implement global search across the dashboard
- Search should filter/find:
  - Sessions by visitor ID, page URL, emotion type
  - Pages by URL
  - Experiments by name
- Show search results in a dropdown below the search bar
- Clicking a result navigates to the relevant page/item
- If no results, show "No results found"

---

### 7. Allow Users to Delete Sessions

**Fix:**
- Add a delete button (trash icon) on each session row in the Sessions page
- Add a "Select All" checkbox to bulk delete sessions
- Show a confirmation dialog: "Are you sure you want to delete X session(s)? This action cannot be undone."
- Backend: add a DELETE endpoint `/api/v1/sessions/{session_id}` and `/api/v1/sessions/bulk-delete`
- Only allow the merchant who owns the session to delete it
- Also delete related emotion_events when a session is deleted

---

### 8. Design Improvements — Simple & Premium SaaS Look

The current dashboard design needs to look more professional and clean. Apply these design principles:

**General:**
- Clean white background, subtle gray borders
- Consistent spacing and padding (use 16px/24px grid)
- Remove unnecessary visual clutter
- Use a professional font (Inter or the current font, but ensure consistent sizing)
- Cards should have subtle shadows (box-shadow: 0 1px 3px rgba(0,0,0,0.1))
- Use a restrained color palette: primary blue for actions, red for frustration, orange for confusion, green for delight/satisfaction

**Overview page:**
- Stat cards should be clean with just the number and label — no unnecessary decorative elements
- "Pages needing attention" and "Sessions needing attention" should be clean tables
- Emotion Trends chart should be properly sized and labeled

**Sessions page:**
- Clean table with proper column widths
- Emotion labels should use small colored dots + text (like they already do — keep this)
- Add pagination (don't load all sessions at once)
- Filters should be compact and inline

**Page Insights:**
- Clean table showing page URL, session count, dominant emotion, avg duration
- Add a simple bar chart or sparkline showing emotion distribution per page

**Diagnosis page:**
- Clean cards with clear hierarchy: issue title → affected metric → recommendation
- Use severity badges: HIGH (red), MEDIUM (orange), LOW (yellow)
- Each diagnosis should have a clear "What to do" section

---

### 9. Verification Checklist Before Pushing

1. Overview page shows ONLY real data from the database — zero hardcoded values
2. All sessions show actual page URLs, not "unknown"
3. Session duration is tracked and displayed correctly
4. Visitor IP/location is tracked and shown
5. Diagnosis page shows real analysis based on actual data
6. Search bar works across all dashboard pages
7. Users can delete individual and bulk sessions
8. Design is clean, consistent, and professional
9. No console errors in the browser
10. `npm run build` passes without errors
11. All API endpoints return correct data

After fixing, test locally, then commit and push to the server.