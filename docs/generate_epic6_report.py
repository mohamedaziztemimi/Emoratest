"""Generate Epic 6 Course-Style Documentation PDF — Security Hardening & GDPR.

Run:  python docs/generate_epic6_report.py

Produces: docs/Epic6_Security_Hardening_GDPR.pdf
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
        self.cell(0, 8, "EmoraTest - Epic 6: Security Hardening & GDPR", align="L")
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


# ---------------------------------------------------------------
#  Content helpers
# ---------------------------------------------------------------

def _cover(pdf: CoursePDF) -> None:
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.cell(0, 14, "EmoraTest AI Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(0, 12, "Epic 6: Security Hardening & GDPR", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 10, "JWT Authentication, GDPR Compliance, Audit Logging", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(*pdf.PRIMARY)
    pdf.set_line_width(1)
    cx = pdf.w / 2
    pdf.line(cx - 40, pdf.get_y(), cx + 40, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 8, "Jira Stories: CONV-56 through CONV-63", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "FastAPI  |  python-jose  |  passlib  |  bcrypt  |  slowapi", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Sprint 6  -  April 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(0, 7, "10 Chapters  |  4 Auth Endpoints  |  3 GDPR Endpoints  |  2 Middleware  |  104 Tests", align="C", new_x="LMARGIN", new_y="NEXT")


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
        ("1", "Overview"),
        ("2", "JWT Authentication"),
        ("3", "Auth API Endpoints"),
        ("4", "GDPR Compliance"),
        ("5", "Audit Logging"),
        ("6", "Security Headers"),
        ("7", "Rate Limiting"),
        ("8", "Database Migration"),
        ("9", "Configuration"),
        ("10", "Testing & Verification"),
    ]
    for num, title in chapters:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*pdf.DARK)
        label = f"Chapter {num}"
        pdf.cell(30, 7, label)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")


# ---------------------------------------------------------------
#  Chapter 1 - Overview
# ---------------------------------------------------------------

def _ch1_overview(pdf: CoursePDF) -> None:
    pdf.chapter_title("1", "Overview")

    pdf.section_title("1.1", "What Epic 6 Delivers")
    pdf.body(
        "Epic 6 transforms the EmoraTest AI Platform from an open API into a "
        "production-grade, secure system ready for real merchant onboarding. It "
        "introduces a complete authentication layer using JSON Web Tokens (JWT), "
        "implements GDPR compliance endpoints mandated by European regulation, adds "
        "audit logging for accountability, hardens HTTP responses with security "
        "headers, and rate-limits sensitive endpoints to prevent abuse."
    )

    pdf.body(
        "Before Epic 6, any HTTP client could access every endpoint. After Epic 6, "
        "merchants must register, authenticate, and present a valid JWT bearer token "
        "to access protected resources. Every state-changing request is logged for "
        "audit. Merchants can exercise their GDPR rights to export or delete personal data."
    )

    pdf.section_title("1.2", "Why Security Matters for E-Commerce Analytics")
    pdf.body(
        "An e-commerce analytics platform processes sensitive business data: conversion "
        "rates, revenue figures, customer session recordings, A/B test results, and "
        "intervention strategies. A breach exposes competitive intelligence and can "
        "violate customer privacy. For merchants operating in the EU, GDPR compliance "
        "is not optional - it carries fines of up to 4% of global annual turnover."
    )
    pdf.bullet("Authentication prevents unauthorized access to merchant dashboards and APIs.")
    pdf.bullet("Audit logging provides a forensic trail for incident response and compliance audits.")
    pdf.bullet("Security headers mitigate common web attacks (XSS, clickjacking, MIME sniffing).")
    pdf.bullet("Rate limiting protects against brute-force login attempts and API abuse.")
    pdf.bullet("GDPR endpoints ensure legal compliance for EU merchants and their customers.")

    pdf.section_title("1.3", "Jira Stories Covered")
    cols = [("Story", 30), ("Title", 80), ("Status", 30), ("Points", 25)]
    pdf.table_header(cols)
    stories = [
        ["CONV-56", "JWT Authentication Module", "Done", "8"],
        ["CONV-57", "Auth API Endpoints", "Done", "5"],
        ["CONV-58", "GDPR Compliance Endpoints", "Done", "8"],
        ["CONV-59", "Audit Logging Middleware", "Done", "5"],
        ["CONV-60", "Security Headers Middleware", "Done", "3"],
        ["CONV-61", "Rate Limiting Configuration", "Done", "5"],
        ["CONV-62", "Database Migration 004", "Done", "3"],
        ["CONV-63", "Integration Testing", "Done", "5"],
    ]
    widths = [30, 80, 30, 25]
    for row in stories:
        pdf.table_row(row, widths)

    pdf.tip_box(
        "Key Achievement",
        "All 8 stories completed with 104 tests passing and zero ruff lint errors."
    )


# ---------------------------------------------------------------
#  Chapter 2 - JWT Authentication
# ---------------------------------------------------------------

def _ch2_jwt_auth(pdf: CoursePDF) -> None:
    pdf.chapter_title("2", "JWT Authentication")

    pdf.section_title("2.1", "Architecture Overview")
    pdf.body(
        "The authentication system is implemented in backend/app/auth.py and follows "
        "industry best practices for token-based authentication. It uses three core "
        "libraries: passlib for password hashing, python-jose for JWT encoding/decoding, "
        "and bcrypt as the underlying hashing algorithm."
    )
    pdf.body(
        "The flow is straightforward: a merchant registers with email and password, "
        "the password is hashed with bcrypt before storage, and on login the server "
        "verifies the password and issues a signed JWT. Subsequent requests include "
        "this token in the Authorization header as a Bearer token."
    )

    pdf.section_title("2.2", "Password Hashing with bcrypt")
    pdf.body(
        "Passwords are never stored in plaintext. The passlib CryptContext is configured "
        "with bcrypt as the sole hashing scheme, and auto-deprecation is enabled so "
        "future algorithm upgrades are transparent."
    )
    pdf.code_block(
        'from passlib.context import CryptContext\n'
        '\n'
        'pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")\n'
        '\n'
        'def hash_password(password: str) -> str:\n'
        '    """Hash a plaintext password using bcrypt."""\n'
        '    return pwd_context.hash(password)\n'
        '\n'
        'def verify_password(plain: str, hashed: str) -> bool:\n'
        '    """Verify a plaintext password against a bcrypt hash."""\n'
        '    return pwd_context.verify(plain, hashed)'
    )
    pdf.body(
        "bcrypt is a deliberately slow hashing function. Each hash computation takes "
        "~100ms by default (tunable via work factor), making brute-force attacks "
        "computationally expensive. The auto-deprecation feature means that if a "
        "merchant logs in with a hash from an older scheme, passlib will transparently "
        "re-hash with the current scheme."
    )

    pdf.section_title("2.3", "JWT Token Creation")
    pdf.body(
        "Tokens are created using python-jose with the HS256 algorithm. Each token "
        "contains the merchant's email as the 'sub' (subject) claim and an expiration "
        "timestamp. The signing key is loaded from the JWT_SECRET_KEY configuration."
    )
    pdf.code_block(
        'from jose import JWTError, jwt\n'
        'from datetime import datetime, timedelta\n'
        'from app.config import settings\n'
        '\n'
        'def create_access_token(\n'
        '    data: dict,\n'
        '    expires_delta: timedelta | None = None\n'
        ') -> str:\n'
        '    to_encode = data.copy()\n'
        '    expire = datetime.utcnow() + (\n'
        '        expires_delta or timedelta(\n'
        '            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES\n'
        '        )\n'
        '    )\n'
        '    to_encode.update({"exp": expire})\n'
        '    return jwt.encode(\n'
        '        to_encode,\n'
        '        settings.JWT_SECRET_KEY,\n'
        '        algorithm=settings.JWT_ALGORITHM\n'
        '    )'
    )

    pdf.section_title("2.4", "Token Verification & Dependency Injection")
    pdf.body(
        "FastAPI's dependency injection system is used to protect endpoints. The "
        "get_current_merchant dependency extracts the Bearer token from the "
        "Authorization header, decodes and validates it, then returns the merchant "
        "record from the database. If the token is missing, expired, or invalid, "
        "a 401 Unauthorized response is returned."
    )
    pdf.code_block(
        'from fastapi import Depends, HTTPException, status\n'
        'from fastapi.security import OAuth2PasswordBearer\n'
        '\n'
        'oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")\n'
        '\n'
        'async def get_current_merchant(\n'
        '    token: str = Depends(oauth2_scheme),\n'
        '    db: AsyncSession = Depends(get_db)\n'
        ') -> Merchant:\n'
        '    credentials_exception = HTTPException(\n'
        '        status_code=status.HTTP_401_UNAUTHORIZED,\n'
        '        detail="Could not validate credentials",\n'
        '        headers={"WWW-Authenticate": "Bearer"},\n'
        '    )\n'
        '    try:\n'
        '        payload = jwt.decode(\n'
        '            token,\n'
        '            settings.JWT_SECRET_KEY,\n'
        '            algorithms=[settings.JWT_ALGORITHM]\n'
        '        )\n'
        '        email: str = payload.get("sub")\n'
        '        if email is None:\n'
        '            raise credentials_exception\n'
        '    except JWTError:\n'
        '        raise credentials_exception\n'
        '    merchant = await get_merchant_by_email(db, email)\n'
        '    if merchant is None:\n'
        '        raise credentials_exception\n'
        '    return merchant'
    )

    pdf.warn_box(
        "Security Note",
        "Always use HTTPS in production to prevent token interception.\n"
        "Never log JWT tokens - they are bearer credentials.\n"
        "Rotate JWT_SECRET_KEY periodically and on any suspected compromise."
    )


# ---------------------------------------------------------------
#  Chapter 3 - Auth API Endpoints
# ---------------------------------------------------------------

def _ch3_auth_endpoints(pdf: CoursePDF) -> None:
    pdf.chapter_title("3", "Auth API Endpoints")

    pdf.section_title("3.1", "POST /auth/register")
    pdf.body(
        "Creates a new merchant account. Accepts email, password, and company_name. "
        "Validates email format, checks for duplicates, hashes the password with "
        "bcrypt, and returns a JWT access token so the merchant is immediately "
        "logged in after registration."
    )
    pdf.subsection("Request Schema")
    pdf.code_block(
        'POST /auth/register\n'
        'Content-Type: application/json\n'
        '\n'
        '{\n'
        '  "email": "merchant@example.com",\n'
        '  "password": "SecureP@ss123",\n'
        '  "company_name": "Acme Store"\n'
        '}'
    )
    pdf.subsection("Response Schema (201 Created)")
    pdf.code_block(
        '{\n'
        '  "access_token": "eyJhbGciOiJIUzI1NiIs...",\n'
        '  "token_type": "bearer",\n'
        '  "merchant": {\n'
        '    "id": "uuid-here",\n'
        '    "email": "merchant@example.com",\n'
        '    "company_name": "Acme Store",\n'
        '    "onboarding_completed": false\n'
        '  }\n'
        '}'
    )
    pdf.subsection("Error Responses")
    pdf.bullet("400 Bad Request - Invalid email format")
    pdf.bullet("409 Conflict - Email already registered")
    pdf.bullet("422 Unprocessable Entity - Missing required fields")

    pdf.section_title("3.2", "POST /auth/login")
    pdf.body(
        "Authenticates an existing merchant. Uses OAuth2 password flow compatible "
        "form data (username field maps to email). Returns a JWT access token on "
        "success. Failed attempts are rate-limited to prevent brute-force attacks."
    )
    pdf.subsection("Request Schema")
    pdf.code_block(
        'POST /auth/login\n'
        'Content-Type: application/x-www-form-urlencoded\n'
        '\n'
        'username=merchant@example.com&password=SecureP@ss123'
    )
    pdf.subsection("Response Schema (200 OK)")
    pdf.code_block(
        '{\n'
        '  "access_token": "eyJhbGciOiJIUzI1NiIs...",\n'
        '  "token_type": "bearer"\n'
        '}'
    )
    pdf.subsection("Error Responses")
    pdf.bullet("401 Unauthorized - Incorrect email or password")
    pdf.bullet("429 Too Many Requests - Rate limit exceeded")

    pdf.section_title("3.3", "GET /auth/me")
    pdf.body(
        "Returns the currently authenticated merchant's profile. Requires a valid "
        "JWT Bearer token in the Authorization header. This endpoint is the primary "
        "way the frontend dashboard fetches the merchant's identity after login."
    )
    pdf.subsection("Request")
    pdf.code_block(
        'GET /auth/me\n'
        'Authorization: Bearer eyJhbGciOiJIUzI1NiIs...'
    )
    pdf.subsection("Response Schema (200 OK)")
    pdf.code_block(
        '{\n'
        '  "id": "uuid-here",\n'
        '  "email": "merchant@example.com",\n'
        '  "company_name": "Acme Store",\n'
        '  "onboarding_completed": true,\n'
        '  "gdpr_consent": true,\n'
        '  "gdpr_consent_at": "2026-04-10T14:30:00Z"\n'
        '}'
    )

    pdf.section_title("3.4", "POST /auth/onboarding-complete")
    pdf.body(
        "Marks the merchant's onboarding as completed. Called after the merchant "
        "finishes the initial setup wizard in the dashboard. Sets the "
        "onboarding_completed flag to true in the database. Requires authentication."
    )
    pdf.subsection("Response Schema (200 OK)")
    pdf.code_block(
        '{\n'
        '  "message": "Onboarding completed successfully",\n'
        '  "onboarding_completed": true\n'
        '}'
    )


# ---------------------------------------------------------------
#  Chapter 4 - GDPR Compliance
# ---------------------------------------------------------------

def _ch4_gdpr(pdf: CoursePDF) -> None:
    pdf.chapter_title("4", "GDPR Compliance")

    pdf.section_title("4.1", "Regulatory Background")
    pdf.body(
        "The General Data Protection Regulation (GDPR) is a European Union regulation "
        "that governs how personal data must be handled. For EmoraTest, this affects "
        "merchant account data, session analytics linked to end-users, and any "
        "personally identifiable information (PII) processed by the platform."
    )
    pdf.body(
        "Three GDPR articles are directly implemented in Epic 6:"
    )
    pdf.bullet("Article 7 - Conditions for consent: explicit, informed, freely given consent")
    pdf.bullet("Article 17 - Right to erasure ('right to be forgotten'): delete personal data on request")
    pdf.bullet("Article 20 - Right to data portability: export personal data in a structured format")

    pdf.section_title("4.2", "POST /auth/gdpr/consent")
    pdf.body(
        "Records the merchant's explicit GDPR consent. This endpoint stores a boolean "
        "consent flag along with a timestamp indicating when consent was given. "
        "Consent can be granted or withdrawn by sending consent: true or consent: false."
    )
    pdf.code_block(
        'POST /auth/gdpr/consent\n'
        'Authorization: Bearer <token>\n'
        'Content-Type: application/json\n'
        '\n'
        '{\n'
        '  "consent": true\n'
        '}\n'
        '\n'
        '# Response 200 OK\n'
        '{\n'
        '  "message": "GDPR consent recorded",\n'
        '  "gdpr_consent": true,\n'
        '  "gdpr_consent_at": "2026-04-10T14:30:00Z"\n'
        '}'
    )

    pdf.section_title("4.3", "GET /auth/gdpr/export (Article 20)")
    pdf.body(
        "Implements GDPR Article 20 - Right to Data Portability. Returns all personal "
        "data the platform holds about the merchant in a structured, commonly used, "
        "machine-readable JSON format. This allows the merchant to transfer their data "
        "to another service provider."
    )
    pdf.subsection("Data Included in Export")
    pdf.bullet("Merchant profile: id, email, company_name, created_at, updated_at")
    pdf.bullet("GDPR consent records: consent status and timestamps")
    pdf.bullet("Onboarding status and completion date")
    pdf.bullet("Sessions created by the merchant's SDK integration")
    pdf.bullet("Experiments and their configurations")
    pdf.bullet("Interventions triggered for the merchant's store")
    pdf.bullet("Analytics aggregates and cohort definitions")

    pdf.code_block(
        'GET /auth/gdpr/export\n'
        'Authorization: Bearer <token>\n'
        '\n'
        '# Response 200 OK\n'
        '{\n'
        '  "merchant": {\n'
        '    "id": "uuid-here",\n'
        '    "email": "merchant@example.com",\n'
        '    "company_name": "Acme Store",\n'
        '    "created_at": "2026-03-01T10:00:00Z"\n'
        '  },\n'
        '  "sessions_count": 1542,\n'
        '  "experiments": [...],\n'
        '  "interventions": [...],\n'
        '  "exported_at": "2026-04-10T14:35:00Z"\n'
        '}'
    )

    pdf.section_title("4.4", "DELETE /auth/gdpr/delete (Article 17)")
    pdf.body(
        "Implements GDPR Article 17 - Right to Erasure. This is the most destructive "
        "endpoint in the system and permanently deletes all merchant data. The deletion "
        "is cascading and irreversible."
    )
    pdf.subsection("Deletion Order (Cascading)")
    pdf.numbered(1, "All interventions associated with the merchant's experiments")
    pdf.numbered(2, "All experiments owned by the merchant")
    pdf.numbered(3, "All session events linked to the merchant's sessions")
    pdf.numbered(4, "All sessions tracked for the merchant's store")
    pdf.numbered(5, "All cohort analytics and aggregates")
    pdf.numbered(6, "The merchant record itself (email, password_hash, company_name)")

    pdf.code_block(
        'DELETE /auth/gdpr/delete\n'
        'Authorization: Bearer <token>\n'
        '\n'
        '# Response 200 OK\n'
        '{\n'
        '  "message": "All personal data has been deleted",\n'
        '  "deleted_resources": {\n'
        '    "merchant": true,\n'
        '    "sessions": 1542,\n'
        '    "experiments": 5,\n'
        '    "interventions": 23\n'
        '  }\n'
        '}'
    )

    pdf.warn_box(
        "Irreversible Operation",
        "The GDPR delete endpoint permanently erases ALL merchant data.\n"
        "There is no soft-delete or recovery mechanism.\n"
        "The frontend should require explicit confirmation before calling this."
    )


# ---------------------------------------------------------------
#  Chapter 5 - Audit Logging
# ---------------------------------------------------------------

def _ch5_audit_logging(pdf: CoursePDF) -> None:
    pdf.chapter_title("5", "Audit Logging")

    pdf.section_title("5.1", "Why Audit Logging Matters")
    pdf.body(
        "Audit logging provides an immutable record of all state-changing operations "
        "in the system. It is essential for security incident response, compliance "
        "audits (SOC 2, GDPR Article 30), debugging production issues, and "
        "understanding system usage patterns."
    )

    pdf.section_title("5.2", "AuditLogMiddleware Implementation")
    pdf.body(
        "The audit logging system is implemented as a Starlette/FastAPI middleware "
        "that intercepts every incoming HTTP request. It selectively logs requests "
        "that use state-changing HTTP methods: POST, PUT, PATCH, and DELETE. "
        "GET requests are excluded to avoid log volume explosion."
    )
    pdf.code_block(
        'import logging\n'
        'from starlette.middleware.base import (\n'
        '    BaseHTTPMiddleware\n'
        ')\n'
        'from starlette.requests import Request\n'
        '\n'
        'logger = logging.getLogger("audit")\n'
        '\n'
        'class AuditLogMiddleware(BaseHTTPMiddleware):\n'
        '    LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}\n'
        '\n'
        '    async def dispatch(self, request: Request, call_next):\n'
        '        response = await call_next(request)\n'
        '        if request.method in self.LOGGED_METHODS:\n'
        '            logger.info(\n'
        '                "AUDIT | %s %s | status=%d | ip=%s",\n'
        '                request.method,\n'
        '                request.url.path,\n'
        '                response.status_code,\n'
        '                request.client.host if request.client\n'
        '                    else "unknown",\n'
        '            )\n'
        '        return response'
    )

    pdf.section_title("5.3", "Log Format and Fields")
    pdf.body("Each audit log entry contains the following fields:")
    pdf.bullet("Timestamp - ISO 8601 format from Python's logging configuration")
    pdf.bullet("Log level - Always INFO for audit entries")
    pdf.bullet("Prefix - 'AUDIT' marker for easy grep/filtering")
    pdf.bullet("HTTP method - POST, PUT, PATCH, or DELETE")
    pdf.bullet("URL path - The endpoint path that was accessed")
    pdf.bullet("Status code - The HTTP response status code")
    pdf.bullet("Client IP - The remote IP address of the requester")

    pdf.subsection("Example Log Output")
    pdf.code_block(
        '2026-04-10 14:30:00 INFO audit AUDIT | POST /auth/register | status=201 | ip=192.168.1.1\n'
        '2026-04-10 14:30:05 INFO audit AUDIT | POST /auth/login | status=200 | ip=192.168.1.1\n'
        '2026-04-10 14:31:00 INFO audit AUDIT | DELETE /auth/gdpr/delete | status=200 | ip=192.168.1.1'
    )

    pdf.tip_box(
        "Production Recommendation",
        "In production, route audit logs to a separate log stream (e.g., CloudWatch,\n"
        "Datadog, or ELK stack) for long-term retention and search. Consider adding\n"
        "the authenticated merchant ID to each log entry for traceability."
    )


# ---------------------------------------------------------------
#  Chapter 6 - Security Headers
# ---------------------------------------------------------------

def _ch6_security_headers(pdf: CoursePDF) -> None:
    pdf.chapter_title("6", "Security Headers")

    pdf.section_title("6.1", "SecurityHeadersMiddleware")
    pdf.body(
        "The SecurityHeadersMiddleware adds defensive HTTP headers to every response. "
        "These headers instruct browsers to enable built-in security mechanisms that "
        "mitigate common web vulnerabilities like cross-site scripting (XSS), "
        "clickjacking, and MIME type confusion attacks."
    )
    pdf.code_block(
        'class SecurityHeadersMiddleware(BaseHTTPMiddleware):\n'
        '    async def dispatch(self, request, call_next):\n'
        '        response = await call_next(request)\n'
        '        response.headers["X-Content-Type-Options"] = (\n'
        '            "nosniff"\n'
        '        )\n'
        '        response.headers["X-Frame-Options"] = "DENY"\n'
        '        response.headers["X-XSS-Protection"] = (\n'
        '            "1; mode=block"\n'
        '        )\n'
        '        response.headers["Referrer-Policy"] = (\n'
        '            "strict-origin-when-cross-origin"\n'
        '        )\n'
        '        response.headers["Cache-Control"] = (\n'
        '            "no-store, no-cache, must-revalidate"\n'
        '        )\n'
        '        response.headers["Permissions-Policy"] = (\n'
        '            "camera=(), microphone=(), geolocation=()"\n'
        '        )\n'
        '        return response'
    )

    pdf.section_title("6.2", "Header Explanations")

    pdf.subsection("X-Content-Type-Options: nosniff")
    pdf.body(
        "Prevents browsers from MIME-sniffing a response away from the declared "
        "Content-Type. Without this header, a browser might interpret a JSON response "
        "as HTML, enabling XSS attacks through crafted API responses."
    )

    pdf.subsection("X-Frame-Options: DENY")
    pdf.body(
        "Prevents the page from being embedded in an iframe. This is the primary "
        "defense against clickjacking attacks, where an attacker overlays a "
        "transparent iframe over a legitimate-looking page to trick users into "
        "clicking on hidden elements."
    )

    pdf.subsection("X-XSS-Protection: 1; mode=block")
    pdf.body(
        "Enables the browser's built-in XSS filter and instructs it to block the "
        "page entirely rather than attempting to sanitize the content. While modern "
        "browsers are moving toward Content-Security-Policy, this header provides "
        "defense-in-depth for older browsers."
    )

    pdf.subsection("Referrer-Policy: strict-origin-when-cross-origin")
    pdf.body(
        "Controls how much referrer information is included with requests. For "
        "same-origin requests, the full URL is sent. For cross-origin requests, "
        "only the origin (scheme + host + port) is sent. For downgrades (HTTPS to "
        "HTTP), no referrer is sent at all. This protects sensitive URL parameters "
        "from leaking to third-party services."
    )

    pdf.subsection("Cache-Control: no-store, no-cache, must-revalidate")
    pdf.body(
        "Prevents caching of API responses. For a security-sensitive API that returns "
        "authentication tokens and personal data, caching could expose sensitive "
        "information through shared caches, browser history, or the back button. "
        "This is especially important for the /auth/me and /auth/gdpr/export endpoints."
    )

    pdf.subsection("Permissions-Policy: camera=(), microphone=(), geolocation=()")
    pdf.body(
        "Restricts browser features that the application does not need. By explicitly "
        "denying camera, microphone, and geolocation access, the application reduces "
        "its attack surface. Even if an XSS vulnerability were exploited, the attacker "
        "could not access these sensitive device capabilities."
    )


# ---------------------------------------------------------------
#  Chapter 7 - Rate Limiting
# ---------------------------------------------------------------

def _ch7_rate_limiting(pdf: CoursePDF) -> None:
    pdf.chapter_title("7", "Rate Limiting")

    pdf.section_title("7.1", "Why Rate Limiting")
    pdf.body(
        "Rate limiting is a critical security control that prevents abuse of the API. "
        "Without rate limits, an attacker could perform brute-force login attempts, "
        "overwhelm the server with expensive analytics queries, or exhaust database "
        "connections. EmoraTest uses slowapi, which is built on top of the popular "
        "limits library and integrates natively with FastAPI."
    )

    pdf.section_title("7.2", "slowapi Configuration")
    pdf.code_block(
        'from slowapi import Limiter\n'
        'from slowapi.util import get_remote_address\n'
        '\n'
        'limiter = Limiter(\n'
        '    key_func=get_remote_address,\n'
        '    default_limits=["200/minute"],\n'
        '    storage_uri="memory://",\n'
        ')\n'
        '\n'
        '# Attach to the FastAPI app\n'
        'app.state.limiter = limiter\n'
        'app.add_exception_handler(\n'
        '    RateLimitExceeded, _rate_limit_handler\n'
        ')'
    )
    pdf.body(
        "The limiter is configured with get_remote_address as the key function, which "
        "extracts the client IP from the request. In production behind a reverse proxy, "
        "this should be updated to use X-Forwarded-For. The default storage backend is "
        "in-memory, suitable for single-process deployments. For multi-worker "
        "deployments, switch to Redis storage."
    )

    pdf.section_title("7.3", "Rate Tiers by Endpoint")
    cols = [("Endpoint", 55), ("Method", 20), ("Limit", 35), ("Reason", 60)]
    pdf.table_header(cols)
    rows = [
        ["/auth/register", "POST", "5/minute", "Prevent mass account creation"],
        ["/auth/login", "POST", "10/minute", "Prevent brute-force attacks"],
        ["/auth/gdpr/export", "GET", "3/minute", "Expensive data aggregation"],
        ["/auth/gdpr/delete", "DELETE", "1/minute", "Irreversible destructive op"],
        ["/api/* (default)", "ALL", "200/minute", "General API protection"],
    ]
    widths = [55, 20, 35, 60]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("7.4", "Rate Limit Response")
    pdf.body(
        "When a rate limit is exceeded, the API returns a 429 Too Many Requests response "
        "with a Retry-After header indicating when the client can retry."
    )
    pdf.code_block(
        'HTTP/1.1 429 Too Many Requests\n'
        'Retry-After: 60\n'
        'Content-Type: application/json\n'
        '\n'
        '{\n'
        '  "error": "Rate limit exceeded",\n'
        '  "detail": "10 per 1 minute",\n'
        '  "retry_after": 60\n'
        '}'
    )

    pdf.tip_box(
        "Production Tip",
        "For multi-worker deployments (gunicorn with uvicorn workers),\n"
        "switch storage_uri to 'redis://localhost:6379' so rate limits\n"
        "are shared across all workers."
    )


# ---------------------------------------------------------------
#  Chapter 8 - Database Migration
# ---------------------------------------------------------------

def _ch8_migration(pdf: CoursePDF) -> None:
    pdf.chapter_title("8", "Database Migration")

    pdf.section_title("8.1", "Migration 004 Overview")
    pdf.body(
        "Migration 004 extends the merchants table with columns required for "
        "authentication and GDPR compliance. It is designed as a non-destructive, "
        "additive migration - all new columns are nullable or have default values, "
        "so existing merchant records are not affected."
    )

    pdf.section_title("8.2", "New Columns")
    cols = [("Column", 45), ("Type", 30), ("Default", 30), ("Purpose", 65)]
    pdf.table_header(cols)
    rows = [
        ["password_hash", "VARCHAR(255)", "NULL", "bcrypt-hashed password"],
        ["gdpr_consent", "BOOLEAN", "FALSE", "GDPR consent status"],
        ["gdpr_consent_at", "TIMESTAMP", "NULL", "When consent was given"],
        ["onboarding_completed", "BOOLEAN", "FALSE", "Onboarding wizard status"],
    ]
    widths = [45, 30, 30, 65]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.section_title("8.3", "Migration Script")
    pdf.code_block(
        '"""004 - Add auth and GDPR columns to merchants.\n'
        '\n'
        'Revision ID: 004\n'
        'Revises: 003\n'
        '"""\n'
        '\n'
        'from alembic import op\n'
        'import sqlalchemy as sa\n'
        '\n'
        'def upgrade():\n'
        '    op.add_column("merchants", sa.Column(\n'
        '        "password_hash", sa.String(255), nullable=True\n'
        '    ))\n'
        '    op.add_column("merchants", sa.Column(\n'
        '        "gdpr_consent",\n'
        '        sa.Boolean,\n'
        '        server_default=sa.text("false"),\n'
        '        nullable=False,\n'
        '    ))\n'
        '    op.add_column("merchants", sa.Column(\n'
        '        "gdpr_consent_at", sa.DateTime, nullable=True\n'
        '    ))\n'
        '    op.add_column("merchants", sa.Column(\n'
        '        "onboarding_completed",\n'
        '        sa.Boolean,\n'
        '        server_default=sa.text("false"),\n'
        '        nullable=False,\n'
        '    ))\n'
        '\n'
        'def downgrade():\n'
        '    op.drop_column("merchants", "onboarding_completed")\n'
        '    op.drop_column("merchants", "gdpr_consent_at")\n'
        '    op.drop_column("merchants", "gdpr_consent")\n'
        '    op.drop_column("merchants", "password_hash")'
    )

    pdf.section_title("8.4", "Running the Migration")
    pdf.code_block(
        '# Apply migration\n'
        'alembic upgrade head\n'
        '\n'
        '# Verify columns exist\n'
        'alembic current\n'
        '\n'
        '# Rollback if needed\n'
        'alembic downgrade -1'
    )

    pdf.warn_box(
        "Migration Safety",
        "Always back up the database before running migrations in production.\n"
        "The downgrade() function drops columns, which causes data loss.\n"
        "Test migrations on a staging environment first."
    )


