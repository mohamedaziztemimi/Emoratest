#!/usr/bin/env python3
"""
Generate Epic 5 - Merchant Dashboard v1 (CONV-51 to CONV-55) course-style PDF.

Usage:
    cd docs && python generate_epic5_report.py
"""

from fpdf import FPDF


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Conversiono - Epic 5: Merchant Dashboard v1", align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, num: int, title: str):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 30, 120)
        self.cell(0, 12, f"Chapter {num}: {title}", new_x="LMARGIN", new_y="NEXT")
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def section(self, title: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def code(self, text: str):
        self.set_font("Courier", "", 8.5)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 4.5, text, fill=True)
        self.ln(3)

    def bullet(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        self.cell(6, 5.5, "- ")
        self.multi_cell(0, 5.5, text)
        self.set_x(x)


def build_pdf():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Title Page ───────────────────────────────────────────
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(30, 30, 120)
    pdf.cell(0, 15, "Epic 5: Merchant Dashboard v1", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "CONV-51 through CONV-55", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "Conversiono Course Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Stack: Next.js 14 | React 18 | TypeScript | Tailwind CSS v4 | Recharts", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Author: AI-assisted development | Date: March 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # ── Chapter 1: Architecture Overview ─────────────────────
    pdf.add_page()
    pdf.chapter_title(1, "Architecture Overview")

    pdf.body(
        "The Merchant Dashboard is a Next.js 14 App Router application that provides "
        "a real-time analytics interface for e-commerce merchants using Conversiono. "
        "It connects to the FastAPI backend API built in Epics 3-4 and visualizes "
        "session data, behavioral analytics, experiments, and intervention performance."
    )

    pdf.section("Technology Choices")
    pdf.bullet("Next.js 14 App Router: File-system routing, React Server Components support, built-in optimization")
    pdf.bullet("React 18: Concurrent features, hooks-based architecture")
    pdf.bullet("TypeScript: Full type safety across all components and API calls")
    pdf.bullet("Tailwind CSS v4: Utility-first styling with @tailwindcss/postcss plugin")
    pdf.bullet("Recharts: Composable charting library for data visualization")
    pdf.bullet("clsx: Conditional CSS class merging utility")

    pdf.section("Directory Structure")
    pdf.code(
        "frontend/src/\n"
        "  app/\n"
        "    layout.tsx              # Root layout with Tailwind globals\n"
        "    page.tsx                # Redirect to /dashboard\n"
        "    globals.css             # Tailwind v4 import\n"
        "    dashboard/\n"
        "      layout.tsx            # Dashboard shell wrapper\n"
        "      page.tsx              # Overview (KPIs, funnel, risk)\n"
        "      sessions/\n"
        "        page.tsx            # Session list with filters\n"
        "        [id]/page.tsx       # Session detail view\n"
        "      analytics/page.tsx    # Full analytics dashboard\n"
        "      experiments/page.tsx  # Experiment CRUD + stats\n"
        "      interventions/page.tsx # Intervention performance\n"
        "      settings/page.tsx     # SDK key + merchant profile\n"
        "  components/\n"
        "    layout/\n"
        "      Sidebar.tsx           # Navigation sidebar\n"
        "      DashboardShell.tsx    # Shell with responsive sidebar\n"
        "    ui/\n"
        "      Card.tsx              # Card, CardHeader, CardBody\n"
        "      StatCard.tsx          # KPI metric card\n"
        "      Badge.tsx             # Status badge\n"
        "      Spinner.tsx           # Loading spinner\n"
        "      ErrorBox.tsx          # Error display with retry\n"
        "      EmptyState.tsx        # Empty state placeholder\n"
        "  lib/\n"
        "    api.ts                  # Typed API client (26 endpoints)\n"
        "    hooks.ts                # useQuery custom hook\n"
        "    format.ts               # Formatting utilities"
    )

    # ── Chapter 2: API Client Layer ──────────────────────────
    pdf.add_page()
    pdf.chapter_title(2, "API Client Layer (CONV-51)")

    pdf.body(
        "The API client in src/lib/api.ts is a centralized, typed HTTP client that handles "
        "all communication with the FastAPI backend. It implements SDK key authentication, "
        "error handling, and provides TypeScript interfaces for every API response."
    )

    pdf.section("Key Design Decisions")
    pdf.bullet("Single request() function: All API calls go through one function that handles headers, auth, and errors")
    pdf.bullet("SDK key from localStorage: The X-SDK-Key header is automatically included in every request")
    pdf.bullet("Typed responses: Every endpoint returns a strongly-typed Promise<T>")
    pdf.bullet("ApiError class: Custom error with status code and detail message for UI error handling")
    pdf.bullet("No external dependencies: Uses native fetch API, no axios or similar")

    pdf.section("Authentication Pattern")
    pdf.code(
        "function getSdkKey(): string {\n"
        "  if (typeof window === 'undefined') return '';\n"
        "  return localStorage.getItem('conversiono_sdk_key') || '';\n"
        "}\n\n"
        "// Included in every request:\n"
        "headers: {\n"
        "  'Content-Type': 'application/json',\n"
        "  ...(sdkKey ? { 'X-SDK-Key': sdkKey } : {}),\n"
        "}"
    )

    pdf.section("API Endpoints Covered")
    pdf.bullet("Sessions: fetchSessions (list+filter), fetchSessionDetail")
    pdf.bullet("Analytics: fetchFunnel, fetchFrictionMap, fetchCohorts, fetchRiskDistribution")
    pdf.bullet("Experiments: fetchExperiments, fetchExperiment, createExperiment, deleteExperiment, fetchExperimentStats")
    pdf.bullet("Interventions: fetchInterventionRecs, fetchInterventionStats")
    pdf.bullet("Merchant: fetchMerchantProfile, fetchUsage, rotateKey")

    # ── Chapter 3: Custom Hooks ──────────────────────────────
    pdf.add_page()
    pdf.chapter_title(3, "Custom React Hooks")

    pdf.body(
        "The useQuery hook in src/lib/hooks.ts implements an SWR-like data fetching "
        "pattern without any external dependencies. This keeps the bundle small while "
        "providing loading states, error handling, and manual refetch capability."
    )

    pdf.section("Hook API")
    pdf.code(
        "interface UseQueryResult<T> {\n"
        "  data: T | null;\n"
        "  error: string | null;\n"
        "  loading: boolean;\n"
        "  refetch: () => void;\n"
        "}\n\n"
        "function useQuery<T>(\n"
        "  fetcher: () => Promise<T>,\n"
        "  deps: unknown[] = []\n"
        "): UseQueryResult<T>"
    )

    pdf.section("How It Works")
    pdf.bullet("Uses useState for data, error, loading, and a tick counter for refetch")
    pdf.bullet("useEffect triggers the fetcher on mount and when deps or tick change")
    pdf.bullet("Cleanup function sets cancelled=true to prevent state updates on unmounted components")
    pdf.bullet("refetch() increments the tick counter, which triggers a new useEffect cycle")

    pdf.section("Usage Pattern")
    pdf.code(
        "// Simple fetch on mount:\n"
        "const { data, error, loading } = useQuery(() => fetchUsage());\n\n"
        "// With dependencies (re-fetches when filters change):\n"
        "const { data } = useQuery(\n"
        "  useCallback(() => fetchSessions(filters), [filters]),\n"
        "  [JSON.stringify(filters)]\n"
        ");"
    )

    # ── Chapter 4: Dashboard Layout ──────────────────────────
    pdf.add_page()
    pdf.chapter_title(4, "Dashboard Layout & Navigation (CONV-51)")

    pdf.body(
        "The dashboard uses a shell pattern with a fixed sidebar on desktop and a "
        "toggleable mobile drawer. The layout leverages Next.js App Router's nested "
        "layouts so the sidebar persists across page navigations without remounting."
    )

    pdf.section("Sidebar Component")
    pdf.bullet("6 navigation items: Overview, Sessions, Analytics, Experiments, Interventions, Settings")
    pdf.bullet("Active state highlighting using usePathname() from next/navigation")
    pdf.bullet("Inline SVG icons (no icon library dependency)")
    pdf.bullet("Exact match for /dashboard, prefix match for sub-routes")

    pdf.section("Responsive Design")
    pdf.code(
        "// DashboardShell.tsx\n"
        "// Mobile: sidebar hidden by default, toggle with hamburger\n"
        "// Desktop (lg+): sidebar always visible\n\n"
        "<div className={clsx(\n"
        "  'fixed inset-y-0 left-0 z-40 lg:static',\n"
        "  sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'\n"
        ")} />\n\n"
        "// Overlay backdrop on mobile when sidebar is open\n"
        "{sidebarOpen && (\n"
        "  <div className='fixed inset-0 z-30 bg-black/30 lg:hidden'\n"
        "       onClick={() => setSidebarOpen(false)} />\n"
        ")}"
    )

    # ── Chapter 5: Overview Page ─────────────────────────────
    pdf.add_page()
    pdf.chapter_title(5, "Overview Dashboard Page")

    pdf.body(
        "The overview page at /dashboard is the landing page after login. It displays "
        "four KPI cards, a conversion funnel bar chart, and a risk distribution pie chart. "
        "All data loads in parallel using three separate useQuery hooks."
    )

    pdf.section("Data Sources")
    pdf.bullet("fetchUsage() -> KPI cards: total sessions, events, active today, experiments")
    pdf.bullet("fetchFunnel() -> Horizontal bar chart showing session counts per funnel step")
    pdf.bullet("fetchRiskDistribution(5) -> Pie chart with 5 risk buckets color-coded green to red")

    pdf.section("Chart Implementation")
    pdf.code(
        "// Funnel: horizontal bar chart\n"
        "<BarChart data={funnel.data.steps} layout='vertical'>\n"
        "  <XAxis type='number' />\n"
        "  <YAxis type='category' dataKey='step' />\n"
        "  <Bar dataKey='sessions' fill='#6366f1' />\n"
        "</BarChart>\n\n"
        "// Risk: Pie chart with Cell-based coloring\n"
        "<Pie data={buckets} dataKey='session_count' nameKey='range_label'>\n"
        "  {buckets.map((_, i) => (\n"
        "    <Cell key={i} fill={RISK_COLORS[i % RISK_COLORS.length]} />\n"
        "  ))}\n"
        "</Pie>"
    )

    # ── Chapter 6: Sessions Pages ────────────────────────────
    pdf.add_page()
    pdf.chapter_title(6, "Sessions List & Detail (CONV-52, CONV-53)")

    pdf.section("Sessions List Page")
    pdf.body(
        "The sessions list at /dashboard/sessions provides a filterable, paginated "
        "table of all tracked sessions. Merchants can filter by outcome, device type, "
        "minimum risk score, and date range."
    )

    pdf.bullet("Filter bar: outcome select, device select, risk min input, date from/to")
    pdf.bullet("Table columns: session ID (linked), page URL, started at, outcome badge, risk score, device")
    pdf.bullet("Pagination: previous/next buttons, shows page X of Y and total count")
    pdf.bullet("All filters reset page to 1 when changed (prevents empty pages)")

    pdf.section("Session Detail Page")
    pdf.body(
        "The detail page at /dashboard/sessions/[id] shows comprehensive information "
        "for a single session, including behavioral features, intervention recommendations, "
        "and a scrollable event timeline."
    )

    pdf.bullet("Breadcrumb navigation back to sessions list")
    pdf.bullet("4 metric boxes: abandonment risk, friction score, intent label, device type")
    pdf.bullet("Behavioral features grid: 8 ML-computed features with formatted values")
    pdf.bullet("Intervention recommendations: psychology-based suggestions with priority and basis")
    pdf.bullet("Event timeline table: time, type, element, position, velocity (max height 500px, scrollable)")

    pdf.section("Dynamic Routing")
    pdf.code(
        "// Next.js dynamic route: app/dashboard/sessions/[id]/page.tsx\n"
        "export default function SessionDetailPage() {\n"
        "  const { id } = useParams<{ id: string }>();\n"
        "  const session = useQuery(() => fetchSessionDetail(id), [id]);\n"
        "  const interventions = useQuery(() => fetchInterventionRecs(id), [id]);\n"
        "  // Both API calls run in parallel on mount\n"
        "}"
    )

    # ── Chapter 7: Analytics Dashboard ───────────────────────
    pdf.add_page()
    pdf.chapter_title(7, "Analytics Dashboard (CONV-54)")

    pdf.body(
        "The analytics page at /dashboard/analytics is the most data-rich page, "
        "combining four visualization types: funnel chart, friction hotspots table, "
        "risk distribution histogram, and interactive cohort analysis."
    )

    pdf.section("Conversion Funnel")
    pdf.bullet("Vertical bar chart with sessions (indigo) and drop-off (red) bars")
    pdf.bullet("Shows step names on X axis, counts on Y axis")

    pdf.section("Friction Hotspots")
    pdf.bullet("Scrollable table of top 30 UI elements by friction score")
    pdf.bullet("Columns: element ID, event count, rage clicks, rage click rate, avg hesitation")
    pdf.bullet("Rage click counts highlighted in red for quick identification")

    pdf.section("Risk Distribution")
    pdf.bullet("Bar chart with 10 configurable buckets")
    pdf.bullet("Shows session count per risk range")

    pdf.section("Cohort Analysis")
    pdf.bullet("Interactive dimension selector: device_type, country_code, outcome, intent_label")
    pdf.bullet("Combo chart: bars for session count (left Y), line for conversion rate (right Y)")
    pdf.bullet("Re-fetches data when dimension changes using useCallback + dependency array")

    pdf.code(
        "// Cohort dimension switching\n"
        "const [cohortDim, setCohortDim] = useState('device_type');\n"
        "const cohorts = useQuery(\n"
        "  useCallback(() => fetchCohorts(cohortDim), [cohortDim]),\n"
        "  [cohortDim]\n"
        ");"
    )

    # ── Chapter 8: Experiments Management ────────────────────
    pdf.add_page()
    pdf.chapter_title(8, "Experiments Management (CONV-55)")

    pdf.body(
        "The experiments page at /dashboard/experiments provides full CRUD for A/B "
        "experiments plus statistical analysis. Merchants can create experiments, view "
        "results, and get significance testing with recommendations."
    )

    pdf.section("Features")
    pdf.bullet("Create form: title, hypothesis, friction type, variant A/B descriptions")
    pdf.bullet("Experiment cards: show title, hypothesis, variants, result badge, conversion delta, sample size")
    pdf.bullet("Stats panel: p-value, significance flag, statistical power, recommendation text")
    pdf.bullet("Delete with confirmation dialog")
    pdf.bullet("Paginated list (20 per page)")

    pdf.section("Input Validation")
    pdf.code(
        "// HTML5 validation + maxLength for XSS prevention\n"
        "<input name='title' required maxLength={200} />\n"
        "<textarea name='hypothesis' maxLength={1000} />\n"
        "// Backend also validates with Pydantic + sanitize_text()"
    )

    pdf.section("Statistics Display")
    pdf.code(
        "// Stats panel shows computed values from backend Z-test\n"
        "function StatsPanel({ stats }) {\n"
        "  return (\n"
        "    <dl>\n"
        "      <dt>Conversion Delta</dt><dd>{formatPercent(stats.conversion_delta)}</dd>\n"
        "      <dt>p-value</dt><dd>{stats.p_value?.toFixed(4)}</dd>\n"
        "      <dt>Significant?</dt><dd>{stats.is_significant ? 'Yes' : 'No'}</dd>\n"
        "      <dt>Power</dt><dd>{stats.power?.toFixed(2)}</dd>\n"
        "    </dl>\n"
        "    <p>{stats.recommendation}</p>\n"
        "  );\n"
        "}"
    )

    # ── Chapter 9: Interventions Dashboard ───────────────────
    pdf.add_page()
    pdf.chapter_title(9, "Interventions Dashboard (CONV-55)")

    pdf.body(
        "The interventions page at /dashboard/interventions visualizes the performance "
        "of all psychology-based interventions. It shows a stacked bar chart of outcomes "
        "and a detailed statistics table."
    )

    pdf.section("Stacked Bar Chart")
    pdf.bullet("X axis: intervention IDs (INT-001 through INT-008)")
    pdf.bullet("Stacked segments: converted (green), dismissed (orange), ignored (gray), bounced (red)")
    pdf.bullet("Gives instant visual feedback on which interventions are effective")

    pdf.section("Statistics Table")
    pdf.bullet("8 columns: intervention, triggers, converted, dismissed, ignored, bounced, conv rate, avg delta")
    pdf.bullet("Color-coded values: green for conversions, red for bounced, indigo for conversion rate")

    # ── Chapter 10: Settings Page ────────────────────────────
    pdf.add_page()
    pdf.chapter_title(10, "Settings & SDK Key Management")

    pdf.body(
        "The settings page at /dashboard/settings allows merchants to manage their "
        "SDK key and view their merchant profile. The SDK key is stored in localStorage "
        "and sent as the X-SDK-Key header with every API request."
    )

    pdf.section("SDK Key Management")
    pdf.bullet("Input field shows current key from localStorage")
    pdf.bullet("Save button persists to localStorage and reloads the page")
    pdf.bullet("Rotate button calls POST /merchants/rotate-key with confirmation dialog")
    pdf.bullet("After rotation: new key auto-saved, old key immediately invalidated")

    pdf.section("Security Considerations")
    pdf.bullet("SDK key stored in localStorage (acceptable for merchant dashboard, not for end-user tokens)")
    pdf.bullet("Key rotation is destructive: confirmation dialog prevents accidental rotation")
    pdf.bullet("Backend uses SHA-256 hashing: raw key never stored server-side")

    # ── Chapter 11: Reusable UI Components ───────────────────
    pdf.add_page()
    pdf.chapter_title(11, "Reusable UI Component Library")

    pdf.body(
        "The dashboard includes 6 reusable UI components in src/components/ui/ that "
        "provide consistent styling and behavior across all pages."
    )

    pdf.section("Component Catalog")
    pdf.bullet("Card / CardHeader / CardBody: Rounded white cards with border, shadow, and optional header")
    pdf.bullet("StatCard: KPI display with label, value, optional subtitle and trend color (up/down/neutral)")
    pdf.bullet("Badge: Pill-shaped status indicator with customizable colors via className")
    pdf.bullet("Spinner: Centered loading animation using Tailwind animate-spin")
    pdf.bullet("ErrorBox: Red-tinted error message with optional retry button")
    pdf.bullet("EmptyState: Centered illustration with title and description for empty data states")

    pdf.section("Design Principles")
    pdf.bullet("Composition over configuration: Card is split into 3 sub-components")
    pdf.bullet("Tailwind-only: No CSS modules or styled-components")
    pdf.bullet("clsx for conditional classes: Clean ternary-based class merging")
    pdf.bullet("No external icon library: Inline SVGs keep the bundle lean")

    # ── Chapter 12: Formatting Utilities ─────────────────────
    pdf.add_page()
    pdf.chapter_title(12, "Formatting Utilities")

    pdf.body(
        "The format.ts module provides 7 pure functions for consistent data display "
        "across the entire dashboard. All functions handle null/undefined gracefully "
        "by returning an em-dash character."
    )

    pdf.section("Function Reference")
    pdf.code(
        "formatPercent(0.234)       -> '23.4%'\n"
        "formatRisk(0.75)           -> '75% High'\n"
        "formatRisk(0.45)           -> '45% Med'\n"
        "formatRisk(0.2)            -> '20% Low'\n"
        "formatDate('2026-03-15T14:30:00Z') -> 'Mar 15, 02:30 PM'\n"
        "formatDuration(125)        -> '2m 5s'\n"
        "formatNumber(1234567)      -> '1,234,567'\n"
        "riskColor(0.8)             -> 'text-red-600'\n"
        "outcomeColor('purchase')   -> 'bg-green-100 text-green-800'"
    )

    # ── Chapter 13: Build & Deployment ───────────────────────
    pdf.add_page()
    pdf.chapter_title(13, "Build Configuration & Deployment")

    pdf.section("Tailwind CSS v4 Setup")
    pdf.code(
        "// postcss.config.mjs\n"
        "const config = {\n"
        "  plugins: { '@tailwindcss/postcss': {} },\n"
        "};\n\n"
        "// globals.css\n"
        "@import 'tailwindcss';"
    )

    pdf.section("Build Output")
    pdf.code(
        "Route (app)                           Size      First Load JS\n"
        "/                                     138 B     87.5 kB\n"
        "/dashboard                            8.12 kB   207 kB\n"
        "/dashboard/analytics                  8.68 kB   208 kB\n"
        "/dashboard/experiments                5.1 kB    92.4 kB\n"
        "/dashboard/interventions              3.13 kB   202 kB\n"
        "/dashboard/sessions                   4.31 kB   101 kB\n"
        "/dashboard/sessions/[id]              4.62 kB   101 kB\n"
        "/dashboard/settings                   3.81 kB   91.1 kB"
    )

    pdf.section("Environment Variables")
    pdf.code(
        "# .env.local\n"
        "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1\n\n"
        "# Production\n"
        "NEXT_PUBLIC_API_URL=https://api.conversiono.com/api/v1"
    )

    # ── Chapter 14: Human Intervention Report ────────────────
    pdf.add_page()
    pdf.chapter_title(14, "Human Intervention Required")

    pdf.body(
        "The following items require manual human setup or decision-making before "
        "the dashboard is fully production-ready:"
    )

    pdf.section("1. Environment Configuration")
    pdf.bullet("Set NEXT_PUBLIC_API_URL for your deployment environment")
    pdf.bullet("Configure CORS on the backend to allow the frontend origin")

    pdf.section("2. Authentication Enhancement")
    pdf.bullet("Current auth uses SDK key in localStorage. For production, consider adding proper login flow with JWT tokens and HTTP-only cookies")
    pdf.bullet("Add session timeout and automatic key refresh logic")

    pdf.section("3. SSL/TLS")
    pdf.bullet("Ensure HTTPS is configured for both frontend and API endpoints")
    pdf.bullet("Set Secure and SameSite flags on any cookies")

    pdf.section("4. Content Security Policy")
    pdf.bullet("Add CSP headers in next.config.js to prevent XSS")
    pdf.bullet("Configure allowed sources for scripts, styles, and API connections")

    pdf.section("5. Error Monitoring")
    pdf.bullet("Integrate Sentry or similar for frontend error tracking")
    pdf.bullet("Add performance monitoring (Web Vitals) for production metrics")

    pdf.section("6. Testing")
    pdf.bullet("Add E2E tests with Playwright or Cypress for critical user flows")
    pdf.bullet("Add component tests with React Testing Library")
    pdf.bullet("Set up visual regression testing for chart components")

    pdf.section("7. Accessibility")
    pdf.bullet("Run axe-core audit and fix any WCAG 2.1 AA violations")
    pdf.bullet("Add ARIA labels to chart components")
    pdf.bullet("Test keyboard navigation through all pages")

    pdf.section("8. Data Seeding")
    pdf.bullet("Run the backend seed scripts to populate demo data for testing")
    pdf.bullet("Verify all chart visualizations render correctly with real data")

    # ── Output ───────────────────────────────────────────────
    output_path = "Epic5_Merchant_Dashboard_v1.pdf"
    pdf.output(output_path)
    print(f"Generated: {output_path} ({pdf.pages_count} pages)")


if __name__ == "__main__":
    build_pdf()
