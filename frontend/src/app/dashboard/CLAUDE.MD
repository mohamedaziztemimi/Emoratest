# EmoraTest Dashboard Rules

## Auth requirement
ALL dashboard pages require authentication.
If no valid JWT → redirect to /login immediately.
Check auth in dashboard/layout.tsx — not in each page.

## Layout structure
dashboard/layout.tsx → sidebar + topbar shell
dashboard/page.tsx   → overview/home
dashboard/experiments/  → experiment list + detail
dashboard/heatmap/      → heatmap visualizer
dashboard/editor/       → no-code visual editor
dashboard/analytics/    → stats + funnel + emotion reports
dashboard/segments/     → audience segments
dashboard/integrations/ → webhook + integration settings
dashboard/settings/     → workspace settings

## Data fetching rules
- Use React Query for ALL API calls
- Base URL: process.env.NEXT_PUBLIC_API_URL
- Always send Authorization: Bearer {token} header
- Query keys: ['experiments'], ['experiment', id], ['emotion', sessionId]
- Stale time: 30 seconds for live experiment data
- Poll every 30s for active experiments: refetchInterval: 30000

## Real-time
- Emotion events: WebSocket at ws://localhost:8000/ws/emotion/{sessionId}
- Frustration alerts: WebSocket or polling every 15s
- Use useRef for WebSocket instance — not useState

## Charts and data viz
- Use Recharts for all charts
- Emotion colors must match brand:
  confusion: #F59E0B
  frustration: #EF4444
  delight: #10B981
  focus: #3B82F6
  anxiety: #F97316
  boredom: #6B7280
  hesitation: #8B5CF6
  satisfaction: #059669

## Heatmap component
- Canvas-based rendering — no external heatmap lib
- Gaussian blur radius: 25px
- Color scale: blue → green → yellow → red
- Always clean up canvas on unmount

## Loading states
- Every data-dependent component shows skeleton while loading
- Use existing Skeleton component from ui/
- Never show empty divs — always show skeleton or empty state

## Empty states
Every list/table needs an empty state component showing:
- Relevant icon
- "No X yet" message
- CTA button to create first item