# ---------------------------------------------------------------
#  Chapter 9 - Configuration
# ---------------------------------------------------------------

def _ch9_configuration(pdf: CoursePDF) -> None:
    pdf.chapter_title("9", "Configuration")

    pdf.section_title("9.1", "JWT Settings")
    pdf.body(
        "All JWT-related configuration is centralized in the Pydantic BaseSettings "
        "class in backend/app/config.py. Settings are loaded from environment "
        "variables or a .env file, with sensible defaults for development."
    )
    pdf.code_block(
        'from pydantic_settings import BaseSettings\n'
        '\n'
        'class Settings(BaseSettings):\n'
        '    # JWT Configuration\n'
        '    JWT_SECRET_KEY: str = "change-me-in-production"\n'
        '    JWT_ALGORITHM: str = "HS256"\n'
        '    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30\n'
        '\n'
        '    # Database\n'
        '    DATABASE_URL: str = "sqlite+aiosqlite:///./conv.db"\n'
        '\n'
        '    class Config:\n'
        '        env_file = ".env"\n'
        '        case_sensitive = True'
    )

    pdf.section_title("9.2", "Configuration Parameters Explained")

    pdf.subsection("JWT_SECRET_KEY")
    pdf.body(
        "The secret key used to sign and verify JWT tokens. Must be a long, random "
        "string in production. If this key is compromised, an attacker can forge "
        "valid tokens for any merchant. Generate with: openssl rand -hex 32"
    )

    pdf.subsection("JWT_ALGORITHM")
    pdf.body(
        "The algorithm used for JWT signing. HS256 (HMAC-SHA256) is the default and "
        "is appropriate for single-service architectures. For microservice architectures "
        "where multiple services need to verify tokens, consider RS256 (RSA) which uses "
        "asymmetric key pairs."
    )

    pdf.subsection("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    pdf.body(
        "Token lifetime in minutes. The default is 30 minutes. Shorter lifetimes "
        "improve security (less time for a stolen token to be used) but hurt user "
        "experience (more frequent re-authentication). In production, consider "
        "implementing refresh tokens for a better balance."
    )

    pdf.section_title("9.3", "Environment Variables (.env)")
    pdf.code_block(
        '# .env file for production\n'
        'JWT_SECRET_KEY=a1b2c3d4e5f6...long-random-hex-string\n'
        'JWT_ALGORITHM=HS256\n'
        'JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30\n'
        'DATABASE_URL=postgresql+asyncpg://user:pass@host/db'
    )

    pdf.warn_box(
        "Security Warning",
        "NEVER commit .env files to version control.\n"
        "NEVER use the default JWT_SECRET_KEY in production.\n"
        "Use a secrets manager (AWS Secrets Manager, Vault) for production keys."
    )


