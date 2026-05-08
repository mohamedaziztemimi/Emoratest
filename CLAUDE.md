# EmoraTest — Claude Code Rules

## What is this project
EmoraTest is an Emotion ML + A/B Testing SaaS platform.
Tagline: "Unlock Emotions, Win Tests"
It detects 4 behavioral states (frustrated, confused, engaged, disengaged) from mouse/scroll behavior using XGBoost with 92.7% accuracy.
DO NOT call it Conversiono anywhere — that is the old name.

## Stack
- Frontend: Next.js 14, TypeScript, Tailwind CSS — port 3000
- Backend: FastAPI (Python 3.11), PostgreSQL, Redis — port 8000
- ML: XGBoost emotion classifier (92.7% accuracy, 4 behavioral states: frustrated, confused, engaged, disengaged)
- Infra: Docker Compose (4 services: postgres, redis, backend, frontend)
- Auth: JWT httpOnly cookies, cookie name: auth_token

## Running locally
```bash
docker-compose up
```
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Test page: http://localhost:8000/static/test-page.html

After Python changes: `docker-compose restart backend`
After SDK changes: `cd sdk && npm run build && cp sdk/dist/emoratest.umd.js backend/static/sdk/emoratest.umd.js`

## Project structure
```
frontend/src/app/(landing)/       → public landing page (ALWAYS light theme)
frontend/src/app/(auth)/          → login, signup pages
frontend/src/app/dashboard/       → authenticated dashboard
frontend/src/components/          → shared components
backend/app/api/                  → FastAPI routes
backend/app/models/               → SQLAlchemy models
backend/app/services/             → business logic
backend/app/api/sdk.py            → SDK event ingestion endpoints
ml/src/                           → emotion classifier
ml/artifacts/                     → trained model files (emotion_v1.pkl)
sdk/src/                          → JavaScript tracking SDK source
sdk/dist/emoratest.umd.js         → built SDK
backend/static/sdk/               → SDK served to customers
```

## Dashboard pages (current structure)
```
/dashboard                → Overview (command center)
/dashboard/sessions       → Session list with emotion filters
/dashboard/sessions/[id]  → Session detail with emotion breakdown
/dashboard/pages          → Page Insights (pages ranked by emotional friction)
/dashboard/diagnosis      → Diagnosis (real issue detection + root causes)
/dashboard/experiments    → Experiments CRUD
/dashboard/integrations   → Integrations
/dashboard/settings       → Settings + SDK key
/dashboard/docs           → SDK documentation
```

## Sidebar groups
```
MONITOR:  Overview, Sessions
ANALYZE:  Page Insights, Diagnosis
ACT:      Experiments
CONNECT:  Integrations
ACCOUNT:  Settings
```

## Auth patterns

Dashboard uses JWT cookie auth. EVERY fetch in dashboard pages MUST use:
```typescript
fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/endpoint`, {
  credentials: "include"
})
```

SDK uses X-SDK-Key header OR sdk_key query param (for sendBeacon):
```typescript
fetch(`${apiUrl}/api/v1/sdk/events`, {
  headers: { "X-SDK-Key": sdkKey }
})
```

Backend auth helper: `get_merchant_flexible()` accepts BOTH methods.

### Critical auth rules
- NEVER use X-SDK-Key in dashboard pages — only JWT cookies
- NEVER use credentials: "include" in SDK code — only X-SDK-Key
- Base URL: `process.env.NEXT_PUBLIC_API_URL` — this is `http://localhost:8000` locally and `https://emoratest.com` in production. NO trailing /api/v1 in the env var.
- All API paths include `/api/v1/` prefix: `${NEXT_PUBLIC_API_URL}/api/v1/sessions`
- NEVER double the prefix: `/api/v1/api/v1/sessions` is WRONG
- NEVER hardcode `http://localhost:8000` or `https://emoratest.com` in code — always use the env var

