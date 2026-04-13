# EmoraTest Frontend Rules

## Framework rules
- Next.js 14 App Router — not Pages Router
- Server components by default
- Add "use client" ONLY when component uses:
  hooks, useState, useEffect, useRef, event handlers,
  browser APIs (window/document/localStorage/canvas)
- NEVER add "use client" to page.tsx or layout.tsx files
- metadata export only in server components
- viewport export separate from metadata:
  export const viewport = { themeColor: '#007BFF' }

## Component rules
- All reusable UI in frontend/src/components/ui/
- All named exports — no default exports except pages
- Export everything from components/ui/index.ts
- Every component must work in both light and dark mode

## Styling rules
- Tailwind for layout and spacing
- CSS variables from src/styles/emoratest-tokens.css for brand colors
- Never hardcode colors that are already in tokens
- Border radius: 16px for cards, 9999px for pills/buttons
- Shadows: 0 4px 20px rgba(0,0,0,0.08) for cards

## Data fetching
- Dashboard pages: React Query for all API calls
- Landing page: ZERO API calls — hardcoded static content only
- Use NEXT_PUBLIC_API_URL env var as base URL — never hardcode localhost
- Always wrap fetch in try/catch
- Always check res.ok before parsing JSON

## StatCard component
- Named export: import { StatCard } from '@/components/ui/StatCard'
- NOT default export

## Known issues fixed — do not reintroduce
- "use client" on page.tsx breaks metadata → never do it
- LazySection without observer.disconnect() causes flicker → always disconnect
- useState(false) for visibility hides content on load → use useState(true)
- Position absolute on stat cards causes overlap → use normal flow