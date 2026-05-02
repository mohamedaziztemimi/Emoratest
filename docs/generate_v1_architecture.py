"""Generate EmoraTest V1 MVP - Architecture Overview PDF.

Run:  python docs/generate_v1_architecture.py

Produces: docs/V1_Architecture_Overview.pdf
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
        self.cell(0, 8, "EmoraTest V1 - Architecture Overview", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, "EmoraTest AI Platform - V1 MVP Documentation", align="C")

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
#  Content
# ─────────────────────────────────────────────────────────


def _cover(pdf: CoursePDF) -> None:
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.cell(0, 14, "EmoraTest V1 MVP", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(0, 12, "Architecture Overview", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 10, "AI Behavioral Intelligence for E-Commerce", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "Complete Technical Reference", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(*pdf.PRIMARY)
    pdf.set_line_width(1)
    cx = pdf.w / 2
    pdf.line(cx - 40, pdf.get_y(), cx + 40, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 8, "7 Epics  |  88 Stories  |  10 Sprints  |  V1 Complete", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "FastAPI  |  Next.js 14  |  PostgreSQL  |  Redis  |  XGBoost  |  SHAP", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "April 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(
        0, 7,
        "13 Chapters  |  6 Database Tables  |  27 API Endpoints  |  104 Tests  |  Full Platform Reference",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )


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
        ("1", "Platform Overview"),
        ("2", "Monorepo Structure"),
        ("3", "Backend Architecture"),
        ("4", "Database Schema"),
        ("5", "Authentication System"),
        ("6", "ML Pipeline"),
        ("7", "JavaScript SDK"),
        ("8", "Dashboard Frontend"),
        ("9", "API Reference"),
        ("10", "Security & GDPR"),
        ("11", "Deployment"),
        ("12", "What V2 Looks Like"),
        ("13", "Testing"),
    ]
    for num, title in chapters:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*pdf.DARK)
        pdf.cell(12, 7, num)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")


# ─── Chapter 1 ──────────────────────────────────────────
def _ch1_platform_overview(pdf: CoursePDF) -> None:
    pdf.chapter_title("1", "Platform Overview")

    pdf.section_title("1.1", "What Is EmoraTest?")
    pdf.body(
        "EmoraTest is an AI-powered behavioral intelligence platform purpose-built for e-commerce. "
        "It captures real-time user behavior on merchant storefronts, applies machine learning models to "
        "detect purchase intent, friction, and abandonment risk, then delivers targeted interventions "
        "(discount popups, urgency banners, exit-intent offers) to maximize conversion rates."
    )
    pdf.body(
        "Unlike traditional A/B testing tools that require manual hypothesis creation, EmoraTest "
        "autonomously identifies behavioral patterns and selects optimal interventions per visitor "
        "segment. The platform combines behavioral event streaming, ensemble ML scoring, SHAP-based "
        "explainability, and a merchant-facing dashboard into a single integrated product."
    )

    pdf.section_title("1.2", "V1 MVP Scope")
    pdf.body(
        "The V1 MVP encompasses 7 completed epics (out of 10 total planned), delivering the core "
        "platform end-to-end. The remaining 3 epics (8-10) are reserved for V2."
    )
    pdf.subsection("Completed Epics (V1)")
    pdf.numbered(1, "Epic 1 - Data Foundation & ML Baseline (CONV-01 to CONV-09): Raw data loading, feature extraction, baseline logistic regression models, evaluation framework.")
    pdf.numbered(2, "Epic 2 - ML Ensemble & SHAP Explainability (CONV-10 to CONV-18): XGBoost models, ensemble scoring, SHAP explanations, intervention recommendation engine.")
    pdf.numbered(3, "Epic 3 - JavaScript SDK (CONV-19 to CONV-27): Browser event collectors, session management, batched transport, UMD/ESM builds.")
    pdf.numbered(4, "Epic 4 - Backend API Complete (CONV-38 to CONV-46): FastAPI application, experiment CRUD, intervention engine, cohort analytics, WebSocket, merchant management.")
    pdf.numbered(5, "Epic 5 - Merchant Dashboard v1 (CONV-51 to CONV-55): Next.js dashboard with overview, sessions, analytics, experiments, interventions, and settings pages.")
    pdf.numbered(6, "Epic 6 - Security & GDPR (CONV-56 to CONV-64): JWT authentication, bcrypt passwords, security headers, rate limiting, audit logging, GDPR consent/export/delete.")
    pdf.numbered(7, "Epic 7 - Dashboard Polish & QA (CONV-65 to CONV-70): Humanized UX, loading states, error boundaries, responsive design, accessibility compliance.")

    pdf.section_title("1.3", "Technology Stack Summary")
    pdf.subsection("Backend")
    pdf.bullet("FastAPI 0.115+ with async/await throughout")
    pdf.bullet("PostgreSQL 16 with UUID primary keys and Row-Level Security")
    pdf.bullet("Redis 7 for caching, rate limiting, and session store")
    pdf.bullet("SQLAlchemy 2.0 ORM with Alembic migrations")
    pdf.bullet("Pydantic v2 for request/response validation")

    pdf.subsection("Frontend")
    pdf.bullet("Next.js 14 with App Router and server components")
    pdf.bullet("React 18 with TypeScript 5")
    pdf.bullet("Tailwind CSS v4 for styling")
    pdf.bullet("Recharts for data visualization")
    pdf.bullet("Lucide React for iconography")

    pdf.subsection("ML Pipeline")
    pdf.bullet("scikit-learn for baseline models (Logistic Regression)")
    pdf.bullet("XGBoost for gradient-boosted ensemble models")
    pdf.bullet("SHAP for model explainability and feature importance")
    pdf.bullet("Pandas + NumPy for data processing")

    pdf.subsection("Infrastructure")
    pdf.bullet("Docker Compose for local development and deployment")
    pdf.bullet("GitHub Actions for CI/CD pipeline")
    pdf.bullet("Alembic for database schema migrations")

    pdf.tip_box(
        "Design Philosophy",
        "EmoraTest follows a monorepo architecture with clear separation of concerns.\n"
        "Each subsystem (backend, frontend, ML, SDK) is independently testable\n"
        "but shares a unified deployment pipeline via Docker Compose."
    )


# ─── Chapter 2 ──────────────────────────────────────────
def _ch2_monorepo_structure(pdf: CoursePDF) -> None:
    pdf.chapter_title("2", "Monorepo Structure")

    pdf.section_title("2.1", "Top-Level Directory Layout")
    pdf.body(
        "The EmoraTest repository is organized as a monorepo with five primary directories, "
        "each owning a distinct concern. This structure allows independent development and testing "
        "of each subsystem while sharing configuration and deployment at the root level."
    )
    pdf.code_block(
        "emoratest/\n"
        "|-- backend/          # FastAPI application\n"
        "|-- frontend/         # Next.js 14 dashboard\n"
        "|-- ml/               # ML pipeline & models\n"
        "|-- sdk/              # JavaScript SDK\n"
        "|-- docs/             # Documentation & PDF generators\n"
        "|-- docker-compose.yml\n"
        "|-- start.sh          # One-command launcher\n"
        "|-- .github/          # CI/CD workflows\n"
        "|-- README.md"
    )

    pdf.section_title("2.2", "Backend Directory")
    pdf.code_block(
        "backend/\n"
        "|-- app/\n"
        "|   |-- main.py              # FastAPI app factory, middleware\n"
        "|   |-- config.py            # Settings via pydantic-settings\n"
        "|   |-- database.py          # SQLAlchemy engine, session\n"
        "|   |-- models.py            # ORM table definitions\n"
        "|   |-- schemas.py           # Pydantic request/response models\n"
        "|   |-- auth.py              # JWT + SDK key authentication\n"
        "|   |-- routers/\n"
        "|   |   |-- sdk.py           # SDK event ingestion\n"
        "|   |   |-- dashboard.py     # Dashboard data endpoints\n"
        "|   |   |-- experiments.py   # Experiment CRUD\n"
        "|   |   |-- interventions.py # Intervention management\n"
        "|   |   |-- analytics.py     # Cohort analytics\n"
        "|   |   |-- merchants.py     # Merchant management\n"
        "|   |   |-- auth.py          # Auth endpoints\n"
        "|   |   |-- ws.py            # WebSocket real-time\n"
        "|   |-- middleware/\n"
        "|   |   |-- rate_limit.py    # Redis-backed rate limiting\n"
        "|   |   |-- security.py      # Security headers\n"
        "|   |   |-- audit.py         # Audit logging\n"
        "|-- tests/                   # 104 pytest tests\n"
        "|-- alembic/                 # Database migrations\n"
        "|-- requirements.txt\n"
        "|-- Dockerfile"
    )
    pdf.body(
        "The backend follows a layered architecture: routers handle HTTP concerns, service logic "
        "lives in router functions (kept thin for V1), and the ORM layer manages persistence. "
        "Middleware is applied globally via the FastAPI app factory in main.py."
    )

    pdf.section_title("2.3", "Frontend Directory")
    pdf.code_block(
        "frontend/\n"
        "|-- src/\n"
        "|   |-- app/\n"
        "|   |   |-- layout.tsx          # Root layout with Sidebar\n"
        "|   |   |-- page.tsx            # Auth guard redirect\n"
        "|   |   |-- login/page.tsx      # Login page\n"
        "|   |   |-- dashboard/\n"
        "|   |       |-- page.tsx         # Overview page\n"
        "|   |       |-- sessions/        # Session explorer\n"
        "|   |       |-- analytics/       # Analytics charts\n"
        "|   |       |-- experiments/     # Experiment manager\n"
        "|   |       |-- interventions/   # Intervention results\n"
        "|   |       |-- settings/        # Account settings\n"
        "|   |-- components/\n"
        "|   |   |-- Sidebar.tsx          # Navigation sidebar\n"
        "|   |   |-- DashboardShell.tsx   # Layout wrapper\n"
        "|   |   |-- StatCard.tsx         # Metric cards\n"
        "|   |   |-- charts/             # Recharts wrappers\n"
        "|   |-- lib/\n"
        "|   |   |-- api.ts              # Axios API client\n"
        "|   |   |-- hooks/              # Custom React hooks\n"
        "|-- tailwind.config.ts\n"
        "|-- next.config.js\n"
        "|-- Dockerfile"
    )

    pdf.section_title("2.4", "ML Directory")
    pdf.code_block(
        "ml/\n"
        "|-- data/                  # Raw + processed datasets\n"
        "|-- models/                # Trained model artifacts\n"
        "|-- src/\n"
        "|   |-- data_loader.py     # CSV/parquet data loading\n"
        "|   |-- features.py        # Feature extraction pipeline\n"
        "|   |-- train_baseline.py  # Logistic regression baseline\n"
        "|   |-- train_xgboost.py   # XGBoost ensemble training\n"
        "|   |-- ensemble.py        # Ensemble scoring engine\n"
        "|   |-- shap_explain.py    # SHAP explainability\n"
        "|   |-- intervention.py    # Intervention recommendation\n"
        "|-- tests/\n"
        "|-- requirements.txt"
    )

    pdf.section_title("2.5", "SDK Directory")
    pdf.code_block(
        "sdk/\n"
        "|-- src/\n"
        "|   |-- index.ts           # Main SDK entry point\n"
        "|   |-- collectors/        # Event collectors (click, scroll, mouse)\n"
        "|   |-- session.ts         # Session management\n"
        "|   |-- queue.ts           # Event queue with batching\n"
        "|   |-- transport.ts       # HTTP transport layer\n"
        "|-- dist/                  # Built UMD + ESM bundles\n"
        "|-- rollup.config.js       # Build configuration\n"
        "|-- package.json"
    )

    pdf.section_title("2.6", "Docs Directory")
    pdf.body(
        "The docs/ directory contains PDF generator scripts for each epic and this architecture "
        "overview document. Each generator is a standalone Python script that uses the fpdf2 library "
        "to produce course-style documentation PDFs."
    )


# ─── Chapter 3 ──────────────────────────────────────────
def _ch3_backend_architecture(pdf: CoursePDF) -> None:
    pdf.chapter_title("3", "Backend Architecture")

    pdf.section_title("3.1", "FastAPI Application Factory")
    pdf.body(
        "The backend is built on FastAPI, a modern async Python web framework. The application is "
        "constructed in main.py using the factory pattern: an app instance is created, middleware is "
        "attached, and routers are included with their respective prefixes."
    )
    pdf.code_block(
        "# main.py - Simplified app factory\n"
        "from fastapi import FastAPI\n"
        "from fastapi.middleware.cors import CORSMiddleware\n"
        "\n"
        "app = FastAPI(title='EmoraTest API', version='1.0.0')\n"
        "\n"
        "# Middleware stack (order matters - outermost first)\n"
        "app.add_middleware(CORSMiddleware, ...)\n"
        "app.add_middleware(SecurityHeadersMiddleware)\n"
        "app.add_middleware(RateLimitMiddleware)\n"
        "app.add_middleware(AuditLogMiddleware)\n"
        "\n"
        "# Router registration\n"
        "app.include_router(auth_router, prefix='/api/auth')\n"
        "app.include_router(sdk_router, prefix='/api/sdk')\n"
        "app.include_router(dashboard_router, prefix='/api/dashboard')\n"
        "app.include_router(experiments_router, prefix='/api/experiments')\n"
        "app.include_router(interventions_router, prefix='/api/interventions')\n"
        "app.include_router(analytics_router, prefix='/api/analytics')\n"
        "app.include_router(merchants_router, prefix='/api/merchants')\n"
        "app.include_router(ws_router, prefix='/api/ws')"
    )

    pdf.section_title("3.2", "Router Architecture")
    pdf.body(
        "Each router module owns a domain of the API. Routers are thin controllers that validate "
        "input via Pydantic schemas, call the database layer, and return structured responses. "
        "Authentication dependencies are injected per-route using FastAPI's Depends() system."
    )
    pdf.subsection("Router Summary")
    cols = [("Router", 35), ("Prefix", 35), ("Endpoints", 20), ("Auth", 25), ("Purpose", 65)]
    pdf.table_header(cols)
    rows = [
        ["auth", "/api/auth", "4", "None/JWT", "Registration, login, token refresh"],
        ["sdk", "/api/sdk", "4", "SDK Key", "Event ingestion, session create"],
        ["dashboard", "/api/dashboard", "4", "JWT", "Overview stats, session list"],
        ["experiments", "/api/experiments", "5", "JWT", "Experiment CRUD + results"],
        ["interventions", "/api/interventions", "3", "JWT", "Intervention management"],
        ["analytics", "/api/analytics", "2", "JWT", "Cohort + funnel analytics"],
        ["merchants", "/api/merchants", "4", "JWT", "Merchant profile CRUD"],
        ["ws", "/api/ws", "1", "JWT", "Real-time WebSocket stream"],
    ]
    widths = [35, 35, 20, 25, 65]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("3.3", "Middleware Stack")
    pdf.body(
        "Middleware is applied in a specific order to ensure correct request processing. "
        "Each middleware wraps the next, forming a pipeline that every request passes through."
    )
    pdf.subsection("CORS Middleware")
    pdf.body(
        "Configured to allow the frontend origin (localhost:3000 in development) with credentials. "
        "Allows GET, POST, PUT, DELETE, OPTIONS methods. Exposes Authorization header for JWT flow."
    )
    pdf.subsection("Security Headers Middleware")
    pdf.body(
        "Adds protective HTTP headers to every response: X-Content-Type-Options: nosniff, "
        "X-Frame-Options: DENY, X-XSS-Protection: 1; mode=block, Strict-Transport-Security, "
        "Content-Security-Policy with restrictive defaults, and Referrer-Policy: strict-origin-when-cross-origin."
    )
    pdf.subsection("Rate Limiting Middleware")
    pdf.body(
        "Redis-backed sliding window rate limiter. Different tiers for different endpoint groups: "
        "SDK ingestion endpoints allow higher throughput (1000 req/min) while auth endpoints are "
        "more restrictive (20 req/min for login to prevent brute-force). Returns 429 Too Many "
        "Requests with Retry-After header when limits are exceeded."
    )
    pdf.subsection("Audit Logging Middleware")
    pdf.body(
        "Records every state-changing request (POST, PUT, DELETE) to an audit log. Captures "
        "timestamp, user ID (from JWT), IP address, endpoint path, method, and response status. "
        "Used for GDPR compliance and security forensics."
    )

    pdf.section_title("3.4", "Error Handling")
    pdf.body(
        "The application uses structured error responses with consistent JSON format. "
        "Custom exception handlers catch validation errors (422), authentication failures (401), "
        "authorization failures (403), not found (404), and internal server errors (500). "
        "Each returns a response with 'detail' field containing a human-readable message."
    )
    pdf.code_block(
        '# Error response format\n'
        '{\n'
        '  "detail": "Experiment not found",\n'
        '  "status_code": 404,\n'
        '  "error_type": "not_found"\n'
        '}'
    )


# ─── Chapter 4 ──────────────────────────────────────────
def _ch4_database_schema(pdf: CoursePDF) -> None:
    pdf.chapter_title("4", "Database Schema")

    pdf.section_title("4.1", "Schema Overview")
    pdf.body(
        "EmoraTest uses PostgreSQL 16 with 6 core tables. All tables use UUID primary keys "
        "generated server-side for global uniqueness. Row-Level Security (RLS) policies ensure "
        "merchants can only access their own data. Timestamps use timezone-aware UTC throughout."
    )

    pdf.section_title("4.2", "merchants Table")
    pdf.body(
        "Stores merchant accounts. Each merchant has a unique SDK key for browser-side "
        "authentication and a hashed password for dashboard login."
    )
    cols = [("Column", 40), ("Type", 35), ("Constraints", 40), ("Description", 65)]
    pdf.table_header(cols)
    rows = [
        ["id", "UUID", "PK, default uuid4", "Unique merchant ID"],
        ["email", "VARCHAR(255)", "UNIQUE, NOT NULL", "Login email"],
        ["company_name", "VARCHAR(255)", "NOT NULL", "Business name"],
        ["hashed_password", "VARCHAR(255)", "NOT NULL", "bcrypt hash"],
        ["sdk_key", "VARCHAR(64)", "UNIQUE, NOT NULL", "SDK auth key"],
        ["is_active", "BOOLEAN", "DEFAULT true", "Account status"],
        ["created_at", "TIMESTAMPTZ", "DEFAULT now()", "Registration time"],
        ["updated_at", "TIMESTAMPTZ", "DEFAULT now()", "Last update time"],
    ]
    widths = [40, 35, 40, 65]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("4.3", "sessions Table")
    pdf.body(
        "Tracks individual visitor browsing sessions. Linked to a merchant via foreign key. "
        "Sessions have a configurable timeout (default 30 minutes of inactivity)."
    )
    cols = [("Column", 40), ("Type", 35), ("Constraints", 40), ("Description", 65)]
    pdf.table_header(cols)
    rows = [
        ["id", "UUID", "PK, default uuid4", "Session ID"],
        ["merchant_id", "UUID", "FK -> merchants.id", "Owning merchant"],
        ["visitor_id", "VARCHAR(64)", "NOT NULL", "Anonymous visitor hash"],
        ["started_at", "TIMESTAMPTZ", "DEFAULT now()", "Session start"],
        ["ended_at", "TIMESTAMPTZ", "NULLABLE", "Session end"],
        ["page_count", "INTEGER", "DEFAULT 0", "Pages visited"],
        ["device_type", "VARCHAR(20)", "NULLABLE", "desktop/mobile/tablet"],
        ["user_agent", "TEXT", "NULLABLE", "Browser user agent"],
    ]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("4.4", "events Table")
    pdf.body(
        "High-volume table storing every behavioral event captured by the SDK. Events are "
        "append-only and never updated. Indexed on session_id and event_type for fast querying."
    )
    cols = [("Column", 40), ("Type", 35), ("Constraints", 40), ("Description", 65)]
    pdf.table_header(cols)
    rows = [
        ["id", "UUID", "PK, default uuid4", "Event ID"],
        ["session_id", "UUID", "FK -> sessions.id", "Parent session"],
        ["event_type", "VARCHAR(50)", "NOT NULL, INDEXED", "click/scroll/mouse/page"],
        ["timestamp", "TIMESTAMPTZ", "NOT NULL", "Event occurrence time"],
        ["page_url", "TEXT", "NOT NULL", "Current page URL"],
        ["element_selector", "VARCHAR(255)", "NULLABLE", "CSS selector target"],
        ["payload", "JSONB", "DEFAULT '{}'", "Event-specific data"],
        ["x_position", "INTEGER", "NULLABLE", "Mouse X coordinate"],
        ["y_position", "INTEGER", "NULLABLE", "Mouse Y coordinate"],
    ]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("4.5", "session_features Table")
    pdf.body(
        "Stores computed ML features for each session. Populated by the feature extraction "
        "pipeline after sufficient events are collected. One row per session."
    )
    cols = [("Column", 40), ("Type", 35), ("Constraints", 40), ("Description", 65)]
    pdf.table_header(cols)
    rows = [
        ["id", "UUID", "PK, default uuid4", "Feature row ID"],
        ["session_id", "UUID", "FK -> sessions.id, UQ", "Linked session"],
        ["hesitation_score", "FLOAT", "DEFAULT 0", "Mouse hesitation metric"],
        ["rage_click_count", "INTEGER", "DEFAULT 0", "Rapid re-clicks detected"],
        ["scroll_retreat_pct", "FLOAT", "DEFAULT 0", "Backward scroll ratio"],
        ["exit_intent_count", "INTEGER", "DEFAULT 0", "Cursor-to-close events"],
        ["intent_score", "FLOAT", "NULLABLE", "ML purchase intent (0-1)"],
        ["friction_score", "FLOAT", "NULLABLE", "ML friction level (0-1)"],
        ["computed_at", "TIMESTAMPTZ", "DEFAULT now()", "Computation timestamp"],
    ]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("4.6", "experiments Table")
    pdf.body(
        "Manages A/B testing experiments. Each experiment defines a control and variant "
        "configuration, target audience percentage, and tracks status lifecycle."
    )
    cols = [("Column", 40), ("Type", 35), ("Constraints", 40), ("Description", 65)]
    pdf.table_header(cols)
    rows = [
        ["id", "UUID", "PK, default uuid4", "Experiment ID"],
        ["merchant_id", "UUID", "FK -> merchants.id", "Owning merchant"],
        ["name", "VARCHAR(255)", "NOT NULL", "Experiment name"],
        ["description", "TEXT", "NULLABLE", "Experiment description"],
        ["status", "VARCHAR(20)", "DEFAULT 'draft'", "draft/running/paused/done"],
        ["variant_config", "JSONB", "NOT NULL", "Control + variant setup"],
        ["traffic_pct", "FLOAT", "DEFAULT 0.5", "Variant traffic allocation"],
        ["started_at", "TIMESTAMPTZ", "NULLABLE", "Experiment start"],
        ["ended_at", "TIMESTAMPTZ", "NULLABLE", "Experiment end"],
        ["created_at", "TIMESTAMPTZ", "DEFAULT now()", "Creation timestamp"],
    ]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("4.7", "intervention_results Table")
    pdf.body(
        "Records the outcome of each intervention delivered to a visitor. Links back to "
        "the session and optionally to an experiment for A/B attribution."
    )
    cols = [("Column", 40), ("Type", 35), ("Constraints", 40), ("Description", 65)]
    pdf.table_header(cols)
    rows = [
        ["id", "UUID", "PK, default uuid4", "Result ID"],
        ["session_id", "UUID", "FK -> sessions.id", "Target session"],
        ["experiment_id", "UUID", "FK -> experiments.id", "Linked experiment"],
        ["intervention_type", "VARCHAR(50)", "NOT NULL", "discount/urgency/exit"],
        ["shown_at", "TIMESTAMPTZ", "DEFAULT now()", "When displayed"],
        ["clicked", "BOOLEAN", "DEFAULT false", "User clicked CTA"],
        ["converted", "BOOLEAN", "DEFAULT false", "Led to purchase"],
        ["revenue_delta", "FLOAT", "DEFAULT 0", "Revenue impact ($)"],
    ]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.tip_box(
        "Schema Design Decisions",
        "UUID primary keys: Enable distributed ID generation without coordination.\n"
        "JSONB for payload/config: Flexible schema for event data and experiment variants.\n"
        "TIMESTAMPTZ everywhere: All times stored in UTC, converted at display layer.\n"
        "RLS policies: PostgreSQL row-level security ensures tenant data isolation."
    )


# ─── Chapter 5 ──────────────────────────────────────────
def _ch5_authentication(pdf: CoursePDF) -> None:
    pdf.chapter_title("5", "Authentication System")

    pdf.section_title("5.1", "Dual Authentication Model")
    pdf.body(
        "EmoraTest uses two distinct authentication mechanisms, each optimized for its use case. "
        "The JavaScript SDK uses API key authentication for simplicity and performance, while the "
        "merchant dashboard uses JWT bearer tokens for stateless session management."
    )

    pdf.section_title("5.2", "SDK Key Authentication")
    pdf.body(
        "The SDK authenticates requests using an X-SDK-Key HTTP header. Each merchant receives a "
        "unique 64-character cryptographically random key upon registration. The key is validated "
        "on every SDK request by looking it up in the merchants table."
    )
    pdf.code_block(
        "# SDK request with API key\n"
        "POST /api/sdk/events\n"
        "X-SDK-Key: sk_live_a1b2c3d4e5f6...\n"
        "Content-Type: application/json\n"
        "\n"
        '{"session_id": "...", "events": [...]}'
    )
    pdf.body(
        "SDK keys are designed for browser-side use and are intentionally limited in scope. "
        "They can only access SDK endpoints (event ingestion, session creation) and cannot "
        "read dashboard data or modify merchant settings."
    )

    pdf.section_title("5.3", "JWT Bearer Token Authentication")
    pdf.body(
        "Dashboard access uses JSON Web Tokens (JWT) with the HS256 algorithm. Tokens are "
        "issued upon successful login and must be included in the Authorization header "
        "for all dashboard, experiment, analytics, and merchant management endpoints."
    )
    pdf.subsection("Token Lifecycle")
    pdf.numbered(1, "Merchant submits email + password to POST /api/auth/login.")
    pdf.numbered(2, "Server verifies password against bcrypt hash in database.")
    pdf.numbered(3, "On success, server returns an access token (24h expiry) and a refresh token (7d expiry).")
    pdf.numbered(4, "Client stores tokens and includes access token in Authorization: Bearer <token> header.")
    pdf.numbered(5, "When access token expires, client calls POST /api/auth/refresh with the refresh token.")
    pdf.numbered(6, "Server issues a new access token. Refresh tokens are single-use (rotated on each refresh).")

    pdf.code_block(
        "# JWT payload structure\n"
        "{\n"
        '  "sub": "merchant-uuid-here",\n'
        '  "email": "merchant@example.com",\n'
        '  "type": "access",\n'
        '  "exp": 1711929600,\n'
        '  "iat": 1711843200\n'
        "}"
    )

    pdf.section_title("5.4", "Registration Flow")
    pdf.body(
        "New merchants register via POST /api/auth/register with email, company name, and password. "
        "The server validates the email format, checks for uniqueness, hashes the password with "
        "bcrypt (12 rounds), generates a unique SDK key, and creates the merchant record. "
        "The response includes the merchant profile and an initial access token."
    )

    pdf.section_title("5.5", "Password Security")
    pdf.body(
        "Passwords are hashed using bcrypt with a cost factor of 12 (approximately 250ms per hash). "
        "Passwords are never stored in plaintext and never logged. Minimum password length is enforced "
        "at 8 characters. The bcrypt algorithm includes a per-hash salt, preventing rainbow table attacks."
    )

    pdf.warn_box(
        "Security Note",
        "V1 uses HS256 (symmetric) JWT signing. V2 will migrate to RS256 (asymmetric)\n"
        "for better key rotation and multi-service token verification."
    )


# ─── Chapter 6 ──────────────────────────────────────────
def _ch6_ml_pipeline(pdf: CoursePDF) -> None:
    pdf.chapter_title("6", "ML Pipeline")

    pdf.section_title("6.1", "Pipeline Overview")
    pdf.body(
        "The ML pipeline spans Epics 1 and 2 and is responsible for transforming raw behavioral "
        "events into actionable intelligence. The pipeline flows from data loading through feature "
        "extraction, model training, ensemble scoring, SHAP explainability, and finally intervention "
        "recommendation."
    )
    pdf.code_block(
        "Pipeline Flow:\n"
        "Raw Events -> Feature Extraction -> Model Training -> Ensemble Scoring\n"
        "    -> SHAP Explanations -> Intervention Recommendations"
    )

    pdf.section_title("6.2", "Data Loading")
    pdf.body(
        "The data_loader module reads raw behavioral data from CSV or Parquet files. It handles "
        "data validation, type coercion, missing value imputation, and outputs a clean Pandas "
        "DataFrame ready for feature extraction. The loader supports incremental loading for "
        "large datasets and includes automatic schema validation."
    )

    pdf.section_title("6.3", "Feature Extraction")
    pdf.body(
        "The feature extraction pipeline computes behavioral signals from raw events. These "
        "features are the core of EmoraTest's behavioral intelligence."
    )
    pdf.subsection("Hesitation Score")
    pdf.body(
        "Measures mouse movement hesitation patterns. Computed from mouse velocity changes, "
        "pauses over interactive elements, and cursor hovering time. High hesitation correlates "
        "with decision uncertainty and is a strong predictor of cart abandonment."
    )
    pdf.subsection("Rage Click Count")
    pdf.body(
        "Detects rapid, repeated clicks on the same or nearby elements within a short time window "
        "(typically 3+ clicks within 500ms). Rage clicks indicate user frustration with "
        "unresponsive UI elements, broken links, or confusing navigation."
    )
    pdf.subsection("Scroll Retreat Percentage")
    pdf.body(
        "Measures the ratio of backward (upward) scrolling to total scroll distance. Users who "
        "frequently scroll back up are re-reading content, comparing options, or struggling to "
        "find information. High retreat percentages suggest friction in the content layout."
    )
    pdf.subsection("Exit Intent Count")
    pdf.body(
        "Tracks cursor movements toward the browser's close/back buttons or rapid mouse movement "
        "toward the top of the viewport. Each detected exit intent gesture is counted per session. "
        "This feature directly triggers exit-intent interventions."
    )

    pdf.section_title("6.4", "Model Training")
    pdf.subsection("Baseline: Logistic Regression (Epic 1)")
    pdf.body(
        "The baseline model uses scikit-learn's LogisticRegression with L2 regularization. "
        "Two models are trained: one for purchase intent prediction (binary: will buy / won't buy) "
        "and one for friction detection (binary: experiencing friction / smooth). The baseline "
        "establishes a performance floor and serves as a sanity check for more complex models."
    )
    pdf.subsection("Advanced: XGBoost Ensemble (Epic 2)")
    pdf.body(
        "XGBoost gradient-boosted trees replace the baseline for production scoring. Key hyperparameters "
        "are tuned via cross-validation: max_depth=6, learning_rate=0.1, n_estimators=200, "
        "min_child_weight=3. The model handles class imbalance via scale_pos_weight. "
        "Two separate XGBoost models are trained for intent and friction respectively."
    )

    pdf.section_title("6.5", "Ensemble Scoring")
    pdf.body(
        "The ensemble module combines predictions from multiple models using weighted averaging. "
        "In V1, the ensemble weights XGBoost at 0.7 and Logistic Regression at 0.3. The ensemble "
        "outputs calibrated probability scores between 0 and 1 for both intent and friction. "
        "Ensemble scoring provides more robust predictions than any single model."
    )
    pdf.code_block(
        "# Ensemble scoring\n"
        "intent_score = 0.7 * xgb_intent + 0.3 * lr_intent\n"
        "friction_score = 0.7 * xgb_friction + 0.3 * lr_friction\n"
        "\n"
        "# Thresholds for intervention triggering\n"
        "HIGH_INTENT = 0.7      # Likely to purchase\n"
        "HIGH_FRICTION = 0.6    # Experiencing friction\n"
        "EXIT_RISK = 0.8        # Likely to abandon"
    )

    pdf.section_title("6.6", "SHAP Explainability")
    pdf.body(
        "SHAP (SHapley Additive exPlanations) values are computed for every prediction to explain "
        "which features drove the model's decision. This powers the dashboard's explainability "
        "panel where merchants can understand why a visitor received a specific intervention."
    )
    pdf.bullet("Per-prediction SHAP values show feature contribution direction and magnitude")
    pdf.bullet("Global SHAP summary plots rank features by overall importance")
    pdf.bullet("SHAP dependence plots reveal interaction effects between features")
    pdf.bullet("Force plots visualize how features push predictions above/below the baseline")

    pdf.section_title("6.7", "Intervention Engine")
    pdf.body(
        "The intervention engine maps ML scores to actionable interventions. It uses a rule-based "
        "decision tree layered on top of the ensemble scores."
    )
    pdf.bullet("High intent + high friction -> Discount popup (reduce friction for likely buyers)")
    pdf.bullet("High intent + low friction -> Urgency banner (accelerate purchase decision)")
    pdf.bullet("Low intent + exit signal -> Exit-intent offer (last-chance retention)")
    pdf.bullet("Low intent + low friction -> No intervention (avoid annoying casual browsers)")

    pdf.tip_box(
        "ML Architecture Decision",
        "V1 uses batch-trained models loaded at API startup. V2 will introduce online\n"
        "learning with incremental model updates as new behavioral data streams in."
    )


# ─── Chapter 7 ──────────────────────────────────────────
def _ch7_javascript_sdk(pdf: CoursePDF) -> None:
    pdf.chapter_title("7", "JavaScript SDK")

    pdf.section_title("7.1", "SDK Overview")
    pdf.body(
        "The EmoraTest JavaScript SDK (Epic 3, CONV-19 to CONV-27) is a lightweight browser "
        "library that captures user behavioral events and streams them to the backend. It is "
        "designed for minimal performance impact on merchant storefronts, with a gzipped size "
        "under 8KB and zero external dependencies."
    )

    pdf.section_title("7.2", "Event Collectors")
    pdf.body(
        "The SDK includes specialized collectors for different event types, each optimized for "
        "its data source. Collectors attach to DOM events using passive listeners to avoid "
        "blocking the main thread."
    )
    pdf.subsection("Click Collector")
    pdf.body(
        "Captures click events with target element selector, coordinates, timestamp, and whether "
        "the click was on an interactive element (link, button, input). Implements rage-click "
        "detection by tracking rapid successive clicks within a 500ms window."
    )
    pdf.subsection("Scroll Collector")
    pdf.body(
        "Monitors scroll position changes using requestAnimationFrame for throttled sampling. "
        "Records scroll direction, velocity, depth percentage, and detects scroll retreat "
        "patterns (scrolling back up after reaching a point)."
    )
    pdf.subsection("Mouse Collector")
    pdf.body(
        "Tracks mouse movement via mousemove events, heavily throttled to ~10 samples/second. "
        "Captures cursor position, velocity, and direction. Detects hesitation (slow movement "
        "over interactive elements) and exit intent (rapid movement toward viewport top)."
    )

    pdf.section_title("7.3", "Session Management")
    pdf.body(
        "The SDK manages visitor sessions automatically. A session is created when the SDK "
        "initializes and persists across page navigations within the same site using sessionStorage. "
        "Sessions expire after 30 minutes of inactivity. Visitor identity is maintained across "
        "sessions using a persistent anonymous ID in localStorage."
    )
    pdf.code_block(
        "// SDK initialization\n"
        "EmoraTest.init({\n"
        "  sdkKey: 'sk_live_YOUR_SDK_KEY_HERE',\n"
        "  endpoint: 'https://api.emoratest.com',\n"
        "  batchSize: 20,\n"
        "  flushInterval: 5000,  // 5 seconds\n"
        "  sessionTimeout: 1800000  // 30 minutes\n"
        "});"
    )

    pdf.section_title("7.4", "Event Queue & Batching")
    pdf.body(
        "Events are not sent individually but accumulated in an in-memory queue. The queue flushes "
        "to the backend when either: (a) the batch size threshold is reached (default 20 events), "
        "or (b) the flush interval timer fires (default 5 seconds), whichever comes first. "
        "The queue also flushes on page unload using the Beacon API for reliability."
    )
    pdf.bullet("In-memory queue with configurable max size (default 500 events)")
    pdf.bullet("Automatic batching reduces HTTP overhead by ~95% vs. per-event sending")
    pdf.bullet("Failed batches are retried with exponential backoff (max 3 retries)")
    pdf.bullet("Queue overflow drops oldest events first (FIFO eviction)")

    pdf.section_title("7.5", "Transport Layer")
    pdf.body(
        "The transport layer handles HTTP communication with the backend. It uses fetch() for "
        "normal requests and navigator.sendBeacon() for page-unload flushes. All requests include "
        "the X-SDK-Key header for authentication."
    )
    pdf.code_block(
        "// Batch event payload\n"
        "POST /api/sdk/events\n"
        "X-SDK-Key: sk_live_...\n"
        "Content-Type: application/json\n"
        "\n"
        "{\n"
        '  "session_id": "sess_abc123",\n'
        '  "events": [\n'
        '    {"type": "click", "timestamp": 1711843200, ...},\n'
        '    {"type": "scroll", "timestamp": 1711843201, ...},\n'
        '    {"type": "mouse", "timestamp": 1711843202, ...}\n'
        "  ]\n"
        "}"
    )

    pdf.section_title("7.6", "Build System")
    pdf.body(
        "The SDK is built using Rollup with TypeScript compilation. Two output formats are produced: "
        "UMD (Universal Module Definition) for script tag inclusion and ESM (ES Modules) for "
        "bundler-based projects. Source maps are generated for debugging."
    )
    pdf.code_block(
        "# Build outputs\n"
        "dist/emoratest-sdk.umd.js       # Script tag usage\n"
        "dist/emoratest-sdk.umd.min.js   # Minified UMD\n"
        "dist/emoratest-sdk.esm.js       # ES module import\n"
        "dist/emoratest-sdk.esm.min.js   # Minified ESM"
    )


# ─── Chapter 8 ──────────────────────────────────────────
def _ch8_dashboard_frontend(pdf: CoursePDF) -> None:
    pdf.chapter_title("8", "Dashboard Frontend")

    pdf.section_title("8.1", "Framework & Architecture")
    pdf.body(
        "The merchant dashboard (Epics 5 and 7) is built with Next.js 14 using the App Router. "
        "It leverages React Server Components where possible for improved performance, with Client "
        "Components for interactive elements. The dashboard provides a complete management interface "
        "for merchants to monitor behavior, run experiments, and view intervention results."
    )

    pdf.section_title("8.2", "Dashboard Pages")
    pdf.subsection("Overview Page (/dashboard)")
    pdf.body(
        "The landing page displays key metrics in StatCard components: total sessions, active "
        "experiments, conversion rate, and revenue impact. Below the metrics, a time-series chart "
        "shows session volume over the last 30 days. Real-time indicators pulse when new sessions "
        "arrive via WebSocket."
    )
    pdf.subsection("Sessions Page (/dashboard/sessions)")
    pdf.body(
        "A paginated, filterable table of all visitor sessions. Each row shows session ID, "
        "device type, page count, duration, and ML scores (intent + friction). Clicking a session "
        "opens a detail panel with the full event timeline and SHAP explanation of the ML scores."
    )
    pdf.subsection("Analytics Page (/dashboard/analytics)")
    pdf.body(
        "Cohort analytics with interactive Recharts visualizations. Includes funnel charts "
        "(visit -> engage -> intent -> convert), time-series overlays comparing cohorts, "
        "and behavioral heatmaps showing feature distributions across visitor segments."
    )
    pdf.subsection("Experiments Page (/dashboard/experiments)")
    pdf.body(
        "Experiment management interface with CRUD operations. Merchants can create new A/B tests, "
        "configure control/variant parameters, set traffic allocation percentages, and monitor "
        "experiment results with statistical significance indicators."
    )
    pdf.subsection("Interventions Page (/dashboard/interventions)")
    pdf.body(
        "Displays intervention results aggregated by type (discount, urgency, exit-intent). "
        "Shows click-through rates, conversion rates, and revenue impact for each intervention "
        "type. Includes a timeline view of recent interventions with outcome details."
    )
    pdf.subsection("Settings Page (/dashboard/settings)")
    pdf.body(
        "Merchant account settings: profile update (company name, email), SDK key display and "
        "regeneration, password change, GDPR data export request, and account deletion."
    )

    pdf.section_title("8.3", "Core Components")
    pdf.subsection("Sidebar")
    pdf.body(
        "Persistent navigation sidebar with links to all dashboard pages. Highlights the active "
        "route, shows the merchant company name, and includes a logout button. Collapses to an "
        "icon-only mode on smaller screens."
    )
    pdf.subsection("DashboardShell")
    pdf.body(
        "Layout wrapper that provides consistent page structure: Sidebar on the left, content "
        "area on the right with a top header bar showing the page title and breadcrumbs. "
        "Handles loading states and error boundaries at the layout level."
    )
    pdf.subsection("StatCard")
    pdf.body(
        "Reusable metric display component with title, value, trend indicator (up/down arrow "
        "with percentage), and optional sparkline. Supports loading skeleton state and "
        "humanized number formatting (e.g., 1.2K instead of 1,234)."
    )
    pdf.subsection("Chart Components")
    pdf.body(
        "Recharts-based visualization components wrapped for EmoraTest's design system. "
        "Includes LineChart, BarChart, AreaChart, PieChart, and FunnelChart with consistent "
        "color theming, responsive sizing, and tooltip formatting."
    )

    pdf.section_title("8.4", "Auth Guard")
    pdf.body(
        "A client-side authentication guard wraps all /dashboard routes. It checks for a valid "
        "JWT token in localStorage on mount. If no token is found or the token is expired, "
        "the user is redirected to /login. The guard also handles token refresh transparently "
        "when the access token is near expiry."
    )

    pdf.section_title("8.5", "API Client")
    pdf.body(
        "A centralized Axios instance configured with the backend base URL, automatic JWT "
        "injection via request interceptor, response error handling (401 triggers logout), "
        "and TypeScript-typed response interfaces. All dashboard pages use this client "
        "via custom React hooks (useOverview, useSessions, useAnalytics, etc.)."
    )


# ─── Chapter 9 ──────────────────────────────────────────
def _ch9_api_reference(pdf: CoursePDF) -> None:
    pdf.chapter_title("9", "API Reference")

    pdf.section_title("9.1", "Authentication Endpoints")
    cols = [("Method", 18), ("Path", 52), ("Auth", 18), ("Description", 92)]
    pdf.table_header(cols)
    widths = [18, 52, 18, 92]
    pdf.table_row(["POST", "/api/auth/register", "None", "Register new merchant account"], widths)
    pdf.table_row(["POST", "/api/auth/login", "None", "Login and receive JWT tokens"], widths)
    pdf.table_row(["POST", "/api/auth/refresh", "JWT", "Refresh access token"], widths)
    pdf.table_row(["GET", "/api/auth/me", "JWT", "Get current merchant profile"], widths)

    pdf.section_title("9.2", "SDK Endpoints")
    pdf.table_header(cols)
    pdf.table_row(["POST", "/api/sdk/sessions", "SDK Key", "Create new visitor session"], widths)
    pdf.table_row(["POST", "/api/sdk/events", "SDK Key", "Ingest batch of events"], widths)
    pdf.table_row(["GET", "/api/sdk/config", "SDK Key", "Get SDK runtime config"], widths)
    pdf.table_row(["POST", "/api/sdk/identify", "SDK Key", "Link visitor to known user"], widths)

    pdf.section_title("9.3", "Dashboard Endpoints")
    pdf.table_header(cols)
    pdf.table_row(["GET", "/api/dashboard/overview", "JWT", "Get overview stats + metrics"], widths)
    pdf.table_row(["GET", "/api/dashboard/sessions", "JWT", "List sessions with filters"], widths)
    pdf.table_row(["GET", "/api/dashboard/sessions/:id", "JWT", "Get session detail + events"], widths)
    pdf.table_row(["GET", "/api/dashboard/recent-events", "JWT", "Get recent event stream"], widths)

    pdf.section_title("9.4", "Experiment Endpoints")
    pdf.table_header(cols)
    pdf.table_row(["GET", "/api/experiments", "JWT", "List all experiments"], widths)
    pdf.table_row(["POST", "/api/experiments", "JWT", "Create new experiment"], widths)
    pdf.table_row(["GET", "/api/experiments/:id", "JWT", "Get experiment details"], widths)
    pdf.table_row(["PUT", "/api/experiments/:id", "JWT", "Update experiment config"], widths)
    pdf.table_row(["DELETE", "/api/experiments/:id", "JWT", "Delete experiment"], widths)

    pdf.section_title("9.5", "Intervention Endpoints")
    pdf.table_header(cols)
    pdf.table_row(["GET", "/api/interventions", "JWT", "List intervention results"], widths)
    pdf.table_row(["GET", "/api/interventions/stats", "JWT", "Get aggregate intervention stats"], widths)
    pdf.table_row(["POST", "/api/interventions/trigger", "JWT", "Manually trigger intervention"], widths)

    pdf.section_title("9.6", "Analytics Endpoints")
    pdf.table_header(cols)
    pdf.table_row(["GET", "/api/analytics/cohorts", "JWT", "Get cohort analysis data"], widths)
    pdf.table_row(["GET", "/api/analytics/funnel", "JWT", "Get conversion funnel data"], widths)

    pdf.section_title("9.7", "Merchant Endpoints")
    pdf.table_header(cols)
    pdf.table_row(["GET", "/api/merchants/profile", "JWT", "Get merchant profile"], widths)
    pdf.table_row(["PUT", "/api/merchants/profile", "JWT", "Update merchant profile"], widths)
    pdf.table_row(["POST", "/api/merchants/sdk-key/rotate", "JWT", "Rotate SDK key"], widths)
    pdf.table_row(["DELETE", "/api/merchants/account", "JWT", "Delete account (GDPR)"], widths)

    pdf.section_title("9.8", "WebSocket Endpoint")
    pdf.table_header(cols)
    pdf.table_row(["WS", "/api/ws/live", "JWT", "Real-time session event stream"], widths)

    pdf.tip_box(
        "API Versioning",
        "All V1 endpoints are unversioned (no /v1/ prefix). V2 will introduce\n"
        "/v2/ prefixed endpoints while maintaining /v1/ backward compatibility."
    )


# ─── Chapter 10 ─────────────────────────────────────────
def _ch10_security_gdpr(pdf: CoursePDF) -> None:
    pdf.chapter_title("10", "Security & GDPR")

    pdf.section_title("10.1", "Security Architecture Overview")
    pdf.body(
        "Security in EmoraTest (Epic 6, CONV-56 to CONV-64) follows a defense-in-depth strategy "
        "with multiple layers: authentication, authorization, transport security, input validation, "
        "rate limiting, security headers, and audit logging. Each layer provides independent "
        "protection against different threat categories."
    )

    pdf.section_title("10.2", "JWT Authentication Security")
    pdf.body(
        "JWT tokens are signed with HS256 using a 256-bit secret key stored in environment "
        "variables. Access tokens expire after 24 hours and refresh tokens after 7 days. "
        "Refresh tokens are single-use and rotated on each use to prevent replay attacks. "
        "Token payloads contain minimal claims (subject, email, type, expiry) to reduce "
        "information exposure."
    )

    pdf.section_title("10.3", "Password Hashing")
    pdf.body(
        "All passwords are hashed using bcrypt with a cost factor of 12 before storage. "
        "bcrypt incorporates a per-hash random salt, making precomputed attacks infeasible. "
        "Password verification is performed in constant time to prevent timing side-channel attacks. "
        "Minimum password length of 8 characters is enforced at the API validation layer."
    )

    pdf.section_title("10.4", "Security Headers")
    pdf.body(
        "Every HTTP response includes security headers applied by the SecurityHeadersMiddleware."
    )
    pdf.bullet("X-Content-Type-Options: nosniff - Prevents MIME type sniffing")
    pdf.bullet("X-Frame-Options: DENY - Prevents clickjacking via iframe embedding")
    pdf.bullet("X-XSS-Protection: 1; mode=block - Enables browser XSS filter")
    pdf.bullet("Strict-Transport-Security: max-age=31536000 - Enforces HTTPS")
    pdf.bullet("Content-Security-Policy: default-src 'self' - Restricts resource loading")
    pdf.bullet("Referrer-Policy: strict-origin-when-cross-origin - Controls referrer leakage")

    pdf.section_title("10.5", "Rate Limiting")
    pdf.body(
        "Redis-backed sliding window rate limiting with tiered thresholds based on endpoint sensitivity."
    )
    cols = [("Endpoint Group", 50), ("Limit", 40), ("Window", 35), ("Action on Exceed", 55)]
    pdf.table_header(cols)
    widths = [50, 40, 35, 55]
    pdf.table_row(["Auth (login/register)", "20 requests", "1 minute", "429 + Retry-After"], widths)
    pdf.table_row(["SDK (event ingestion)", "1000 requests", "1 minute", "429 + Retry-After"], widths)
    pdf.table_row(["Dashboard (read)", "200 requests", "1 minute", "429 + Retry-After"], widths)
    pdf.table_row(["Dashboard (write)", "50 requests", "1 minute", "429 + Retry-After"], widths)
    pdf.table_row(["Global per-IP", "5000 requests", "1 hour", "429 + temp IP block"], widths)

    pdf.section_title("10.6", "Audit Logging")
    pdf.body(
        "All state-changing API operations (POST, PUT, DELETE) are logged to an audit trail. "
        "Each audit entry captures: timestamp, merchant ID, IP address, HTTP method, endpoint path, "
        "request body hash (not the body itself, for privacy), response status code, and user agent. "
        "Audit logs are retained for 90 days and can be exported for compliance review."
    )

    pdf.section_title("10.7", "GDPR Compliance")
    pdf.body(
        "EmoraTest implements GDPR requirements across multiple dimensions."
    )
    pdf.subsection("Consent Management")
    pdf.body(
        "The SDK does not initialize event collection until the merchant's site has obtained "
        "visitor consent. A consent API allows the SDK to check and record consent status. "
        "No behavioral data is captured or transmitted without explicit opt-in."
    )
    pdf.subsection("Data Export (Right of Access)")
    pdf.body(
        "Merchants can request a full export of all data associated with their account via "
        "the settings page. The export includes all sessions, events, features, experiment "
        "configurations, and intervention results in JSON format. Exports are generated "
        "asynchronously and delivered as a downloadable archive."
    )
    pdf.subsection("Data Deletion (Right to Erasure)")
    pdf.body(
        "Account deletion triggers a cascade that removes all merchant data: sessions, events, "
        "features, experiments, intervention results, and the merchant record itself. Deletion "
        "is irreversible and completed within 72 hours per GDPR requirements. Audit log entries "
        "are anonymized (merchant ID replaced with a hash) rather than deleted, to maintain "
        "security forensic capability."
    )


# ─── Chapter 11 ─────────────────────────────────────────
def _ch11_deployment(pdf: CoursePDF) -> None:
    pdf.chapter_title("11", "Deployment")

    pdf.section_title("11.1", "Docker Compose Architecture")
    pdf.body(
        "EmoraTest deploys as a multi-container application using Docker Compose. The compose "
        "file defines four services: PostgreSQL database, Redis cache, FastAPI backend, and "
        "Next.js frontend. All services communicate over a shared Docker network."
    )
    pdf.code_block(
        "# docker-compose.yml (simplified)\n"
        "services:\n"
        "  postgres:\n"
        "    image: postgres:16-alpine\n"
        "    volumes: [pgdata:/var/lib/postgresql/data]\n"
        "    environment:\n"
        "      POSTGRES_DB: emoratest\n"
        "      POSTGRES_USER: emoratest\n"
        "      POSTGRES_PASSWORD: ${DB_PASSWORD}\n"
        "    ports: ['5432:5432']\n"
        "\n"
        "  redis:\n"
        "    image: redis:7-alpine\n"
        "    ports: ['6379:6379']\n"
        "\n"
        "  backend:\n"
        "    build: ./backend\n"
        "    ports: ['8000:8000']\n"
        "    depends_on: [postgres, redis]\n"
        "    environment:\n"
        "      DATABASE_URL: postgresql://...\n"
        "      REDIS_URL: redis://redis:6379\n"
        "      JWT_SECRET: ${JWT_SECRET}\n"
        "\n"
        "  frontend:\n"
        "    build: ./frontend\n"
        "    ports: ['3000:3000']\n"
        "    depends_on: [backend]\n"
        "    environment:\n"
        "      NEXT_PUBLIC_API_URL: http://backend:8000"
    )

    pdf.section_title("11.2", "Environment Variables")
    cols = [("Variable", 55), ("Service", 25), ("Required", 20), ("Description", 80)]
    pdf.table_header(cols)
    widths = [55, 25, 20, 80]
    pdf.table_row(["DATABASE_URL", "backend", "Yes", "PostgreSQL connection string"], widths)
    pdf.table_row(["REDIS_URL", "backend", "Yes", "Redis connection string"], widths)
    pdf.table_row(["JWT_SECRET", "backend", "Yes", "256-bit secret for JWT signing"], widths)
    pdf.table_row(["DB_PASSWORD", "postgres", "Yes", "Database password"], widths)
    pdf.table_row(["CORS_ORIGINS", "backend", "No", "Allowed CORS origins (comma-separated)"], widths)
    pdf.table_row(["LOG_LEVEL", "backend", "No", "Logging level (default: INFO)"], widths)
    pdf.table_row(["NEXT_PUBLIC_API_URL", "frontend", "Yes", "Backend API base URL"], widths)

    pdf.section_title("11.3", "Start Script")
    pdf.body(
        "The start.sh script provides a one-command launcher for the entire platform. It handles "
        "environment file loading, database migrations, service startup, and health checks."
    )
    pdf.code_block(
        "#!/bin/bash\n"
        "# start.sh - One-command platform launcher\n"
        "\n"
        "# Load environment\n"
        "source .env\n"
        "\n"
        "# Start infrastructure\n"
        "docker compose up -d postgres redis\n"
        "sleep 5  # Wait for DB readiness\n"
        "\n"
        "# Run migrations\n"
        "cd backend && alembic upgrade head && cd ..\n"
        "\n"
        "# Start application services\n"
        "docker compose up -d backend frontend\n"
        "\n"
        "# Health check\n"
        "echo 'Waiting for services...'\n"
        "curl --retry 10 --retry-delay 2 http://localhost:8000/health\n"
        "echo 'EmoraTest is running!'\n"
        "echo 'Dashboard: http://localhost:3000'\n"
        "echo 'API: http://localhost:8000/docs'"
    )

    pdf.section_title("11.4", "Alembic Migrations")
    pdf.body(
        "Database schema changes are managed via Alembic, SQLAlchemy's migration tool. "
        "Migrations are auto-generated from ORM model changes and applied in order. "
        "Each migration includes both upgrade() and downgrade() functions for rollback support."
    )
    pdf.code_block(
        "# Migration commands\n"
        "alembic revision --autogenerate -m 'add experiments table'\n"
        "alembic upgrade head        # Apply all pending migrations\n"
        "alembic downgrade -1        # Rollback one migration\n"
        "alembic history             # Show migration history"
    )

    pdf.warn_box(
        "Production Note",
        "V1 deployment uses Docker Compose suitable for single-server deployment.\n"
        "V2 will introduce Kubernetes manifests for multi-node horizontal scaling."
    )


# ─── Chapter 12 ─────────────────────────────────────────
def _ch12_v2_roadmap(pdf: CoursePDF) -> None:
    pdf.chapter_title("12", "What V2 Looks Like")

    pdf.section_title("12.1", "Remaining Epics Overview")
    pdf.body(
        "Three epics remain for V2, building on the complete V1 foundation. These epics focus on "
        "intelligence amplification (learning from experiment history), natural language interaction "
        "(semantic search and AI-powered suggestions), and infrastructure hardening for production "
        "scale (multi-tenant SaaS with Shopify marketplace integration)."
    )

    pdf.section_title("12.2", "Epic 8: Experiment Memory & Integrations")
    pdf.body(
        "Epic 8 introduces a knowledge graph that remembers outcomes from past experiments. "
        "When a merchant creates a new experiment, the system will reference historical results "
        "from similar experiments (same industry, similar visitor segments, comparable interventions) "
        "to predict likely outcomes and suggest optimal configurations."
    )
    pdf.bullet("Experiment outcome database with embeddings for similarity search")
    pdf.bullet("Cross-merchant anonymized learning (aggregate insights without data sharing)")
    pdf.bullet("Automated experiment suggestions based on detected behavioral patterns")
    pdf.bullet("Integration APIs for external tools (Slack notifications, webhook callbacks)")
    pdf.bullet("Email campaign integration for post-visit re-engagement")

    pdf.section_title("12.3", "Epic 9: Semantic Search & Suggestion Engine")
    pdf.body(
        "Epic 9 adds a natural language interface to the platform. Merchants will be able to "
        "ask questions in plain English ('Why did conversions drop last week?', 'Which pages have "
        "the highest friction?') and receive AI-generated answers with supporting data."
    )
    pdf.bullet("Vector embeddings for session behavior patterns")
    pdf.bullet("Natural language query parser using LLM (Claude API integration)")
    pdf.bullet("Proactive insight generation: system alerts merchants to anomalies")
    pdf.bullet("Suggestion engine recommends experiments based on behavioral trends")
    pdf.bullet("Conversational dashboard interface for non-technical merchants")

    pdf.section_title("12.4", "Epic 10: Infrastructure Scale & Shopify")
    pdf.body(
        "Epic 10 transforms EmoraTest from a single-tenant deployment into a production-grade "
        "multi-tenant SaaS platform with Shopify marketplace presence."
    )
    pdf.bullet("Kubernetes deployment with horizontal pod autoscaling")
    pdf.bullet("Multi-tenant data isolation with schema-per-tenant PostgreSQL")
    pdf.bullet("Shopify App Store listing with OAuth installation flow")
    pdf.bullet("CDN-delivered SDK with edge caching for global performance")
    pdf.bullet("Stripe billing integration with usage-based pricing tiers")
    pdf.bullet("99.9% SLA with multi-region failover and automated disaster recovery")

    pdf.tip_box(
        "V2 Timeline",
        "Epic 8: Estimated 3 sprints (6 weeks)\n"
        "Epic 9: Estimated 3 sprints (6 weeks)\n"
        "Epic 10: Estimated 4 sprints (8 weeks)\n"
        "Target V2 GA: Q4 2026"
    )


# ─── Chapter 13 ─────────────────────────────────────────
def _ch13_testing(pdf: CoursePDF) -> None:
    pdf.chapter_title("13", "Testing")

    pdf.section_title("13.1", "Testing Strategy")
    pdf.body(
        "EmoraTest employs a multi-layer testing strategy covering unit tests, integration tests, "
        "and build verification. The CI pipeline runs all test suites on every push and pull request "
        "to the main branch, blocking merges on any failure."
    )

    pdf.section_title("13.2", "Backend Tests (104 pytest Tests)")
    pdf.body(
        "The backend test suite contains 104 tests covering all API endpoints, authentication flows, "
        "middleware behavior, and error handling. Tests use pytest with async support (pytest-asyncio) "
        "and a test database that is reset between test runs."
    )
    pdf.subsection("Test Categories")
    pdf.bullet("Auth tests: Registration, login, token refresh, invalid credentials, expired tokens (18 tests)")
    pdf.bullet("SDK tests: Session creation, event ingestion, batch processing, SDK key validation (16 tests)")
    pdf.bullet("Dashboard tests: Overview stats, session listing, session detail, pagination (14 tests)")
    pdf.bullet("Experiment tests: CRUD operations, status transitions, validation errors (15 tests)")
    pdf.bullet("Intervention tests: Result recording, aggregation, trigger logic (10 tests)")
    pdf.bullet("Analytics tests: Cohort queries, funnel computation, date range filtering (8 tests)")
    pdf.bullet("Merchant tests: Profile CRUD, SDK key rotation, account deletion (10 tests)")
    pdf.bullet("Middleware tests: Rate limiting, security headers, audit log entries (8 tests)")
    pdf.bullet("WebSocket tests: Connection, authentication, event streaming (5 tests)")

    pdf.subsection("Running Backend Tests")
    pdf.code_block(
        "cd backend\n"
        "pip install -r requirements.txt\n"
        "pip install pytest pytest-asyncio httpx\n"
        "\n"
        "# Run all tests\n"
        "pytest tests/ -v\n"
        "\n"
        "# Run specific test module\n"
        "pytest tests/test_experiments.py -v\n"
        "\n"
        "# Run with coverage\n"
        "pytest tests/ --cov=app --cov-report=html"
    )

    pdf.section_title("13.3", "Code Quality: Ruff Linting")
    pdf.body(
        "The backend uses ruff for fast Python linting and formatting. Ruff checks are enforced "
        "in CI and must pass with zero errors before merge. The ruff configuration covers "
        "import sorting (isort-compatible), unused imports, type annotation consistency, "
        "and PEP 8 compliance."
    )
    pdf.code_block(
        "# Run ruff lint\n"
        "ruff check backend/\n"
        "\n"
        "# Auto-fix fixable issues\n"
        "ruff check backend/ --fix\n"
        "\n"
        "# Format code\n"
        "ruff format backend/"
    )

    pdf.section_title("13.4", "Frontend Build Verification")
    pdf.body(
        "The Next.js frontend is verified by running a full production build. This catches "
        "TypeScript type errors, missing imports, invalid page configurations, and build-time "
        "rendering failures. The build step is mandatory in CI."
    )
    pdf.code_block(
        "cd frontend\n"
        "npm install\n"
        "npm run build    # Next.js production build\n"
        "npm run lint     # ESLint checks"
    )

    pdf.section_title("13.5", "ML Test Suite")
    pdf.body(
        "The ML pipeline has its own test suite verifying data loading, feature extraction "
        "correctness, model training convergence, ensemble scoring consistency, and SHAP "
        "explanation generation. Tests use synthetic datasets to ensure reproducibility."
    )

    pdf.section_title("13.6", "CI/CD Pipeline (GitHub Actions)")
    pdf.body(
        "The GitHub Actions workflow runs on every push to main and every pull request. "
        "It executes all test suites in parallel for fast feedback."
    )
    pdf.code_block(
        "# .github/workflows/ci.yml (simplified)\n"
        "name: CI\n"
        "on: [push, pull_request]\n"
        "\n"
        "jobs:\n"
        "  backend:\n"
        "    runs-on: ubuntu-latest\n"
        "    services:\n"
        "      postgres: {image: postgres:16}\n"
        "      redis: {image: redis:7}\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "      - run: pip install -r backend/requirements.txt\n"
        "      - run: ruff check backend/\n"
        "      - run: pytest backend/tests/ -v\n"
        "\n"
        "  frontend:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-node@v4\n"
        "      - run: cd frontend && npm ci && npm run build\n"
        "\n"
        "  ml:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "      - run: pip install -r ml/requirements.txt\n"
        "      - run: pytest ml/tests/ -v"
    )

    pdf.warn_box(
        "Test Coverage Goal",
        "V1 achieves ~85% line coverage on the backend. The V2 target is 95%\n"
        "with mandatory coverage thresholds enforced in CI (--cov-fail-under=95)."
    )


# ─────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────

def main() -> None:
    pdf = CoursePDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    _cover(pdf)
    _toc(pdf)
    _ch1_platform_overview(pdf)
    _ch2_monorepo_structure(pdf)
    _ch3_backend_architecture(pdf)
    _ch4_database_schema(pdf)
    _ch5_authentication(pdf)
    _ch6_ml_pipeline(pdf)
    _ch7_javascript_sdk(pdf)
    _ch8_dashboard_frontend(pdf)
    _ch9_api_reference(pdf)
    _ch10_security_gdpr(pdf)
    _ch11_deployment(pdf)
    _ch12_v2_roadmap(pdf)
    _ch13_testing(pdf)

    out = "C:/EmoraTest/docs/V1_Architecture_Overview.pdf"
    pdf.output(out)
    print(f"Generated {out}")


if __name__ == "__main__":
    main()
