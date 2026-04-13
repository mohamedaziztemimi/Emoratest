"""Generate Epic 5 Course-Style Documentation PDF — Merchant Dashboard v1.

Run:  python docs/generate_epic5_report.py

Produces: docs/Epic5_Merchant_Dashboard_v1.pdf
"""

from __future__ import annotations

from fpdf import FPDF


class CoursePDF(FPDF):
    """Custom PDF with header/footer and styling helpers."""

    PRIMARY = (41, 98, 255)
    DARK = (30, 30, 30)
    GRAY = (100, 100, 100)
    LIGHT_BG = (245, 247, 250)
    WHITE = (255, 255, 255)
    GREEN = (34, 197, 94)
    AMBER = (245, 158, 11)
    ACCENT = (99, 102, 241)
    TIP_BG = (219, 234, 254)
    TIP_BORDER = (59, 130, 246)
    WARN_BG = (254, 243, 199)
    WARN_BORDER = (245, 158, 11)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.GRAY)
        self.cell(0, 8, "EmoraTest - Epic 5: Merchant Dashboard v1", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, "EmoraTest AI Platform - Course Documentation", align="C")

    def chapter_title(self, num: str, title: str):
        self.add_page()
        self.ln(10)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*self.PRIMARY)
        self.cell(0, 12, f"Chapter {num}", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*self.DARK)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.7)
        self.line(self.l_margin, self.get_y() + 2, self.l_margin + 80, self.get_y() + 2)
        self.ln(8)

    def section_title(self, num: str, title: str):
        self.ln(6)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.PRIMARY)
        self.cell(0, 9, f"{num}  {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.l_margin + 50, self.get_y())
        self.ln(3)

    def subsection(self, title: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.DARK)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text: str, indent: int = 10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        self.cell(indent, 5.5, "")
        w = self.w - self.l_margin - self.r_margin - indent - 5
        self.cell(5, 5.5, "- ")
        self.multi_cell(w, 5.5, text)
        self.set_x(self.l_margin)

    def numbered(self, num: int, text: str, indent: int = 10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        self.cell(indent, 5.5, "")
        self.set_font("Helvetica", "B", 10)
        self.cell(8, 5.5, f"{num}.")
        self.set_font("Helvetica", "", 10)
        w = self.w - self.l_margin - self.r_margin - indent - 13
        self.multi_cell(w, 5.5, text)
        self.set_x(self.l_margin)

    def code_block(self, text: str):
        self.set_fill_color(*self.LIGHT_BG)
        self.set_font("Courier", "", 8.5)
        self.set_text_color(60, 60, 60)
        x = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        lines = text.strip().split("\n")
        h = len(lines) * 4.5 + 6
        if self.get_y() + h > self.h - 25:
            self.add_page()
        self.rect(x, self.get_y(), w, h, style="F")
        self.set_xy(x + 4, self.get_y() + 3)
        for line in lines:
            self.cell(0, 4.5, line[:95], new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 4)
        self.ln(4)

    def tip_box(self, title: str, text: str):
        self._callout(title, text, self.TIP_BG, self.TIP_BORDER)

    def warn_box(self, title: str, text: str):
        self._callout(title, text, self.WARN_BG, self.WARN_BORDER)

    def _callout(self, title: str, text: str, bg: tuple, border_color: tuple):
        x = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        self.set_fill_color(*bg)
        self.set_draw_color(*border_color)
        lines = text.strip().split("\n")
        h = len(lines) * 5 + 14
        if self.get_y() + h > self.h - 25:
            self.add_page()
        y_start = self.get_y()
        self.rect(x, y_start, w, h, style="FD")
        self.line(x, y_start, x, y_start + h)
        self.set_xy(x + 5, y_start + 3)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*border_color)
        self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        self.set_x(x + 5)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.DARK)
        for line in lines:
            self.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 5)
        self.set_y(y_start + h + 4)

    def table_header(self, cols: list[tuple[str, int]]):
        self.set_fill_color(*self.PRIMARY)
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 9)
        for col_name, col_w in cols:
            self.cell(col_w, 7, col_name, border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(*self.DARK)

    def table_row(self, values: list[str], widths: list[int]):
        self.set_font("Helvetica", "", 9)
        for val, w in zip(values, widths):
            self.cell(w, 6, val, border=1, align="C")
        self.ln()


# ─────────────────────────────────────────────────────────
#  Content helpers
# ─────────────────────────────────────────────────────────

def _cover(pdf: CoursePDF) -> None:
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.cell(0, 14, "EmoraTest AI Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(0, 12, "Epic 5: Merchant Dashboard v1", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 10, "Comprehensive Course Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(*pdf.PRIMARY)
    pdf.set_line_width(1)
    cx = pdf.w / 2
    pdf.line(cx - 40, pdf.get_y(), cx + 40, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 8, "Jira Stories: CONV-51 through CONV-55", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Next.js 14  |  React 18  |  TypeScript 5  |  Tailwind v4  |  Recharts", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Sprint 5  -  March 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(0, 7, "16 Chapters  |  7 Dashboard Pages  |  26 API Endpoints  |  Full Component Library", align="C", new_x="LMARGIN", new_y="NEXT")


def _toc(pdf: CoursePDF) -> None:
    pdf.add_page()
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*pdf.PRIMARY)
    pdf.set_line_width(0.7)
    pdf.line(pdf.l_margin, pdf.get_y() + 2, pdf.l_margin + 60, pdf.get_y() + 2)
    pdf.ln(8)

    chapters = [
        ("1", "Architecture Overview"),
        ("2", "Technology Stack & Project Setup"),
        ("3", "API Client Layer (CONV-51)"),
        ("4", "Custom React Hooks"),
        ("5", "Dashboard Layout & Navigation (CONV-51)"),
        ("6", "Reusable UI Component Library"),
        ("7", "Overview Dashboard Page"),
        ("8", "Sessions List & Filtering (CONV-52)"),
        ("9", "Session Detail View (CONV-53)"),
        ("10", "Analytics Dashboard (CONV-54)"),
        ("11", "Experiments Management (CONV-55)"),
        ("12", "Interventions Dashboard (CONV-55)"),
        ("13", "Settings & SDK Key Management"),
        ("14", "Formatting Utilities"),
        ("15", "Performance Optimization Deep Dive"),
        ("16", "Build, Deploy & Next Steps"),
    ]
    for num, title in chapters:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*pdf.PRIMARY)
        pdf.cell(12, 7, num)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*pdf.DARK)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")


# ─────────────────────────────────────────────────────────
#  Chapter 1 - Architecture Overview
# ─────────────────────────────────────────────────────────

def _ch01(pdf: CoursePDF) -> None:
    pdf.chapter_title("1", "Architecture Overview")

    pdf.section_title("1.1", "Layered Architecture")
    pdf.body(
        "The EmoraTest frontend follows a clean layered architecture that separates concerns into "
        "distinct tiers. Each layer has a single responsibility and communicates only with its "
        "adjacent layers. This pattern ensures maintainability, testability, and scalability as "
        "the application grows."
    )
    pdf.body(
        "At the highest level, the architecture consists of four layers:"
    )
    pdf.numbered(1, "Presentation Layer (Pages & Components): React components that render UI and handle user interactions. Each page lives under app/ using Next.js App Router conventions.")
    pdf.numbered(2, "State & Data Layer (Hooks): Custom hooks like useQuery that manage server state, caching, and data fetching lifecycle. This layer abstracts away the complexity of API communication.")
    pdf.numbered(3, "API Client Layer (lib/api.ts): A typed fetch wrapper that handles HTTP communication, timeouts, authentication headers, and error normalization.")
    pdf.numbered(4, "External Services: The backend REST API, which provides sessions, analytics, experiments, interventions, and merchant management endpoints.")

    pdf.tip_box(
        "Why Layered Architecture?",
        "By isolating each concern, you can swap implementations without\n"
        "affecting other layers. For example, you could replace the fetch-based\n"
        "API client with Axios or GraphQL without changing any page component."
    )

    pdf.section_title("1.2", "Directory Structure")
    pdf.body(
        "The project follows Next.js 14 App Router conventions where each folder under app/ "
        "represents a URL route. Components, hooks, and utilities live in dedicated directories "
        "outside the app/ folder for reusability."
    )
    pdf.code_block(
        "frontend/src/\n"
        "  app/\n"
        "    layout.tsx              # Root layout (html + body)\n"
        "    page.tsx                # Redirect to /dashboard\n"
        "    globals.css             # Tailwind v4 + design tokens\n"
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
        "    charts/LazyRecharts.tsx  # Lazy-loaded chart wrappers\n"
        "    layout/Sidebar.tsx       # Navigation sidebar\n"
        "    layout/DashboardShell.tsx # Shell with responsive sidebar\n"
        "    ui/                      # Card, Badge, Spinner, etc.\n"
        "  lib/\n"
        "    api.ts                   # Typed API client\n"
        "    hooks.ts                 # useQuery with caching\n"
        "    format.ts               # Formatting utilities"
    )

    pdf.section_title("1.3", "Data Flow")
    pdf.body(
        "Data flows unidirectionally through the application. Understanding this flow is "
        "critical for debugging and extending the dashboard:"
    )
    pdf.numbered(1, "User navigates to a page (e.g., /dashboard/sessions).")
    pdf.numbered(2, "The page component calls useQuery with an API endpoint function (e.g., getSessions).")
    pdf.numbered(3, "useQuery checks its in-memory cache. If a valid entry exists (< 30s old), it returns cached data immediately.")
    pdf.numbered(4, "If cache misses, useQuery calls the API client function, which issues a fetch() with AbortController timeout.")
    pdf.numbered(5, "The API client attaches the X-SDK-Key header from localStorage and sends the request to the backend.")
    pdf.numbered(6, "The response is parsed, cached, and returned to the component, which renders the UI.")
    pdf.numbered(7, "If the user navigates away before the response arrives, the cancelled flag prevents stale state updates.")

    pdf.warn_box(
        "Important: Server Components vs Client Components",
        "All dashboard pages use 'use client' because they depend on\n"
        "browser APIs (localStorage, useState, useEffect). The root\n"
        "layout.tsx is a Server Component that wraps the client tree."
    )

    pdf.section_title("1.4", "Jira Story Mapping")
    pdf.body(
        "Epic 5 consists of five Jira stories, each delivering a vertical slice of functionality:"
    )
    cols = [("Story", 30), ("Title", 70), ("Scope", 80)]
    pdf.table_header(cols)
    pdf.table_row(["CONV-51", "Dashboard Foundation", "Layout, API client, hooks, overview"], [30, 70, 80])
    pdf.table_row(["CONV-52", "Session Explorer", "Session list, filters, pagination"], [30, 70, 80])
    pdf.table_row(["CONV-53", "Session Detail", "Detail view, features, timeline"], [30, 70, 80])
    pdf.table_row(["CONV-54", "Analytics Dashboard", "Charts, cohorts, friction analysis"], [30, 70, 80])
    pdf.table_row(["CONV-55", "Experiments & More", "CRUD, interventions, settings"], [30, 70, 80])