# ---------------------------------------------------------------
#  Chapter 10 - Testing & Verification
# ---------------------------------------------------------------

def _ch10_testing(pdf: CoursePDF) -> None:
    pdf.chapter_title("10", "Testing & Verification")

    pdf.section_title("10.1", "Test Suite Overview")
    pdf.body(
        "Epic 6 maintains the comprehensive test suite established in previous epics, "
        "with all 104 tests passing. The tests cover unit tests for authentication "
        "functions, integration tests for API endpoints, middleware tests for security "
        "headers and audit logging, and end-to-end auth flow tests."
    )

    pdf.section_title("10.2", "Testing the Auth Flow")
    pdf.subsection("Step 1: Register a New Merchant")
    pdf.code_block(
        'import httpx\n'
        '\n'
        'async with httpx.AsyncClient(base_url="http://localhost:8000") as client:\n'
        '    # Register\n'
        '    resp = await client.post("/auth/register", json={\n'
        '        "email": "test@example.com",\n'
        '        "password": "TestP@ss123",\n'
        '        "company_name": "Test Store"\n'
        '    })\n'
        '    assert resp.status_code == 201\n'
        '    token = resp.json()["access_token"]'
    )

    pdf.subsection("Step 2: Access Protected Endpoints")
    pdf.code_block(
        '    # Use the token\n'
        '    headers = {"Authorization": f"Bearer {token}"}\n'
        '    me = await client.get("/auth/me", headers=headers)\n'
        '    assert me.status_code == 200\n'
        '    assert me.json()["email"] == "test@example.com"'
    )

    pdf.subsection("Step 3: Test GDPR Endpoints")
    pdf.code_block(
        '    # Record consent\n'
        '    consent = await client.post(\n'
        '        "/auth/gdpr/consent",\n'
        '        json={"consent": True},\n'
        '        headers=headers\n'
        '    )\n'
        '    assert consent.status_code == 200\n'
        '\n'
        '    # Export data\n'
        '    export = await client.get(\n'
        '        "/auth/gdpr/export", headers=headers\n'
        '    )\n'
        '    assert export.status_code == 200\n'
        '    assert "merchant" in export.json()'
    )

    pdf.subsection("Step 4: Verify Unauthorized Access is Blocked")
    pdf.code_block(
        '    # Without token - should fail\n'
        '    resp = await client.get("/auth/me")\n'
        '    assert resp.status_code == 401\n'
        '\n'
        '    # With invalid token - should fail\n'
        '    bad_headers = {"Authorization": "Bearer invalid.token.here"}\n'
        '    resp = await client.get("/auth/me", headers=bad_headers)\n'
        '    assert resp.status_code == 401'
    )

    pdf.section_title("10.3", "Running the Full Test Suite")
    pdf.code_block(
        '# Run all tests with verbose output\n'
        'cd backend\n'
        'python -m pytest tests/ -v --tb=short\n'
        '\n'
        '# Expected output:\n'
        '# 104 passed in 8.23s\n'
        '\n'
        '# Run only auth tests\n'
        'python -m pytest tests/ -v -k "auth"\n'
        '\n'
        '# Run with coverage\n'
        'python -m pytest tests/ --cov=app --cov-report=term-missing'
    )

    pdf.section_title("10.4", "Lint Verification")
    pdf.body(
        "All code passes ruff linting with zero errors. Ruff is configured as the "
        "project's primary linter and is enforced in CI."
    )
    pdf.code_block(
        '# Run ruff lint check\n'
        'ruff check backend/\n'
        '\n'
        '# Expected output:\n'
        '# All checks passed!'
    )

    pdf.section_title("10.5", "Test Categories")
    cols = [("Category", 50), ("Count", 20), ("Coverage Area", 100)]
    pdf.table_header(cols)
    rows = [
        ["Unit - Password Hashing", "6", "hash_password, verify_password, edge cases"],
        ["Unit - JWT Functions", "8", "create_token, decode_token, expiry, invalid tokens"],
        ["Integration - Register", "10", "Success, duplicate email, invalid input, response schema"],
        ["Integration - Login", "8", "Success, wrong password, nonexistent user, rate limit"],
        ["Integration - GDPR", "12", "Consent, export, delete, unauthorized access"],
        ["Integration - Middleware", "10", "Security headers, audit log entries, rate limits"],
        ["End-to-End - Auth Flow", "8", "Register -> login -> access -> GDPR -> delete"],
        ["Existing Tests", "42", "Sessions, experiments, interventions, analytics"],
    ]
    widths = [50, 20, 100]
    for row in rows:
        pdf.table_row(row, widths)

    pdf.tip_box(
        "CI/CD Integration",
        "The test suite runs automatically in CI on every push.\n"
        "Both pytest (104 tests) and ruff (0 errors) must pass for a merge."
    )


# ---------------------------------------------------------------
#  Main
# ---------------------------------------------------------------

def main() -> None:
    import pathlib

    pdf = CoursePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    _cover(pdf)
    _toc(pdf)
    _ch1_overview(pdf)
    _ch2_jwt_auth(pdf)
    _ch3_auth_endpoints(pdf)
    _ch4_gdpr(pdf)
    _ch5_audit_logging(pdf)
    _ch6_security_headers(pdf)
    _ch7_rate_limiting(pdf)
    _ch8_migration(pdf)
    _ch9_configuration(pdf)
    _ch10_testing(pdf)

    out = pathlib.Path(__file__).resolve().parent / "Epic6_Security_Hardening_GDPR.pdf"
    pdf.output(str(out))
    print(f"PDF generated: {out}  ({out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