## Brand colors
```
Primary blue:    #007BFF
Primary purple:  #7C3AED
```

## Behavioral State colors (use these consistently everywhere)
```
frustrated:  #EF4444 (red)    — high rage clicks, erratic movement
confused:    #F59E0B (amber)  — back-and-forth scrolling, aimless hovering
hesitating:  #EAB308 (yellow) — hovering near CTAs without clicking (frontend display state)
engaged:     #22C55E (green)  — steady movement, completing actions
disengaged:  #6B7280 (gray)   — inactivity, fast scroll past content
```

## Design system
- Dashboard background: #F5F6FA
- Cards: white, border 1px solid #E5E7EB, border-radius 12px
- Sidebar: white background, brand blue (#007BFF) for active item
- NO green in sidebar (that was old Conversiono branding)
- Auth pages: split layout (left = gradient panel, right = white form)
- Landing page: light theme, alternating white / #F8F9FF sections

## Environment variables
```
# LOCAL (.env for docker-compose.yml)
NEXT_PUBLIC_API_URL=http://localhost:8000

# PRODUCTION (.env on server for docker-compose.prod.yml)
NEXT_PUBLIC_API_URL=https://emoratest.com
```
Backend needs: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`
Never hardcode secrets — always use .env files.
Never commit .env files to git.

## Naming conventions
- React components: PascalCase
- API routes: snake_case
- DB columns: snake_case
- TypeScript interfaces: PascalCase
- Files: kebab-case for components, camelCase for utils

## Git rules
- Never commit .env files
- Never commit node_modules
- Never commit __pycache__

---

# CRITICAL RULES — ALWAYS FOLLOW

## Before writing ANY code
1. READ the relevant existing files first
2. Report what you found
3. Explain what you plan to change
4. Make surgical changes — don't rewrite working code
5. If unsure about something, ASK — don't guess

## After EVERY change
1. Report exactly which files were modified
2. Report what was changed in each file
3. Give the exact command or browser test to verify

## Next.js rules
- `"use client"` required on any component using hooks, useState, useEffect, or browser APIs
- NEVER add `"use client"` to page.tsx or layout.tsx
- metadata exports only in server components (page.tsx without "use client")
- viewport export must be separate from metadata export
- NO `document.createElement` at module level — must be inside useEffect
- NO `window` access at module level — must be inside useEffect

## API call rules
- All dashboard fetches use `credentials: "include"`
- Never use X-SDK-Key header in dashboard pages
- Base URL from `process.env.NEXT_PUBLIC_API_URL`
- All paths start with `/api/v1/`
- Never hardcode `http://localhost:8000` in frontend components

## Data integrity rules — THE MOST IMPORTANT SECTION
- NEVER show hardcoded/demo/mock data in the dashboard
- NEVER create fake data arrays in frontend components
- If an API returns empty data → show an empty state message, NOT fake data
- If a feature doesn't have a working backend → don't build the frontend for it
- If a UI element doesn't do anything when clicked → DELETE IT
- If a button has `onClick={() => {}}` (empty handler) → DELETE IT
- If a link goes to "#" → DELETE IT or make it go somewhere real
- NEVER add a notification bell, badge, or counter that isn't connected to real data
- NEVER show "coming soon" over a non-functional feature — just don't show the feature
- Every number on every dashboard card MUST come from a database query
- "No data yet" is always better than fake data

## Empty state examples (use these patterns)
```
// Good: honest empty state
"No sessions yet today. Sessions will appear once users visit your site."
"No issues detected. Your users are having a smooth experience."
"No experiments running. Create your first experiment to get started."

// Bad: hiding emptiness with fake data
const DEMO_SESSIONS = [{ id: 'fake-1', emotion: 'frustration', ... }]
```

## Backend endpoint rules
- Every endpoint must use `get_merchant_flexible()` for auth
- Every endpoint must query the real database — never return hardcoded data
- Every endpoint must handle errors: try/except with proper HTTP status codes
- Return empty arrays `[]` when no data exists — never fake data
- Return `404` when a specific resource doesn't exist
- Return `401` when auth fails

## Testing requirements
After making any change, provide:
1. The curl command to test backend endpoints
2. The browser steps to test frontend changes
3. The database query to verify data was saved
Example:
```bash
# Test the endpoint:
curl -b "auth_token=TOKEN" http://localhost:8000/api/v1/sessions
# Verify in DB:
docker-compose exec postgres psql -U postgres -d emoratest -c "SELECT COUNT(*) FROM sessions;"
```

---

# NEVER DO THESE (learned from real mistakes)

## Frontend mistakes
- Never add "use client" to page.tsx
- Never make API calls on landing page components
- Never use position:absolute for stat cards
- Never initialize isVisible as false (content disappears on landing page)
- Never use LazySection wrappers on landing page
- Never double the /api/v1 prefix in URLs
- Never use X-SDK-Key in dashboard fetch calls
- Never call `document` outside useEffect
- Never call `window` outside useEffect

## Data mistakes
- Never create hardcoded demo/mock data to make the UI look busy
- Never catch an API error and show fake data as fallback
- Never show "Analyzing..." — show "No data" or "Emotion not detected"
- Never show "No recommendations available" — either show real recs or remove the card
- Never show "User Intent: High Intent" — this is meaningless, remove it
- Never add a notification bell that doesn't connect to real notifications
- Never add a search bar that doesn't actually search

## Product mistakes
- Never call it "Session Replay" — we don't have video replay, call it "Sessions"
- Never call it "Emotion Heatmaps" — we don't have visual heatmaps, call it "Page Insights"
- Never show "Funnel Analytics" — we don't have this feature
- Never show "85-95% accuracy" — our actual accuracy is 80.1%, say "80%+"
- Never show a "Fix Now" or "EDIT_ELEMENT" button — we can't edit customer websites
- Never show fake testimonials or fake customer counts
- Never show "HIPAA Ready" — we are NOT HIPAA compliant
- Never show fake social proof numbers ("2,400+ teams", "$2.1M recovered")
- Never link to pages that don't exist (Blog, Careers, Help Center)

## Architecture mistakes
- Never break existing auth when fixing other things
- Never rename project back to "Conversiono"
- Never combine unrelated changes in one prompt
- Never rewrite a working file — make surgical edits

---

# SDK flow (how data gets from user browser to dashboard)

```
1. SDK loads on customer website
2. EmoraTest.init({ sdkKey }) → creates session via POST /api/v1/sdk/sessions
3. Event listeners capture: mouse_move, click, scroll, rage_click, exit_intent
4. Events batched and sent: POST /api/v1/sdk/events (every 5s or 50 events)
5. User closes tab → beforeunload fires → sendBeacon flushes remaining events
6. Session ends → POST /api/v1/sdk/sessions/{id}/end
7. Backend extracts features from raw events
8. XGBoost model predicts 8 emotion probabilities
9. Primary emotion + confidence saved to sessions table
10. Dashboard reads from sessions table via JWT-authenticated endpoints
```

## Sessions table key fields
```sql
id, merchant_id, visitor_id, page_url, device_type,
outcome,              -- 'unknown' → 'purchase'/'abandoned'/'signup'/etc
primary_emotion,      -- 'frustrated', 'confused', 'engaged', 'disengaged'
emotion_confidence,   -- 0.0 to 1.0
emotion_scores,       -- JSON: {"frustrated": 0.35, "engaged": 0.45, ...}
valence,              -- positive-negative axis
arousal,              -- high-low energy axis
duration_seconds,
created_at, ended_at
```

---

# PRODUCTION DEPLOYMENT

## Production server
- Server: Hetzner VPS (Ubuntu), path: `/opt/emoratest/`
- Domain: `emoratest.com` and `www.emoratest.com`
- Reverse proxy: Caddy (auto HTTPS/TLS)
- Compose file: `docker-compose.prod.yml`
- Env file: `.env` in `/opt/emoratest/`

## Production architecture
```
Internet → Caddy (HTTPS) → frontend:3000 (Next.js)
                         → backend:8000  (FastAPI) for /api/* and /static/*
```

Caddy handles:
- SSL/TLS certificates (automatic via Let's Encrypt)
- Routes /api/* and /static/* to backend
- Routes everything else to frontend
- www.emoratest.com is the primary domain

## Local → Production workflow
```bash
# 1. Develop and test locally
docker-compose up                    # uses docker-compose.yml
# test everything at http://localhost:3000

# 2. Commit and push
git add -A && git commit -m "description" && git push

# 3. Deploy on production server
ssh root@YOUR_SERVER
cd /opt/emoratest
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Critical production rules
- NEVER hardcode `localhost` in any code that runs in production
- ALWAYS use `process.env.NEXT_PUBLIC_API_URL` for API base URL
- ALWAYS use `process.env.*` for secrets and configuration
- The `.env` file on the server has production values:
  - `NEXT_PUBLIC_API_URL=https://emoratest.com`
  - `CORS_ORIGINS=["https://emoratest.com","https://www.emoratest.com"]`
- The `.env` file locally has development values:
  - `NEXT_PUBLIC_API_URL=http://localhost:8000`
- NEVER copy the production .env to local or vice versa
- NEVER commit .env files to git

## SDK URL in production
The SDK is served at: `https://emoratest.com/static/sdk/emoratest.umd.js`
Caddy routes /static/* to the backend which serves the file.
In docs and code examples, use `YOUR_DOMAIN` as placeholder — never hardcode the domain.

## Database in production
- PostgreSQL runs inside Docker, data persisted in `pgdata` volume
- To access: `docker-compose -f docker-compose.prod.yml exec postgres psql -U emoratest -d emoratest`
- NEVER delete the pgdata volume unless you want to lose all data
- Back up regularly: `docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U emoratest emoratest > backup.sql`

## Files to clean up on production server
These old files should be deleted from `/opt/emoratest/`:
- `Convorsono_Prod_Document.docx` — old name, outdated
- `Convorsono_Prod_Document.pdf` — old name, outdated
- `demo-store/` — demo directory, not needed in production
- `DOCKER_HOTFIX.md` — one-time fix doc, not needed
- `SYSTEM_DIAGNOSTIC_REPORT.md` — one-time report, not needed

## Common production issues
- If backend returns CORS errors → check `CORS_ORIGINS` in .env includes the domain
- If SSL errors → Caddy auto-renews, but check `caddy reload --config /opt/emoratest/Caddyfile`
- If frontend shows stale content → rebuild: `docker-compose -f docker-compose.prod.yml build frontend`
- If DB migrations needed → run inside backend container:
  `docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head`

---

# MAKING CHANGES PRODUCTION-SAFE

## Checklist before deploying any change
1. Does the code use `process.env.NEXT_PUBLIC_API_URL` (not hardcoded URL)?
2. Does the code use `credentials: "include"` for dashboard API calls?
3. Does the backend handle `CORS_ORIGINS` correctly?
4. Does the frontend build successfully? (`cd frontend && npm run build`)
5. Does the backend start without errors? (`docker-compose restart backend`)
6. Were any new environment variables added? → Add them to production .env too
7. Were any new database tables/columns added? → Run migration on production
8. Were any new npm/pip packages added? → They'll be installed during Docker build

## Things that break production but work locally
- Hardcoded `http://localhost:8000` → works locally, fails in production
- Missing `credentials: "include"` → works if same-origin locally, fails cross-origin
- `CORS_ORIGINS` not including the domain → browser blocks all API calls
- New env vars not added to production .env → features silently fail
- New DB columns without migration → backend crashes on query