# ─────────────────────────────────────────────────────────
#  Chapter 2 - Technology Stack & Project Setup
# ─────────────────────────────────────────────────────────

def _ch02(pdf: CoursePDF) -> None:
    pdf.chapter_title("2", "Technology Stack & Project Setup")

    pdf.section_title("2.1", "Core Dependencies")
    pdf.body(
        "The project is built on a modern React stack optimized for developer experience and "
        "runtime performance. Every dependency was chosen deliberately to minimize bundle size "
        "while maximizing capability."
    )
    cols = [("Package", 45), ("Version", 25), ("Purpose", 110)]
    pdf.table_header(cols)
    pdf.table_row(["Next.js", "14.x", "App Router, SSR, file-based routing, image optimization"], [45, 25, 110])
    pdf.table_row(["React", "18.x", "Component model, hooks, concurrent features"], [45, 25, 110])
    pdf.table_row(["TypeScript", "5.x", "Static typing with strict mode for safety"], [45, 25, 110])
    pdf.table_row(["Tailwind CSS", "v4", "Utility-first CSS with HSL design tokens"], [45, 25, 110])
    pdf.table_row(["Recharts", "3.8", "Composable chart library built on D3"], [45, 25, 110])
    pdf.table_row(["clsx", "latest", "Conditional className merging utility"], [45, 25, 110])

    pdf.tip_box(
        "Why No State Management Library?",
        "We deliberately avoided Redux, Zustand, or Jotai. The useQuery\n"
        "hook with its built-in cache handles all server state. Local UI\n"
        "state (filters, form inputs) is managed with useState. This keeps\n"
        "the dependency tree lean and the mental model simple."
    )

    pdf.section_title("2.2", "Tailwind v4 and HSL Design Tokens")
    pdf.body(
        "Tailwind CSS v4 introduces a new CSS-first configuration approach. Instead of a "
        "tailwind.config.js file, design tokens are defined as CSS custom properties in "
        "globals.css. This is a major shift from Tailwind v3."
    )
    pdf.body(
        "The design system uses HSL (Hue, Saturation, Lightness) color values stored without "
        "the hsl() wrapper. This allows dynamic opacity via the syntax hsl(var(--primary)/0.5)."
    )
    pdf.code_block(
        "/* globals.css - Design Token Excerpt */\n"
        ":root {\n"
        "  --background: 0 0% 100%;\n"
        "  --foreground: 222.2 84% 4.9%;\n"
        "  --primary: 221.2 83.2% 53.3%;\n"
        "  --primary-foreground: 210 40% 98%;\n"
        "  --secondary: 210 40% 96.1%;\n"
        "  --muted: 210 40% 96.1%;\n"
        "  --muted-foreground: 215.4 16.3% 46.9%;\n"
        "  --destructive: 0 84.2% 60.2%;\n"
        "  --border: 214.3 31.8% 91.4%;\n"
        "  --ring: 221.2 83.2% 53.3%;\n"
        "  --radius: 0.5rem;\n"
        "}"
    )

    pdf.subsection("Using HSL Tokens in Components")
    pdf.body(
        "To use these tokens in Tailwind classes, you reference them with the hsl() function "
        "and var() syntax. The key insight is that the CSS variable holds the raw HSL values "
        "without the hsl() wrapper, enabling opacity modifiers."
    )
    pdf.code_block(
        '// Usage in a component\n'
        '<div className="bg-[hsl(var(--primary))]">\n'
        '  Solid primary background\n'
        '</div>\n'
        '<div className="bg-[hsl(var(--primary)/0.5)]">\n'
        '  50% opacity primary background\n'
        '</div>\n'
        '<div className="text-[hsl(var(--muted-foreground))]">\n'
        '  Muted text color\n'
        '</div>'
    )

    pdf.section_title("2.3", "TypeScript Strict Mode")
    pdf.body(
        "The project uses TypeScript strict mode, which enables all strict type-checking options "
        "including strictNullChecks, noImplicitAny, and strictFunctionTypes. This catches entire "
        "classes of bugs at compile time rather than runtime."
    )
    pdf.body(
        "Every API response is typed with explicit interfaces. The API client returns typed "
        "promises, and useQuery is generic over the response type. This creates a fully typed "
        "pipeline from the API to the rendered component."
    )
    pdf.code_block(
        "// Typed API response example\n"
        "interface Session {\n"
        "  session_id: string;\n"
        "  visitor_id: string;\n"
        "  outcome: 'converted' | 'abandoned' | 'bounced';\n"
        "  risk_score: number;\n"
        "  device_type: string;\n"
        "  created_at: string;\n"
        "}\n"
        "\n"
        "// useQuery infers the type from the fetcher\n"
        "const { data, loading, error } = useQuery<Session[]>(\n"
        "  'sessions',\n"
        "  () => getSessions(filters)\n"
        ");"
    )

    pdf.section_title("2.4", "Project Setup Steps")
    pdf.numbered(1, "Clone the repository and navigate to the frontend/ directory.")
    pdf.numbered(2, "Run 'npm install' to install all dependencies from package.json.")
    pdf.numbered(3, "Copy .env.example to .env.local and configure NEXT_PUBLIC_API_URL (defaults to http://localhost:8000).")
    pdf.numbered(4, "Run 'npm run dev' to start the Next.js development server on port 3000.")
    pdf.numbered(5, "Ensure the backend API is running on port 8000 for data to load.")
    pdf.numbered(6, "Navigate to http://localhost:3000 which redirects to /dashboard automatically.")

    pdf.warn_box(
        "CORS Configuration Required",
        "The backend must allow requests from localhost:3000 (and 3001 for\n"
        "alternate dev ports). The backend config.py was updated to include\n"
        "both origins. Verify CORS_ORIGINS in backend .env if you see errors."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 3 - API Client Layer
# ─────────────────────────────────────────────────────────

def _ch03(pdf: CoursePDF) -> None:
    pdf.chapter_title("3", "API Client Layer (CONV-51)")

    pdf.section_title("3.1", "The request() Function")
    pdf.body(
        "The core of the API layer is a single request() function in src/lib/api.ts. This "
        "function wraps the native fetch() API with three critical features: automatic timeout "
        "via AbortController, authentication header injection, and error normalization. Every "
        "API call in the application flows through this function."
    )
    pdf.code_block(
        "const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';\n"
        "\n"
        "class ApiError extends Error {\n"
        "  constructor(\n"
        "    public status: number,\n"
        "    public detail: string\n"
        "  ) {\n"
        "    super(detail);\n"
        "    this.name = 'ApiError';\n"
        "  }\n"
        "}\n"
        "\n"
        "async function request<T>(\n"
        "  path: string,\n"
        "  options: RequestInit = {}\n"
        "): Promise<T> {\n"
        "  const ctrl = new AbortController();\n"
        "  const timer = setTimeout(() => ctrl.abort(), 15_000);\n"
        "\n"
        "  const sdkKey =\n"
        "    typeof window !== 'undefined'\n"
        "      ? localStorage.getItem('sdkKey') ?? ''\n"
        "      : '';\n"
        "\n"
        "  try {\n"
        "    const res = await fetch(`${API}${path}`, {\n"
        "      ...options,\n"
        "      signal: ctrl.signal,\n"
        "      headers: {\n"
        "        'Content-Type': 'application/json',\n"
        "        'X-SDK-Key': sdkKey,\n"
        "        ...options.headers,\n"
        "      },\n"
        "    });\n"
        "    if (!res.ok) {\n"
        "      const body = await res.json().catch(() => ({}));\n"
        "      throw new ApiError(res.status, body.detail ?? res.statusText);\n"
        "    }\n"
        "    return (await res.json()) as T;\n"
        "  } catch (err) {\n"
        "    if (err instanceof DOMException && err.name === 'AbortError') {\n"
        "      throw new ApiError(0, 'Request timed out after 15s');\n"
        "    }\n"
        "    throw err;\n"
        "  } finally {\n"
        "    clearTimeout(timer);\n"
        "  }\n"
        "}"
    )

    pdf.tip_box(
        "AbortController Pattern",
        "AbortController is the modern way to cancel fetch requests. By\n"
        "creating one per request and aborting after 15 seconds, we prevent\n"
        "hanging requests from blocking the UI. The finally block ensures\n"
        "the timer is always cleared, preventing memory leaks."
    )

    pdf.section_title("3.2", "Authentication Pattern")
    pdf.body(
        "Authentication uses a simple SDK key stored in localStorage. The key is read on every "
        "request and sent as the X-SDK-Key header. This pattern was chosen for its simplicity "
        "in a merchant dashboard context where the SDK key identifies the merchant account."
    )
    pdf.body(
        "The typeof window !== 'undefined' guard is essential in Next.js because code can "
        "execute on the server during SSR where localStorage is not available. This guard "
        "prevents ReferenceError crashes during server-side rendering."
    )

    pdf.warn_box(
        "Security Note: localStorage Limitations",
        "localStorage is vulnerable to XSS attacks. For production, consider\n"
        "httpOnly cookies or a backend-for-frontend (BFF) token exchange.\n"
        "The current pattern is acceptable for an internal merchant dashboard\n"
        "but should be hardened before public deployment."
    )

    pdf.section_title("3.3", "Custom ApiError Class")
    pdf.body(
        "The ApiError class extends the native Error with two additional properties: status "
        "(HTTP status code) and detail (human-readable message). This enables downstream code "
        "to handle errors based on status codes (401 for auth, 404 for not found, etc.)."
    )
    pdf.body(
        "When the response is not OK, the function attempts to parse the JSON body for a "
        "detail field (following FastAPI's error convention). If parsing fails, it falls back "
        "to the HTTP status text."
    )

    pdf.section_title("3.4", "Endpoint Coverage")
    pdf.body(
        "The API client provides 26 typed functions across 6 categories. Each function calls "
        "request<T>() with the appropriate path and HTTP method."
    )
    cols = [("Category", 35), ("Function", 55), ("Method", 20), ("Path", 70)]
    pdf.table_header(cols)
    pdf.table_row(["Sessions", "getSessions()", "GET", "/api/v1/sessions"], [35, 55, 20, 70])
    pdf.table_row(["Sessions", "getSession(id)", "GET", "/api/v1/sessions/:id"], [35, 55, 20, 70])
    pdf.table_row(["Sessions", "getSessionEvents(id)", "GET", "/api/v1/sessions/:id/events"], [35, 55, 20, 70])
    pdf.table_row(["Analytics", "getConversionFunnel()", "GET", "/api/v1/analytics/funnel"], [35, 55, 20, 70])
    pdf.table_row(["Analytics", "getFrictionPoints()", "GET", "/api/v1/analytics/friction"], [35, 55, 20, 70])
    pdf.table_row(["Analytics", "getRiskDistribution()", "GET", "/api/v1/analytics/risk"], [35, 55, 20, 70])
    pdf.table_row(["Analytics", "getCohortAnalysis()", "GET", "/api/v1/analytics/cohorts"], [35, 55, 20, 70])
    pdf.table_row(["Experiments", "getExperiments()", "GET", "/api/v1/experiments"], [35, 55, 20, 70])
    pdf.table_row(["Experiments", "createExperiment()", "POST", "/api/v1/experiments"], [35, 55, 20, 70])
    pdf.table_row(["Experiments", "getExperimentStats()", "GET", "/api/v1/experiments/:id/stats"], [35, 55, 20, 70])
    pdf.table_row(["Interventions", "getInterventions()", "GET", "/api/v1/interventions"], [35, 55, 20, 70])
    pdf.table_row(["Interventions", "getInterventionStats()", "GET", "/api/v1/interventions/stats"], [35, 55, 20, 70])
    pdf.table_row(["Merchant", "getMerchant()", "GET", "/api/v1/merchant"], [35, 55, 20, 70])
    pdf.table_row(["Merchant", "updateMerchant()", "PUT", "/api/v1/merchant"], [35, 55, 20, 70])

    pdf.tip_box(
        "Type Safety End-to-End",
        "Each endpoint function specifies its return type via the generic\n"
        "parameter: request<Session[]>('/api/v1/sessions'). TypeScript\n"
        "then enforces correct usage in every component that consumes the\n"
        "data. A type mismatch is caught at compile time, not in production."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 4 - Custom React Hooks
# ─────────────────────────────────────────────────────────

def _ch04(pdf: CoursePDF) -> None:
    pdf.chapter_title("4", "Custom React Hooks")

    pdf.section_title("4.1", "The useQuery Hook")
    pdf.body(
        "The useQuery hook is the backbone of all data fetching in the application. It provides "
        "an SWR-like (stale-while-revalidate) pattern without any external dependencies. The "
        "hook manages loading states, error handling, caching, and automatic cancellation."
    )
    pdf.code_block(
        "interface QueryResult<T> {\n"
        "  data: T | null;\n"
        "  loading: boolean;\n"
        "  error: string | null;\n"
        "  refetch: () => void;\n"
        "}\n"
        "\n"
        "function useQuery<T>(\n"
        "  key: string,\n"
        "  fetcher: () => Promise<T>,\n"
        "  deps: unknown[] = []\n"
        "): QueryResult<T> { ... }"
    )
    pdf.body(
        "The hook accepts three parameters: a cache key string, a fetcher function that returns "
        "a promise, and an optional dependency array. It returns an object with data, loading, "
        "error, and a refetch function."
    )

    pdf.section_title("4.2", "In-Memory Cache System")
    pdf.body(
        "The cache is a module-level Map that persists across renders but not across page "
        "refreshes. Each entry stores the data and a timestamp. Entries older than 30 seconds "
        "are considered stale and trigger a re-fetch."
    )
    pdf.code_block(
        "const CACHE_TTL = 30_000; // 30 seconds\n"
        "const MAX_CACHE = 100;    // Maximum entries\n"
        "\n"
        "interface CacheEntry<T> {\n"
        "  data: T;\n"
        "  ts: number;\n"
        "}\n"
        "\n"
        "const cache = new Map<string, CacheEntry<unknown>>();\n"
        "\n"
        "function pruneCache() {\n"
        "  if (cache.size > MAX_CACHE) {\n"
        "    // Delete oldest entries (LRU approximation)\n"
        "    const oldest = [...cache.entries()]\n"
        "      .sort((a, b) => a[1].ts - b[1].ts)\n"
        "      .slice(0, cache.size - MAX_CACHE);\n"
        "    oldest.forEach(([k]) => cache.delete(k));\n"
        "  }\n"
        "}"
    )

    pdf.tip_box(
        "Why Module-Level Cache?",
        "By defining the cache outside any component, it becomes a singleton\n"
        "shared across all useQuery instances. This means navigating between\n"
        "pages reuses cached data, providing instant page transitions for\n"
        "recently visited routes. The 30s TTL prevents stale data."
    )

    pdf.section_title("4.3", "The fetcherRef Pattern")
    pdf.body(
        "A subtle but critical pattern in useQuery is the fetcherRef. The fetcher function "
        "often captures state variables in its closure (like filter values). If we put the "
        "fetcher directly in the useEffect dependency array, it would cause infinite re-renders "
        "because functions are recreated on every render."
    )
    pdf.code_block(
        "const fetcherRef = useRef(fetcher);\n"
        "fetcherRef.current = fetcher;\n"
        "\n"
        "useEffect(() => {\n"
        "  let cancelled = false;\n"
        "\n"
        "  // Use fetcherRef.current so the effect doesn't\n"
        "  // depend on the fetcher identity\n"
        "  fetcherRef.current().then(data => {\n"
        "    if (!cancelled) {\n"
        "      setData(data);\n"
        "      cache.set(key, { data, ts: Date.now() });\n"
        "      pruneCache();\n"
        "    }\n"
        "  });\n"
        "\n"
        "  return () => { cancelled = true; };\n"
        "}, [key, depsKey, tick]);"
    )

    pdf.warn_box(
        "Common Pitfall: Stale Closures",
        "Without fetcherRef, the useEffect would close over an old version\n"
        "of the fetcher function. When the effect fires, it would use stale\n"
        "filter values. The ref always points to the latest function, solving\n"
        "this classic React hooks gotcha."
    )

    pdf.section_title("4.4", "Dependency Tracking via JSON.stringify")
    pdf.body(
        "The deps array is serialized to a string using JSON.stringify, creating a stable "
        "dependency key. This allows useQuery to detect when filter parameters change without "
        "relying on object reference equality."
    )
    pdf.code_block(
        "// Inside useQuery:\n"
        "const depsKey = JSON.stringify(deps);\n"
        "\n"
        "// Used in useEffect dependency array:\n"
        "useEffect(() => { ... }, [key, depsKey, tick]);\n"
        "\n"
        "// Usage in a component:\n"
        "const { data } = useQuery(\n"
        "  'sessions',\n"
        "  () => getSessions(filters),\n"
        "  [filters.outcome, filters.device, filters.page]\n"
        ");"
    )

    pdf.section_title("4.5", "Cancellation on Unmount")
    pdf.body(
        "The 'let cancelled = false' pattern prevents state updates after a component unmounts. "
        "When the user navigates away, the cleanup function sets cancelled = true. Any pending "
        "API response will be ignored, preventing React's 'setState on unmounted component' "
        "warning."
    )

    pdf.section_title("4.6", "Manual Refetch")
    pdf.body(
        "The refetch function increments a tick counter, which is in the useEffect dependency "
        "array. This triggers a re-fetch without changing the cache key or dependencies."
    )
    pdf.code_block(
        "const [tick, setTick] = useState(0);\n"
        "const refetch = useCallback(() => setTick(t => t + 1), []);\n"
        "\n"
        "// Returned to the caller:\n"
        "return { data, loading, error, refetch };"
    )


# ─────────────────────────────────────────────────────────
#  Chapter 5 - Dashboard Layout & Navigation
# ─────────────────────────────────────────────────────────

def _ch05(pdf: CoursePDF) -> None:
    pdf.chapter_title("5", "Dashboard Layout & Navigation (CONV-51)")

    pdf.section_title("5.1", "DashboardShell Component")
    pdf.body(
        "The DashboardShell is the outermost layout component for all dashboard pages. It "
        "provides a responsive sidebar and main content area. The shell is used in the "
        "dashboard/layout.tsx file, which wraps all child routes."
    )
    pdf.code_block(
        "// dashboard/layout.tsx\n"
        "import DashboardShell from '@/components/layout/DashboardShell';\n"
        "\n"
        "export default function DashboardLayout({\n"
        "  children,\n"
        "}: {\n"
        "  children: React.ReactNode;\n"
        "}) {\n"
        "  return <DashboardShell>{children}</DashboardShell>;\n"
        "}"
    )
    pdf.body(
        "The DashboardShell renders a flex container with the Sidebar on the left and the "
        "children content area on the right. On mobile viewports, the sidebar collapses into "
        "a hamburger menu."
    )
    pdf.code_block(
        "// DashboardShell.tsx (simplified)\n"
        "export default function DashboardShell({\n"
        "  children\n"
        "}: { children: React.ReactNode }) {\n"
        "  const [open, setOpen] = useState(false);\n"
        "\n"
        "  return (\n"
        "    <div className=\"flex h-screen bg-[hsl(var(--background))]\">\n"
        "      <Sidebar open={open} onClose={() => setOpen(false)} />\n"
        "      <div className=\"flex-1 overflow-auto\">\n"
        "        <header className=\"md:hidden p-4\">\n"
        "          <button onClick={() => setOpen(true)}>Menu</button>\n"
        "        </header>\n"
        "        <main className=\"p-6\">{children}</main>\n"
        "      </div>\n"
        "    </div>\n"
        "  );\n"
        "}"
    )

    pdf.section_title("5.2", "Sidebar Navigation")
    pdf.body(
        "The Sidebar component renders the EmoraTest logo, navigation links, and handles "
        "active state highlighting. It uses Next.js usePathname() to determine which link is "
        "currently active."
    )
    pdf.code_block(
        "// Sidebar.tsx navigation items\n"
        "const NAV_ITEMS = [\n"
        "  { href: '/dashboard', label: 'Overview', icon: HomeIcon },\n"
        "  { href: '/dashboard/sessions', label: 'Sessions', icon: UsersIcon },\n"
        "  { href: '/dashboard/analytics', label: 'Analytics', icon: ChartIcon },\n"
        "  { href: '/dashboard/experiments', label: 'Experiments', icon: FlaskIcon },\n"
        "  { href: '/dashboard/interventions', label: 'Interventions' },\n"
        "  { href: '/dashboard/settings', label: 'Settings', icon: GearIcon },\n"
        "];"
    )
    pdf.body(
        "Each navigation item is a Next.js Link component with conditional styling. The active "
        "state uses bg-[hsl(var(--primary)/0.1)] for a subtle highlight and text-[hsl(var(--primary))] "
        "for the text color."
    )

    pdf.tip_box(
        "Next.js Image priority Prop",
        "The Sidebar logo uses <Image priority /> to tell Next.js to\n"
        "preload this image. Since the logo is above the fold on every page,\n"
        "it impacts Largest Contentful Paint (LCP). The priority prop adds\n"
        "a <link rel='preload'> to the document head."
    )

    pdf.section_title("5.3", "Responsive Design Strategy")
    pdf.body(
        "The dashboard uses Tailwind's responsive prefixes (md:, lg:) to adapt the layout. "
        "The sidebar is hidden on mobile (hidden md:flex) and the hamburger menu appears "
        "only on small screens (md:hidden). This approach avoids JavaScript-based responsive "
        "logic in favor of CSS media queries."
    )
    pdf.numbered(1, "Mobile (< 768px): Sidebar hidden, hamburger button visible, full-width content.")
    pdf.numbered(2, "Tablet (768px+): Sidebar visible as narrow strip with icons only.")
    pdf.numbered(3, "Desktop (1024px+): Full sidebar with labels, spacious content area.")


# ─────────────────────────────────────────────────────────
#  Chapter 6 - Reusable UI Component Library
# ─────────────────────────────────────────────────────────

def _ch06(pdf: CoursePDF) -> None:
    pdf.chapter_title("6", "Reusable UI Component Library")

    pdf.section_title("6.1", "Card & CardHeader / CardBody")
    pdf.body(
        "The Card component is the fundamental container used throughout the dashboard. It "
        "provides consistent rounded borders, shadows, and padding. CardHeader and CardBody "
        "subcomponents handle internal spacing."
    )
    pdf.code_block(
        "// Card.tsx\n"
        "export function Card({\n"
        "  children, className = ''\n"
        "}: { children: React.ReactNode; className?: string }) {\n"
        "  return (\n"
        "    <div className={clsx(\n"
        "      'rounded-2xl border border-[hsl(var(--border))]',\n"
        "      'bg-[hsl(var(--background))] shadow-sm',\n"
        "      className\n"
        "    )}>\n"
        "      {children}\n"
        "    </div>\n"
        "  );\n"
        "}\n"
        "\n"
        "export function CardHeader({ children }: Props) {\n"
        "  return <div className=\"px-6 py-4 border-b\">{children}</div>;\n"
        "}\n"
        "\n"
        "export function CardBody({ children }: Props) {\n"
        "  return <div className=\"px-6 py-4\">{children}</div>;\n"
        "}"
    )

    pdf.section_title("6.2", "StatCard with Memoization")
    pdf.body(
        "StatCard displays a key metric with a label, value, and optional trend indicator. "
        "It is wrapped in React.memo to prevent unnecessary re-renders when parent components "
        "update but the stat values remain the same."
    )
    pdf.code_block(
        "// StatCard.tsx\n"
        "interface StatCardProps {\n"
        "  label: string;\n"
        "  value: string | number;\n"
        "  trend?: 'up' | 'down' | 'neutral';\n"
        "  trendValue?: string;\n"
        "}\n"
        "\n"
        "const StatCard = memo(function StatCard({\n"
        "  label, value, trend, trendValue\n"
        "}: StatCardProps) {\n"
        "  return (\n"
        "    <div className=\"relative overflow-hidden rounded-2xl ...\">\n"
        "      {/* Animated gradient blob for visual interest */}\n"
        "      <div className=\"absolute -right-4 -top-4 h-24 w-24\n"
        "        rounded-full bg-gradient-to-br from-[hsl(var(--primary)/0.2)]\n"
        "        to-transparent will-change-transform\" />\n"
        "      <p className=\"text-sm text-muted\">{label}</p>\n"
        "      <p className=\"text-2xl font-bold\">{value}</p>\n"
        "      {trend && <TrendBadge dir={trend} val={trendValue} />}\n"
        "    </div>\n"
        "  );\n"
        "});"
    )

    pdf.tip_box(
        "will-change-transform for GPU Compositing",
        "The gradient blob uses will-change-transform to hint to the browser\n"
        "that this element will be animated. This promotes it to its own GPU\n"
        "compositing layer, preventing repaints of the entire card when the\n"
        "blob animates. Use sparingly - overuse wastes GPU memory."
    )

    pdf.section_title("6.3", "Badge Component")
    pdf.body(
        "Badge renders a small colored label, commonly used for session outcomes, experiment "
        "statuses, and risk levels. It supports 6 variants through a variant prop."
    )
    cols = [("Variant", 35), ("Background", 50), ("Text Color", 45), ("Use Case", 50)]
    pdf.table_header(cols)
    pdf.table_row(["default", "gray-100", "gray-800", "General labels"], [35, 50, 45, 50])
    pdf.table_row(["success", "green-100", "green-800", "Converted, active"], [35, 50, 45, 50])
    pdf.table_row(["warning", "amber-100", "amber-800", "Medium risk"], [35, 50, 45, 50])
    pdf.table_row(["destructive", "red-100", "red-800", "High risk, failed"], [35, 50, 45, 50])
    pdf.table_row(["outline", "transparent", "gray-700", "Subtle tags"], [35, 50, 45, 50])
    pdf.table_row(["primary", "primary-100", "primary-800", "Active filters"], [35, 50, 45, 50])

    pdf.section_title("6.4", "Spinner, ErrorBox, and EmptyState")
    pdf.body(
        "Three utility components handle loading, error, and empty states consistently across "
        "all pages."
    )
    pdf.subsection("Spinner")
    pdf.body(
        "A CSS-animated spinning circle used as a loading indicator. It uses Tailwind's "
        "animate-spin utility class with a border-based spinner design."
    )
    pdf.subsection("ErrorBox with Retry")
    pdf.body(
        "ErrorBox displays an error message with an optional retry button. The retry button "
        "calls the refetch function from useQuery, enabling users to recover from transient "
        "network errors without refreshing the page."
    )
    pdf.code_block(
        "// ErrorBox.tsx\n"
        "export function ErrorBox({\n"
        "  message, onRetry\n"
        "}: { message: string; onRetry?: () => void }) {\n"
        "  return (\n"
        "    <div className=\"rounded-xl border-destructive bg-red-50 p-4\">\n"
        "      <p className=\"text-destructive\">{message}</p>\n"
        "      {onRetry && (\n"
        "        <button onClick={onRetry}\n"
        "          className=\"mt-2 text-sm underline\">Retry</button>\n"
        "      )}\n"
        "    </div>\n"
        "  );\n"
        "}"
    )
    pdf.subsection("EmptyState")
    pdf.body(
        "EmptyState renders a centered message when a query returns no results. It accepts "
        "a message prop and optionally an icon. Used in sessions list, experiments, and "
        "interventions pages."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 7 - Overview Dashboard Page
# ─────────────────────────────────────────────────────────

def _ch07(pdf: CoursePDF) -> None:
    pdf.chapter_title("7", "Overview Dashboard Page")

    pdf.section_title("7.1", "Page Structure")
    pdf.body(
        "The overview page (/dashboard) is the landing page that provides a high-level summary "
        "of the merchant's conversion performance. It consists of three sections: KPI cards at "
        "the top, a conversion funnel bar chart, and a risk distribution pie chart."
    )
    pdf.code_block(
        "// dashboard/page.tsx\n"
        "'use client';\n"
        "\n"
        "import { useQuery } from '@/lib/hooks';\n"
        "import { getOverviewKPIs, getConversionFunnel,\n"
        "         getRiskDistribution } from '@/lib/api';\n"
        "import { StatCard } from '@/components/ui/StatCard';\n"
        "import { LazyBarChart, LazyPieChart,\n"
        "         LazyResponsiveContainer } from\n"
        "         '@/components/charts/LazyRecharts';\n"
        "\n"
        "export default function OverviewPage() {\n"
        "  const kpis = useQuery('overview-kpis', getOverviewKPIs);\n"
        "  const funnel = useQuery('funnel', getConversionFunnel);\n"
        "  const risk = useQuery('risk-dist', getRiskDistribution);\n"
        "  // ... render\n"
        "}"
    )

    pdf.section_title("7.2", "KPI StatCards")
    pdf.body(
        "The top section renders 4 StatCard components in a responsive grid. Each card shows "
        "a key metric: total sessions, conversion rate, average risk score, and active "
        "interventions. The grid uses Tailwind's grid-cols system for responsive layout."
    )
    pdf.code_block(
        "<div className=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6\">\n"
        "  <StatCard label=\"Total Sessions\" value={kpis.data?.total_sessions}\n"
        "    trend=\"up\" trendValue=\"+12%\" />\n"
        "  <StatCard label=\"Conversion Rate\" value={fmt.pct(kpis.data?.rate)}\n"
        "    trend=\"up\" trendValue=\"+3.2%\" />\n"
        "  <StatCard label=\"Avg Risk Score\" value={fmt.dec(kpis.data?.risk)}\n"
        "    trend=\"down\" trendValue=\"-0.05\" />\n"
        "  <StatCard label=\"Active Interventions\"\n"
        "    value={kpis.data?.active_interventions} />\n"
        "</div>"
    )

    pdf.section_title("7.3", "Lazy-Loaded Recharts")
    pdf.body(
        "Charts are loaded dynamically using next/dynamic to avoid including the entire "
        "Recharts library (~400KB) in the initial JavaScript bundle. This is one of the most "
        "impactful performance optimizations in the application."
    )
    pdf.code_block(
        "// components/charts/LazyRecharts.tsx\n"
        "import dynamic from 'next/dynamic';\n"
        "\n"
        "export const LazyBarChart = dynamic(\n"
        "  () => import('recharts').then(m => m.BarChart),\n"
        "  { ssr: false }\n"
        ");\n"
        "export const LazyPieChart = dynamic(\n"
        "  () => import('recharts').then(m => m.PieChart),\n"
        "  { ssr: false }\n"
        ");\n"
        "export const LazyLineChart = dynamic(\n"
        "  () => import('recharts').then(m => m.LineChart),\n"
        "  { ssr: false }\n"
        ");\n"
        "export const LazyResponsiveContainer = dynamic(\n"
        "  () => import('recharts').then(m => m.ResponsiveContainer),\n"
        "  { ssr: false }\n"
        ");"
    )

    pdf.tip_box(
        "Why ssr: false?",
        "Recharts uses DOM APIs (SVG, getBBox) that are not available during\n"
        "server-side rendering. Setting ssr: false tells Next.js to only\n"
        "load and render these components on the client. The page first\n"
        "renders without charts, then they appear after the JS chunk loads."
    )

    pdf.section_title("7.4", "Shared Chart Styles")
    pdf.body(
        "To prevent re-renders caused by inline style objects, the chart tooltip and tick "
        "styles are defined as module-level constants. In React, an inline object like "
        "style={{ fontSize: 12 }} creates a new reference on every render, causing the "
        "Recharts component to re-render unnecessarily."
    )
    pdf.code_block(
        "// Defined outside any component:\n"
        "export const chartTooltipStyle = {\n"
        "  borderRadius: '8px',\n"
        "  border: '1px solid hsl(var(--border))',\n"
        "  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',\n"
        "};\n"
        "\n"
        "export const tickStyle = {\n"
        "  fontSize: 12,\n"
        "  fill: 'hsl(var(--muted-foreground))',\n"
        "};"
    )

    pdf.section_title("7.5", "Conversion Funnel Chart")
    pdf.body(
        "The funnel chart uses LazyBarChart to display the conversion stages: page_view, "
        "add_to_cart, checkout, and purchase. Each bar represents the count at that stage, "
        "visually showing where users drop off."
    )

    pdf.section_title("7.6", "Risk Distribution Pie Chart")
    pdf.body(
        "The risk distribution pie chart uses LazyPieChart to show the breakdown of sessions "
        "by risk level (low, medium, high). Colors are mapped to the design system: green for "
        "low, amber for medium, red for high."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 8 - Sessions List & Filtering
# ─────────────────────────────────────────────────────────

def _ch08(pdf: CoursePDF) -> None:
    pdf.chapter_title("8", "Sessions List & Filtering (CONV-52)")

    pdf.section_title("8.1", "Page Overview")
    pdf.body(
        "The sessions page (/dashboard/sessions) displays a filterable, paginated table of all "
        "visitor sessions. It demonstrates several important React patterns: memoized filter "
        "components, stable options arrays, and dependency-tracked data fetching."
    )

    pdf.section_title("8.2", "Filter State Management")
    pdf.body(
        "All filter values are stored in a single state object. This keeps related state "
        "together and makes it easy to serialize for the useQuery dependency array."
    )
    pdf.code_block(
        "interface Filters {\n"
        "  outcome: string;\n"
        "  device: string;\n"
        "  risk: string;\n"
        "  dateFrom: string;\n"
        "  dateTo: string;\n"
        "  page: number;\n"
        "}\n"
        "\n"
        "const [filters, setFilters] = useState<Filters>({\n"
        "  outcome: '', device: '', risk: '',\n"
        "  dateFrom: '', dateTo: '', page: 1,\n"
        "});"
    )

    pdf.section_title("8.3", "Memoized Filter Components")
    pdf.body(
        "The FilterSelect and FilterInput components are wrapped in React.memo to prevent "
        "re-renders when unrelated filters change. Without memo, changing the 'outcome' filter "
        "would re-render the 'device' filter component unnecessarily."
    )
    pdf.code_block(
        "const FilterSelect = memo(function FilterSelect({\n"
        "  label, value, onChange, options\n"
        "}: FilterSelectProps) {\n"
        "  return (\n"
        "    <div>\n"
        "      <label className=\"text-sm font-medium\">{label}</label>\n"
        "      <select value={value} onChange={e => onChange(e.target.value)}\n"
        "        className=\"rounded-lg border px-3 py-2\">\n"
        "        <option value=\"\">All</option>\n"
        "        {options.map(o =>\n"
        "          <option key={o} value={o}>{o}</option>)}\n"
        "      </select>\n"
        "    </div>\n"
        "  );\n"
        "});"
    )

    pdf.section_title("8.4", "Stable Options Arrays")
    pdf.body(
        "The options for each filter dropdown are defined outside the component as module-level "
        "constants. This is a critical optimization - if the array were defined inside the "
        "component, React.memo would see a new reference on every render and re-render anyway."
    )
    pdf.code_block(
        "// Defined OUTSIDE the component:\n"
        "const OUTCOME_OPTIONS = ['converted', 'abandoned', 'bounced'];\n"
        "const DEVICE_OPTIONS = ['desktop', 'mobile', 'tablet'];\n"
        "const RISK_OPTIONS = ['low', 'medium', 'high'];\n"
        "\n"
        "// Inside render:\n"
        "<FilterSelect\n"
        "  label=\"Outcome\"\n"
        "  value={filters.outcome}\n"
        "  onChange={v => setFilters(f => ({ ...f, outcome: v, page: 1 }))}\n"
        "  options={OUTCOME_OPTIONS}  // stable reference!\n"
        "/>"
    )

    pdf.warn_box(
        "Gotcha: Filter Change Resets Page",
        "Notice that changing any filter resets page to 1. Without this,\n"
        "the user could be on page 5, apply a filter that returns only\n"
        "2 pages of results, and see an empty page. Always reset pagination\n"
        "when filters change."
    )

    pdf.section_title("8.5", "Pagination")
    pdf.body(
        "Pagination uses a memoized PaginationBtn component and calculates total pages from "
        "the API response. The page number is part of the filter state, so changing it triggers "
        "a useQuery refetch through the dependency array."
    )
    pdf.code_block(
        "const PaginationBtn = memo(function PaginationBtn({\n"
        "  page, current, onClick\n"
        "}: { page: number; current: boolean; onClick: () => void }) {\n"
        "  return (\n"
        "    <button\n"
        "      onClick={onClick}\n"
        "      className={clsx(\n"
        "        'px-3 py-1 rounded-lg text-sm',\n"
        "        current\n"
        "          ? 'bg-[hsl(var(--primary))] text-white'\n"
        "          : 'bg-[hsl(var(--secondary))]'\n"
        "      )}\n"
        "    >\n"
        "      {page}\n"
        "    </button>\n"
        "  );\n"
        "});"
    )

    pdf.section_title("8.6", "Session Table & Row Links")
    pdf.body(
        "Each table row is a Next.js Link to the session detail page. The row displays session ID, "
        "visitor ID, outcome (as a Badge), risk score, device type, and created date. Clicking "
        "navigates to /dashboard/sessions/[id]."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 9 - Session Detail View
# ─────────────────────────────────────────────────────────

def _ch09(pdf: CoursePDF) -> None:
    pdf.chapter_title("9", "Session Detail View (CONV-53)")

    pdf.section_title("9.1", "Page Structure")
    pdf.body(
        "The session detail page (/dashboard/sessions/[id]) provides a deep dive into a single "
        "visitor session. It displays three sections: behavioral features, intervention "
        "recommendations, and an event timeline. The page uses the Next.js dynamic route "
        "parameter [id] to fetch session-specific data."
    )
    pdf.code_block(
        "// sessions/[id]/page.tsx\n"
        "'use client';\n"
        "\n"
        "import { useParams } from 'next/navigation';\n"
        "\n"
        "export default function SessionDetailPage() {\n"
        "  const { id } = useParams<{ id: string }>();\n"
        "\n"
        "  const session = useQuery(\n"
        "    `session-${id}`,\n"
        "    () => getSession(id)\n"
        "  );\n"
        "  const events = useQuery(\n"
        "    `session-events-${id}`,\n"
        "    () => getSessionEvents(id)\n"
        "  );\n"
        "  // ...\n"
        "}"
    )

    pdf.section_title("9.2", "useCallback for Fetcher Functions")
    pdf.body(
        "The fetcher functions are wrapped in useCallback to maintain stable references. While "
        "the fetcherRef in useQuery already handles stale closures, useCallback prevents "
        "unnecessary work in the hook itself."
    )
    pdf.code_block(
        "const fetchSession = useCallback(\n"
        "  () => getSession(id),\n"
        "  [id]\n"
        ");\n"
        "\n"
        "const fetchEvents = useCallback(\n"
        "  () => getSessionEvents(id),\n"
        "  [id]\n"
        ");\n"
        "\n"
        "const session = useQuery(`session-${id}`, fetchSession);\n"
        "const events = useQuery(`events-${id}`, fetchEvents);"
    )

    pdf.section_title("9.3", "Behavioral Features Grid")
    pdf.body(
        "The features grid displays ML-extracted behavioral signals from the session. Each "
        "feature is shown in a MetricBox or Feature component with its name and value."
    )
    pdf.code_block(
        "// Memoized feature display components\n"
        "const MetricBox = memo(function MetricBox({\n"
        "  label, value\n"
        "}: { label: string; value: string | number }) {\n"
        "  return (\n"
        "    <div className=\"rounded-xl bg-[hsl(var(--secondary))] p-4\">\n"
        "      <p className=\"text-xs text-muted-foreground\">{label}</p>\n"
        "      <p className=\"text-lg font-semibold\">{value}</p>\n"
        "    </div>\n"
        "  );\n"
        "});\n"
        "\n"
        "const Feature = memo(function Feature({\n"
        "  name, value\n"
        "}: { name: string; value: number }) {\n"
        "  return (\n"
        "    <div className=\"flex justify-between py-2 border-b\">\n"
        "      <span>{name}</span>\n"
        "      <span className=\"font-mono\">{value.toFixed(3)}</span>\n"
        "    </div>\n"
        "  );\n"
        "});"
    )

    pdf.section_title("9.4", "Intervention Recommendations")
    pdf.body(
        "Based on the session's risk score and behavioral features, the backend suggests "
        "intervention strategies. These are displayed as cards with the intervention type, "
        "confidence score, and expected impact."
    )

    pdf.section_title("9.5", "Event Timeline Table")
    pdf.body(
        "The bottom section shows a chronological table of all events in the session (page views, "
        "clicks, scrolls, cart actions, etc.). Each row shows the event type, timestamp, and "
        "associated metadata."
    )
    pdf.code_block(
        "<table className=\"w-full text-sm\">\n"
        "  <thead>\n"
        "    <tr className=\"border-b text-muted-foreground\">\n"
        "      <th className=\"text-left py-2\">Event</th>\n"
        "      <th className=\"text-left py-2\">Timestamp</th>\n"
        "      <th className=\"text-left py-2\">Details</th>\n"
        "    </tr>\n"
        "  </thead>\n"
        "  <tbody>\n"
        "    {events.data?.map((evt, i) => (\n"
        "      <tr key={i} className=\"border-b\">\n"
        "        <td className=\"py-2\">\n"
        "          <Badge>{evt.event_type}</Badge>\n"
        "        </td>\n"
        "        <td>{formatTime(evt.timestamp)}</td>\n"
        "        <td>{JSON.stringify(evt.metadata)}</td>\n"
        "      </tr>\n"
        "    ))}\n"
        "  </tbody>\n"
        "</table>"
    )

    pdf.tip_box(
        "Cache Keys Include the Session ID",
        "Notice that cache keys like 'session-abc123' and 'events-abc123'\n"
        "are unique per session. This means navigating between sessions\n"
        "creates separate cache entries, allowing instant back-navigation\n"
        "to a previously viewed session within the 30s TTL window."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 10 - Analytics Dashboard
# ─────────────────────────────────────────────────────────

def _ch10(pdf: CoursePDF) -> None:
    pdf.chapter_title("10", "Analytics Dashboard (CONV-54)")

    pdf.section_title("10.1", "Page Layout")
    pdf.body(
        "The analytics page (/dashboard/analytics) is the most chart-heavy page in the "
        "application. It contains four visualization sections: conversion funnel, friction "
        "hotspots, risk distribution, and cohort analysis. Each section fetches its data "
        "independently via useQuery."
    )
    pdf.code_block(
        "// analytics/page.tsx\n"
        "'use client';\n"
        "\n"
        "export default function AnalyticsPage() {\n"
        "  const funnel = useQuery('analytics-funnel', getConversionFunnel);\n"
        "  const friction = useQuery('analytics-friction', getFrictionPoints);\n"
        "  const riskDist = useQuery('analytics-risk', getRiskDistribution);\n"
        "  const [cohortDim, setCohortDim] = useState('device');\n"
        "  const cohorts = useQuery(\n"
        "    `analytics-cohorts-${cohortDim}`,\n"
        "    () => getCohortAnalysis(cohortDim),\n"
        "    [cohortDim]\n"
        "  );\n"
        "  // ...\n"
        "}"
    )

    pdf.section_title("10.2", "Conversion Funnel (Bar Chart)")
    pdf.body(
        "The funnel visualization uses LazyBarChart with horizontal bars showing progression "
        "through conversion stages. Each bar represents a stage count, with color intensity "
        "decreasing to visually convey the funnel narrowing."
    )

    pdf.section_title("10.3", "Friction Hotspot Table")
    pdf.body(
        "The friction analysis identifies pages and interactions where users experience the "
        "most difficulty. Data is displayed in a table sorted by friction score, with each row "
        "showing the page URL, average time on page, rage click count, and drop-off rate."
    )
    pdf.code_block(
        "// Friction hotspots table\n"
        "<table className=\"w-full text-sm\">\n"
        "  <thead>\n"
        "    <tr className=\"text-muted-foreground border-b\">\n"
        "      <th className=\"text-left py-2\">Page</th>\n"
        "      <th className=\"text-right py-2\">Friction Score</th>\n"
        "      <th className=\"text-right py-2\">Avg Time (s)</th>\n"
        "      <th className=\"text-right py-2\">Drop-off %</th>\n"
        "    </tr>\n"
        "  </thead>\n"
        "  <tbody>\n"
        "    {friction.data?.map((row, i) => (\n"
        "      <tr key={i} className=\"border-b\">\n"
        "        <td className=\"py-2\">{row.page}</td>\n"
        "        <td className=\"text-right\">{row.score.toFixed(2)}</td>\n"
        "        <td className=\"text-right\">{row.avg_time}</td>\n"
        "        <td className=\"text-right\">{fmt.pct(row.dropoff)}</td>\n"
        "      </tr>\n"
        "    ))}\n"
        "  </tbody>\n"
        "</table>"
    )

    pdf.section_title("10.4", "Risk Distribution (Bar Chart)")
    pdf.body(
        "Unlike the overview's pie chart, the analytics page uses a bar chart for risk "
        "distribution to show more precise counts. Bars are color-coded: green for low risk, "
        "amber for medium, and red for high."
    )

    pdf.section_title("10.5", "Cohort Analysis with Dimension Selector")
    pdf.body(
        "The cohort analysis section is the most interactive chart. Users can select a "
        "dimension (device, browser, country, traffic source) to group sessions and compare "
        "conversion rates across cohorts."
    )
    pdf.code_block(
        "// Cohort dimension selector\n"
        "const COHORT_DIMENSIONS = ['device', 'browser', 'country', 'source'];\n"
        "\n"
        "<select\n"
        "  value={cohortDim}\n"
        "  onChange={e => setCohortDim(e.target.value)}\n"
        "  className=\"rounded-lg border px-3 py-2\"\n"
        ">\n"
        "  {COHORT_DIMENSIONS.map(d =>\n"
        "    <option key={d} value={d}>{d}</option>)}\n"
        "</select>"
    )
    pdf.body(
        "Changing the dimension updates the cohortDim state, which changes the useQuery cache "
        "key (analytics-cohorts-device vs analytics-cohorts-browser), triggering a new API call. "
        "Previously fetched dimensions are cached for 30 seconds."
    )

    pdf.section_title("10.6", "Memoized Tooltip Formatters")
    pdf.body(
        "Recharts accepts formatter functions for tooltips and axis labels. These are wrapped "
        "in useMemo to prevent re-renders:"
    )
    pdf.code_block(
        "const tooltipFormatter = useMemo(\n"
        "  () => (value: number) => [fmt.number(value), 'Count'],\n"
        "  []\n"
        ");\n"
        "\n"
        "const pctFormatter = useMemo(\n"
        "  () => (value: number) => [fmt.pct(value), 'Rate'],\n"
        "  []\n"
        ");\n"
        "\n"
        "// Used in Recharts:\n"
        "<Tooltip formatter={tooltipFormatter}\n"
        "  contentStyle={chartTooltipStyle} />"
    )

    pdf.tip_box(
        "Combo Charts: Line + Bar",
        "The cohort analysis uses a composed chart (ComposedChart from\n"
        "Recharts) that combines bars for session count and a line for\n"
        "conversion rate. This dual-axis visualization lets merchants\n"
        "compare volume and performance in a single view."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 11 - Experiments Management
# ─────────────────────────────────────────────────────────

def _ch11(pdf: CoursePDF) -> None:
    pdf.chapter_title("11", "Experiments Management (CONV-55)")

    pdf.section_title("11.1", "Page Architecture")
    pdf.body(
        "The experiments page (/dashboard/experiments) provides full CRUD (Create, Read, "
        "Update, Delete) capabilities for A/B experiments. The page is composed of three "
        "main sub-components: a create form, experiment cards, and a stats panel."
    )
    pdf.code_block(
        "// experiments/page.tsx structure\n"
        "'use client';\n"
        "\n"
        "export default function ExperimentsPage() {\n"
        "  const [showCreate, setShowCreate] = useState(false);\n"
        "  const [selectedId, setSelectedId] = useState<string | null>(null);\n"
        "  const experiments = useQuery('experiments', getExperiments);\n"
        "\n"
        "  return (\n"
        "    <div>\n"
        "      <header className=\"flex justify-between items-center mb-6\">\n"
        "        <h1>Experiments</h1>\n"
        "        <button onClick={() => setShowCreate(true)}>\n"
        "          + New Experiment\n"
        "        </button>\n"
        "      </header>\n"
        "\n"
        "      {showCreate && <CreateForm onClose={() => {\n"
        "        setShowCreate(false);\n"
        "        experiments.refetch();\n"
        "      }} />}\n"
        "\n"
        "      <div className=\"grid gap-4\">\n"
        "        {experiments.data?.map(exp =>\n"
        "          <ExperimentCard key={exp.id} experiment={exp}\n"
        "            onSelect={() => setSelectedId(exp.id)} />\n"
        "        )}\n"
        "      </div>\n"
        "\n"
        "      {selectedId && <StatsPanel id={selectedId}\n"
        "        onClose={() => setSelectedId(null)} />}\n"
        "    </div>\n"
        "  );\n"
        "}"
    )

    pdf.section_title("11.2", "CreateForm Component")
    pdf.body(
        "The CreateForm collects experiment details: name, description, hypothesis, variant "
        "names, and traffic allocation percentage. On submit, it calls the createExperiment() "
        "API function and triggers a refetch of the experiments list."
    )
    pdf.code_block(
        "// CreateForm submit handler\n"
        "const handleSubmit = async (e: React.FormEvent) => {\n"
        "  e.preventDefault();\n"
        "  setSubmitting(true);\n"
        "  try {\n"
        "    await createExperiment({\n"
        "      name: form.name,\n"
        "      description: form.description,\n"
        "      hypothesis: form.hypothesis,\n"
        "      variants: form.variants.split(',').map(v => v.trim()),\n"
        "      traffic_pct: Number(form.traffic_pct),\n"
        "    });\n"
        "    onClose(); // triggers refetch in parent\n"
        "  } catch (err) {\n"
        "    setError(err instanceof ApiError ? err.detail : 'Failed');\n"
        "  } finally {\n"
        "    setSubmitting(false);\n"
        "  }\n"
        "};"
    )

    pdf.section_title("11.3", "ExperimentCard Component")
    pdf.body(
        "Each experiment is displayed in a card showing its name, status (as a Badge), "
        "creation date, and a button to view stats. The card uses conditional styling based "
        "on experiment status (active, paused, completed)."
    )

    pdf.section_title("11.4", "StatsPanel Component")
    pdf.body(
        "When a user clicks 'View Stats' on an experiment card, the StatsPanel slides in "
        "showing variant-level performance metrics. It fetches data via getExperimentStats(id)."
    )
    pdf.code_block(
        "function StatsPanel({ id, onClose }: StatsPanelProps) {\n"
        "  const stats = useQuery(\n"
        "    `experiment-stats-${id}`,\n"
        "    () => getExperimentStats(id)\n"
        "  );\n"
        "\n"
        "  return (\n"
        "    <Card>\n"
        "      <CardHeader>\n"
        "        <h3>Experiment Results</h3>\n"
        "        <button onClick={onClose}>Close</button>\n"
        "      </CardHeader>\n"
        "      <CardBody>\n"
        "        {stats.data?.variants.map(v => (\n"
        "          <div key={v.name} className=\"flex justify-between\">\n"
        "            <span>{v.name}</span>\n"
        "            <span>Conv: {fmt.pct(v.conversion_rate)}</span>\n"
        "            <span>n={v.sample_size}</span>\n"
        "          </div>\n"
        "        ))}\n"
        "        {stats.data?.winner &&\n"
        "          <Badge variant=\"success\">\n"
        "            Winner: {stats.data.winner}\n"
        "          </Badge>}\n"
        "      </CardBody>\n"
        "    </Card>\n"
        "  );\n"
        "}"
    )

    pdf.tip_box(
        "Refetch Pattern After Mutation",
        "After creating an experiment, we call onClose() which triggers\n"
        "the parent to call experiments.refetch(). This ensures the list\n"
        "shows the new experiment immediately. An alternative is optimistic\n"
        "updates (adding to local state before API confirms), but refetch\n"
        "is simpler and guarantees consistency with the server."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 12 - Interventions Dashboard
# ─────────────────────────────────────────────────────────

def _ch12(pdf: CoursePDF) -> None:
    pdf.chapter_title("12", "Interventions Dashboard (CONV-55)")

    pdf.section_title("12.1", "Page Layout")
    pdf.body(
        "The interventions page (/dashboard/interventions) visualizes the effectiveness of "
        "automated interventions (popups, discounts, urgency messages, etc.) that the system "
        "triggers based on ML risk predictions. The page has two sections: a stacked bar chart "
        "and a detailed statistics table."
    )

    pdf.section_title("12.2", "Stacked Bar Chart")
    pdf.body(
        "The main visualization is a stacked bar chart where each bar represents an "
        "intervention type, and the segments show the outcome breakdown: converted (green), "
        "dismissed (gray), ignored (amber), and bounced (red)."
    )
    pdf.code_block(
        "// Stacked bar chart for interventions\n"
        "<LazyResponsiveContainer width=\"100%\" height={400}>\n"
        "  <LazyBarChart data={interventions.data} layout=\"vertical\">\n"
        "    <XAxis type=\"number\" />\n"
        "    <YAxis type=\"category\" dataKey=\"type\" width={120} />\n"
        "    <Tooltip\n"
        "      formatter={tooltipFormatter}\n"
        "      contentStyle={chartTooltipStyle}\n"
        "    />\n"
        "    <Legend />\n"
        "    <Bar dataKey=\"converted\" stackId=\"a\" fill=\"#22c55e\" />\n"
        "    <Bar dataKey=\"dismissed\" stackId=\"a\" fill=\"#94a3b8\" />\n"
        "    <Bar dataKey=\"ignored\"   stackId=\"a\" fill=\"#f59e0b\" />\n"
        "    <Bar dataKey=\"bounced\"   stackId=\"a\" fill=\"#ef4444\" />\n"
        "  </LazyBarChart>\n"
        "</LazyResponsiveContainer>"
    )

    pdf.tip_box(
        "stackId Groups Bars Together",
        "In Recharts, Bar components with the same stackId are stacked on\n"
        "top of each other instead of placed side by side. This creates a\n"
        "single bar per intervention type showing the proportional outcomes.\n"
        "Remove stackId to get a grouped bar chart instead."
    )

    pdf.section_title("12.3", "Tooltip Formatter")
    pdf.body(
        "The tooltip formatter is memoized to prevent re-renders and formats the count value "
        "with thousand separators."
    )
    pdf.code_block(
        "const tooltipFormatter = useMemo(\n"
        "  () => (value: number, name: string) => [\n"
        "    fmt.number(value),\n"
        "    name.charAt(0).toUpperCase() + name.slice(1),\n"
        "  ],\n"
        "  []\n"
        ");"
    )

    pdf.section_title("12.4", "Intervention Stats Table")
    pdf.body(
        "Below the chart, a detailed table shows per-intervention metrics: total triggers, "
        "conversion rate, average time to convert, dismiss rate, and ROI estimate. This data "
        "comes from the getInterventionStats() endpoint."
    )
    pdf.code_block(
        "// Stats table rendering\n"
        "<table className=\"w-full text-sm\">\n"
        "  <thead>\n"
        "    <tr className=\"border-b\">\n"
        "      <th className=\"text-left py-2\">Intervention</th>\n"
        "      <th className=\"text-right\">Triggers</th>\n"
        "      <th className=\"text-right\">Conv Rate</th>\n"
        "      <th className=\"text-right\">Avg Time</th>\n"
        "      <th className=\"text-right\">Dismiss %</th>\n"
        "    </tr>\n"
        "  </thead>\n"
        "  <tbody>\n"
        "    {stats.data?.map((s, i) => (\n"
        "      <tr key={i} className=\"border-b\">\n"
        "        <td className=\"py-2\">{s.type}</td>\n"
        "        <td className=\"text-right\">{fmt.number(s.triggers)}</td>\n"
        "        <td className=\"text-right\">{fmt.pct(s.conv_rate)}</td>\n"
        "        <td className=\"text-right\">{s.avg_time_s}s</td>\n"
        "        <td className=\"text-right\">{fmt.pct(s.dismiss_rate)}</td>\n"
        "      </tr>\n"
        "    ))}\n"
        "  </tbody>\n"
        "</table>"
    )


# ─────────────────────────────────────────────────────────
#  Chapter 13 - Settings & SDK Key Management
# ─────────────────────────────────────────────────────────

def _ch13(pdf: CoursePDF) -> None:
    pdf.chapter_title("13", "Settings & SDK Key Management")

    pdf.section_title("13.1", "Page Overview")
    pdf.body(
        "The settings page (/dashboard/settings) manages the merchant's SDK key and profile. "
        "It is the only page that writes to localStorage (all other pages only read from it). "
        "The page demonstrates client-side state management without full-page reloads."
    )

    pdf.section_title("13.2", "SDK Key Management")
    pdf.body(
        "The SDK key is the authentication token used in all API requests. The settings page "
        "provides three operations: view the current key, save a new key, and rotate (regenerate) "
        "the key."
    )
    pdf.code_block(
        "// Settings page SDK key management\n"
        "const [sdkKey, setSdkKey] = useState('');\n"
        "const [saved, setSaved] = useState(false);\n"
        "\n"
        "useEffect(() => {\n"
        "  const key = localStorage.getItem('sdkKey') ?? '';\n"
        "  setSdkKey(key);\n"
        "}, []);\n"
        "\n"
        "const handleSave = () => {\n"
        "  localStorage.setItem('sdkKey', sdkKey);\n"
        "  setSaved(true);\n"
        "  setTimeout(() => setSaved(false), 2000);\n"
        "};"
    )

    pdf.tip_box(
        "Client-Side Save Feedback (No Reload!)",
        "An earlier version used window.location.reload() after saving the\n"
        "SDK key. This was replaced with a 'saved' state flag that shows a\n"
        "green checkmark for 2 seconds. This is much better UX - the user\n"
        "gets instant feedback without losing page state."
    )

    pdf.section_title("13.3", "Key Rotation")
    pdf.body(
        "Key rotation calls a backend endpoint to generate a new SDK key. The new key is "
        "automatically saved to localStorage and the input field is updated."
    )
    pdf.code_block(
        "const handleRotate = async () => {\n"
        "  if (!confirm('Rotate SDK key? The old key will stop working.')) {\n"
        "    return;\n"
        "  }\n"
        "  try {\n"
        "    const result = await rotateSdkKey();\n"
        "    setSdkKey(result.sdk_key);\n"
        "    localStorage.setItem('sdkKey', result.sdk_key);\n"
        "    setSaved(true);\n"
        "    setTimeout(() => setSaved(false), 2000);\n"
        "  } catch (err) {\n"
        "    setError('Failed to rotate key');\n"
        "  }\n"
        "};"
    )

    pdf.warn_box(
        "Security: Confirm Before Rotation",
        "Key rotation invalidates the old key immediately. All active SDK\n"
        "integrations will break until updated with the new key. The\n"
        "confirm() dialog prevents accidental rotation. In production,\n"
        "consider a grace period where both keys work."
    )

    pdf.section_title("13.4", "Merchant Profile Display")
    pdf.body(
        "The bottom section of the settings page displays the merchant profile fetched from "
        "the API. This includes the merchant name, plan, created date, and contact email. "
        "It uses the getMerchant() endpoint."
    )
    pdf.code_block(
        "const merchant = useQuery('merchant', getMerchant);\n"
        "\n"
        "<Card>\n"
        "  <CardHeader>Merchant Profile</CardHeader>\n"
        "  <CardBody>\n"
        "    <div className=\"grid grid-cols-2 gap-4\">\n"
        "      <div>\n"
        "        <p className=\"text-sm text-muted\">Name</p>\n"
        "        <p className=\"font-medium\">{merchant.data?.name}</p>\n"
        "      </div>\n"
        "      <div>\n"
        "        <p className=\"text-sm text-muted\">Plan</p>\n"
        "        <Badge variant=\"primary\">{merchant.data?.plan}</Badge>\n"
        "      </div>\n"
        "    </div>\n"
        "  </CardBody>\n"
        "</Card>"
    )


# ─────────────────────────────────────────────────────────
#  Chapter 14 - Formatting Utilities
# ─────────────────────────────────────────────────────────

def _ch14(pdf: CoursePDF) -> None:
    pdf.chapter_title("14", "Formatting Utilities")

    pdf.section_title("14.1", "Overview")
    pdf.body(
        "The format.ts module (src/lib/format.ts) provides 7 pure utility functions for "
        "consistent data formatting across the application. All functions are stateless and "
        "side-effect-free, making them easy to test and reuse."
    )

    pdf.section_title("14.2", "Function Reference")

    pdf.subsection("1. fmt.number(value: number): string")
    pdf.body(
        "Formats a number with thousand separators using Intl.NumberFormat. Handles undefined "
        "and NaN gracefully by returning '0'."
    )
    pdf.code_block(
        "export function number(value: number | undefined): string {\n"
        "  if (value == null || isNaN(value)) return '0';\n"
        "  return new Intl.NumberFormat('en-US').format(value);\n"
        "}\n"
        "\n"
        "// Examples:\n"
        "// number(1234567)  => '1,234,567'\n"
        "// number(42)       => '42'\n"
        "// number(undefined) => '0'"
    )

    pdf.subsection("2. fmt.pct(value: number): string")
    pdf.body(
        "Formats a decimal value (0-1) as a percentage string with one decimal place."
    )
    pdf.code_block(
        "export function pct(value: number | undefined): string {\n"
        "  if (value == null || isNaN(value)) return '0.0%';\n"
        "  return (value * 100).toFixed(1) + '%';\n"
        "}\n"
        "\n"
        "// Examples:\n"
        "// pct(0.856)  => '85.6%'\n"
        "// pct(0.1)    => '10.0%'\n"
        "// pct(1)      => '100.0%'"
    )

    pdf.subsection("3. fmt.dec(value: number, places?: number): string")
    pdf.body(
        "Formats a number with a specified number of decimal places (default 2)."
    )
    pdf.code_block(
        "export function dec(\n"
        "  value: number | undefined, places = 2\n"
        "): string {\n"
        "  if (value == null || isNaN(value)) return '0.00';\n"
        "  return value.toFixed(places);\n"
        "}\n"
        "\n"
        "// Examples:\n"
        "// dec(3.14159)     => '3.14'\n"
        "// dec(3.14159, 4)  => '3.1416'"
    )

    pdf.subsection("4. fmt.date(value: string): string")
    pdf.body(
        "Formats an ISO date string to a human-readable date using the browser locale."
    )
    pdf.code_block(
        "export function date(value: string | undefined): string {\n"
        "  if (!value) return '-';\n"
        "  return new Date(value).toLocaleDateString('en-US', {\n"
        "    year: 'numeric', month: 'short', day: 'numeric',\n"
        "  });\n"
        "}\n"
        "\n"
        "// Examples:\n"
        "// date('2026-03-21T10:30:00Z') => 'Mar 21, 2026'"
    )

    pdf.subsection("5. fmt.time(value: string): string")
    pdf.body(
        "Formats an ISO date string to a time string with hours, minutes, and seconds."
    )
    pdf.code_block(
        "export function time(value: string | undefined): string {\n"
        "  if (!value) return '-';\n"
        "  return new Date(value).toLocaleTimeString('en-US', {\n"
        "    hour: '2-digit', minute: '2-digit', second: '2-digit',\n"
        "  });\n"
        "}"
    )

    pdf.subsection("6. fmt.duration(seconds: number): string")
    pdf.body(
        "Converts a number of seconds into a human-readable duration string (e.g., '2m 30s')."
    )
    pdf.code_block(
        "export function duration(seconds: number | undefined): string {\n"
        "  if (seconds == null || isNaN(seconds)) return '0s';\n"
        "  const m = Math.floor(seconds / 60);\n"
        "  const s = Math.round(seconds % 60);\n"
        "  return m > 0 ? `${m}m ${s}s` : `${s}s`;\n"
        "}\n"
        "\n"
        "// Examples:\n"
        "// duration(150)  => '2m 30s'\n"
        "// duration(45)   => '45s'"
    )

    pdf.subsection("7. fmt.truncate(text: string, max?: number): string")
    pdf.body(
        "Truncates a string to a maximum length with an ellipsis."
    )
    pdf.code_block(
        "export function truncate(\n"
        "  text: string, max = 50\n"
        "): string {\n"
        "  if (!text || text.length <= max) return text ?? '';\n"
        "  return text.slice(0, max) + '...';\n"
        "}"
    )

    pdf.tip_box(
        "Why Intl.NumberFormat?",
        "Using Intl.NumberFormat for number formatting respects the user's\n"
        "locale settings and handles edge cases (negative numbers, very\n"
        "large numbers) correctly. It is built into all modern browsers\n"
        "with zero bundle cost, unlike libraries like numeral.js."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 15 - Performance Optimization Deep Dive
# ─────────────────────────────────────────────────────────

def _ch15(pdf: CoursePDF) -> None:
    pdf.chapter_title("15", "Performance Optimization Deep Dive")

    pdf.section_title("15.1", "Bundle Size: Lazy Imports")
    pdf.body(
        "The single largest optimization is lazy-loading Recharts via next/dynamic. Recharts "
        "and its D3 dependencies account for approximately 400KB of JavaScript. By using "
        "dynamic imports, this code is split into a separate chunk that only loads when a "
        "chart component first renders."
    )
    pdf.code_block(
        "// Without lazy loading:\n"
        "import { BarChart } from 'recharts'; // 400KB in main bundle\n"
        "\n"
        "// With lazy loading:\n"
        "const LazyBarChart = dynamic(\n"
        "  () => import('recharts').then(m => m.BarChart),\n"
        "  { ssr: false }\n"
        ");\n"
        "// 0KB in main bundle, 400KB loaded on demand"
    )
    pdf.body(
        "Combined with next.config.js optimizePackageImports for recharts, this ensures that "
        "only the specific chart components used are included in the dynamic chunk, further "
        "reducing the loaded size."
    )

    pdf.section_title("15.2", "React.memo Strategy")
    pdf.body(
        "React.memo is applied to components that meet two criteria: (1) they render frequently "
        "due to parent re-renders, and (2) their props change infrequently. Memoized components "
        "in this project include:"
    )
    cols = [("Component", 45), ("Why Memoized", 135)]
    pdf.table_header(cols)
    pdf.table_row(["StatCard", "Parent (Overview) re-renders on any KPI change; individual cards rarely change"], [45, 135])
    pdf.table_row(["FilterSelect", "Other filter changes cause parent re-render; this filter's props are stable"], [45, 135])
    pdf.table_row(["FilterInput", "Same as FilterSelect for text input fields"], [45, 135])
    pdf.table_row(["PaginationBtn", "Only current page button changes; others should skip re-render"], [45, 135])
    pdf.table_row(["MetricBox", "Session detail features grid re-renders; individual boxes are static"], [45, 135])
    pdf.table_row(["Feature", "Same as MetricBox for feature list items"], [45, 135])

    pdf.warn_box(
        "When NOT to Use React.memo",
        "React.memo has overhead: it must shallow-compare all props on every\n"
        "render. If a component's props change on every render (e.g., inline\n"
        "objects, new function references), memo actually makes performance\n"
        "worse. Only memoize after verifying props are stable."
    )

    pdf.section_title("15.3", "Stable References Pattern")
    pdf.body(
        "Several patterns in the codebase ensure that object and function references remain "
        "stable across renders:"
    )
    pdf.numbered(1, "Module-level constants: OUTCOME_OPTIONS, DEVICE_OPTIONS, chartTooltipStyle, tickStyle are defined outside components so they are created once.")
    pdf.numbered(2, "useMemo for computed values: tooltipFormatter functions are memoized with empty dependency arrays.")
    pdf.numbered(3, "useCallback for event handlers: Filter change handlers and fetcher functions use useCallback to maintain stable references.")
    pdf.numbered(4, "fetcherRef in useQuery: The ref pattern avoids putting the fetcher function in the effect dependency array.")

    pdf.section_title("15.4", "Cache Deduplication")
    pdf.body(
        "The useQuery cache prevents duplicate API calls when multiple components request the "
        "same data within 30 seconds. For example, navigating away from the overview page and "
        "back within 30 seconds returns cached data instantly without an API call."
    )
    pdf.body(
        "The cache also deduplicates concurrent requests. If two components mount simultaneously "
        "with the same cache key, only one API call is made (the second finds cached data)."
    )

    pdf.section_title("15.5", "Next.js Configuration Optimizations")
    pdf.code_block(
        "// next.config.js\n"
        "const nextConfig = {\n"
        "  reactStrictMode: true,    // Catches bugs in development\n"
        "  compress: true,           // gzip compression for responses\n"
        "  images: {\n"
        "    formats: ['image/avif', 'image/webp'],  // Modern formats\n"
        "  },\n"
        "  experimental: {\n"
        "    optimizePackageImports: ['recharts'],  // Tree-shake recharts\n"
        "  },\n"
        "};"
    )
    pdf.numbered(1, "reactStrictMode: Runs effects twice in development to catch side effects and stale closures. No impact in production.")
    pdf.numbered(2, "compress: Enables gzip compression for all HTTP responses, reducing transfer size by ~70%.")
    pdf.numbered(3, "image formats: Serves AVIF (best compression) with WebP fallback. AVIF saves ~50% vs JPEG.")
    pdf.numbered(4, "optimizePackageImports: Enables deep tree-shaking for recharts, eliminating unused chart types from the bundle.")

    pdf.section_title("15.6", "GPU Compositing for Animations")
    pdf.body(
        "The StatCard gradient blob uses will-change: transform (via Tailwind's "
        "will-change-transform) to promote the element to its own GPU compositing layer. This "
        "means the blob animation runs on the GPU without triggering layout recalculations or "
        "repaints of surrounding elements."
    )

    pdf.section_title("15.7", "LCP Optimization")
    pdf.body(
        "The Sidebar logo uses Next.js Image with the priority prop, which adds a "
        "<link rel='preload'> tag in the document head. Since the logo is the largest "
        "contentful paint (LCP) element on initial load, preloading it ensures it appears "
        "as quickly as possible."
    )


# ─────────────────────────────────────────────────────────
#  Chapter 16 - Build, Deploy & Next Steps
# ─────────────────────────────────────────────────────────

def _ch16(pdf: CoursePDF) -> None:
    pdf.chapter_title("16", "Build, Deploy & Next Steps")

    pdf.section_title("16.1", "Build Configuration")
    pdf.body(
        "The production build process uses Next.js's built-in optimization pipeline. Running "
        "'npm run build' produces an optimized production bundle with automatic code splitting, "
        "tree shaking, and minification."
    )
    pdf.code_block(
        "# Development\n"
        "npm run dev      # Starts dev server on localhost:3000\n"
        "\n"
        "# Production build\n"
        "npm run build    # Compiles and optimizes\n"
        "npm run start    # Serves production build\n"
        "\n"
        "# Type checking\n"
        "npx tsc --noEmit # Verify types without emitting files"
    )

    pdf.section_title("16.2", "Environment Variables")
    pdf.body(
        "The application uses a single environment variable for configuration. Next.js requires "
        "the NEXT_PUBLIC_ prefix for variables that must be available in the browser."
    )
    cols = [("Variable", 60), ("Default", 55), ("Description", 65)]
    pdf.table_header(cols)
    pdf.table_row(["NEXT_PUBLIC_API_URL", "http://localhost:8000", "Backend API base URL"], [60, 55, 65])

    pdf.warn_box(
        "NEXT_PUBLIC_ Prefix is Required",
        "Without the NEXT_PUBLIC_ prefix, environment variables are only\n"
        "available on the server (in API routes and Server Components).\n"
        "Since our API client runs in the browser, the variable MUST have\n"
        "the NEXT_PUBLIC_ prefix to be included in the client bundle."
    )

    pdf.section_title("16.3", "CORS Configuration")
    pdf.body(
        "The backend was updated to allow cross-origin requests from the frontend development "
        "servers. The CORS configuration in the backend config.py includes both localhost:3000 "
        "(default Next.js port) and localhost:3001 (alternate port)."
    )
    pdf.code_block(
        "# Backend config.py CORS settings\n"
        "CORS_ORIGINS = os.getenv('CORS_ORIGINS',\n"
        "  'http://localhost:3000,http://localhost:3001'\n"
        ").split(',')\n"
        "\n"
        "# Backend .env override\n"
        "CORS_ORIGINS=http://localhost:3000,http://your-domain.com"
    )

    pdf.section_title("16.4", "Production Checklist")
    pdf.body(
        "Before deploying to production, verify the following items:"
    )
    pdf.numbered(1, "Set NEXT_PUBLIC_API_URL to the production backend URL (e.g., https://api.emoratest.com).")
    pdf.numbered(2, "Update CORS_ORIGINS in the backend to include the production frontend domain.")
    pdf.numbered(3, "Replace localStorage SDK key storage with httpOnly cookies or a secure token exchange.")
    pdf.numbered(4, "Enable CSP (Content Security Policy) headers to prevent XSS attacks.")
    pdf.numbered(5, "Configure a CDN (CloudFront, Vercel Edge) for static assets and the Next.js build output.")
    pdf.numbered(6, "Set up monitoring (Sentry, Datadog) for runtime error tracking.")
    pdf.numbered(7, "Run Lighthouse audit to verify Core Web Vitals (LCP < 2.5s, FID < 100ms, CLS < 0.1).")
    pdf.numbered(8, "Enable rate limiting on the backend to prevent API abuse.")
    pdf.numbered(9, "Add E2E tests (Playwright or Cypress) for critical user flows.")
    pdf.numbered(10, "Review bundle analysis output (npm run build shows chunk sizes) for unexpected large modules.")

    pdf.section_title("16.5", "Next Steps - Epic 6 and Beyond")
    pdf.body(
        "The Merchant Dashboard v1 establishes the foundation. Future enhancements planned for "
        "subsequent epics include:"
    )
    pdf.bullet("Real-time updates via WebSocket for live session monitoring and KPI streaming.")
    pdf.bullet("Dark mode support using the CSS custom property design system (swap :root token values).")
    pdf.bullet("Advanced filtering with saved filter presets and URL-based filter state for shareable links.")
    pdf.bullet("Export capabilities: CSV/PDF export for analytics data and experiment reports.")
    pdf.bullet("Role-based access control (RBAC) with different permission levels for merchant team members.")
    pdf.bullet("Onboarding wizard to guide new merchants through SDK integration and dashboard setup.")
    pdf.bullet("A/B test statistical significance calculator with Bayesian inference visualization.")
    pdf.bullet("Custom dashboard layouts allowing merchants to arrange widgets and pin favorite metrics.")

    pdf.tip_box(
        "Architecture Ready for Growth",
        "The layered architecture, typed API client, and caching hook were\n"
        "designed to support these future features without major refactoring.\n"
        "Adding WebSocket support, for example, only requires a new hook\n"
        "that writes to the same cache, and all existing components will\n"
        "automatically display the live data."
    )


# ─────────────────────────────────────────────────────────
#  Build entry point
# ─────────────────────────────────────────────────────────

def build() -> None:
    pdf = CoursePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    _cover(pdf)
    _toc(pdf)
    _ch01(pdf)
    _ch02(pdf)
    _ch03(pdf)
    _ch04(pdf)
    _ch05(pdf)
    _ch06(pdf)
    _ch07(pdf)
    _ch08(pdf)
    _ch09(pdf)
    _ch10(pdf)
    _ch11(pdf)
    _ch12(pdf)
    _ch13(pdf)
    _ch14(pdf)
    _ch15(pdf)
    _ch16(pdf)

    out = "docs/Epic5_Merchant_Dashboard_v1.pdf"
    pdf.output(out)
    print(f"PDF generated: {out}")


if __name__ == "__main__":
    build()
