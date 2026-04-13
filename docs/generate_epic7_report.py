"""Generate Epic 7 Course-Style Documentation PDF - First Merchant Onboarding.

Run:  python docs/generate_epic7_report.py

Produces: docs/Epic7_Merchant_Onboarding.pdf
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
        self.cell(0, 8, "EmoraTest - Epic 7: First Merchant Onboarding", align="L")
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


# -------------------------------------------------------------
#  Content helpers
# -------------------------------------------------------------

def _cover(pdf: CoursePDF) -> None:
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.cell(0, 14, "EmoraTest AI Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(0, 12, "Epic 7: First Merchant Onboarding", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 10, "Registration, Login, Onboarding Wizard, Protected Routes", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(*pdf.PRIMARY)
    pdf.set_line_width(1)
    cx = pdf.w / 2
    pdf.line(cx - 40, pdf.get_y(), cx + 40, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 8, "Jira Stories: CONV-61 through CONV-68", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Next.js 14  |  React 18  |  TypeScript 5  |  Tailwind v4  |  FastAPI", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Sprint 7  -  April 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(
        0, 7,
        "10 Chapters  |  Auth Flow  |  Onboarding Wizard  |  Protected Dashboard  |  Full API Client",
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
        ("1", "Overview"),
        ("2", "Auth Context Provider"),
        ("3", "Login Page"),
        ("4", "Registration Page"),
        ("5", "Onboarding Wizard"),
        ("6", "Protected Dashboard Routes"),
        ("7", "Sidebar User Info & Logout"),
        ("8", "API Client Updates"),
        ("9", "User Flow"),
        ("10", "Frontend Build & Deployment"),
    ]
    for num, title in chapters:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*pdf.DARK)
        label = f"Chapter {num}"
        pdf.cell(30, 7, label)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")


# -------------------------------------------------------------------
#  Chapter 1 - Overview
# -------------------------------------------------------------------

def _ch1(pdf: CoursePDF) -> None:
    pdf.chapter_title("1", "Overview")

    pdf.section_title("1.1", "What Epic 7 Delivers")
    pdf.body(
        "Epic 7 implements the complete merchant onboarding experience for the "
        "EmoraTest AI Platform. This epic bridges the gap between the backend API "
        "(Epic 4) and the merchant dashboard (Epic 5) by adding full authentication, "
        "registration, and a guided onboarding wizard that walks new merchants through "
        "setting up their account, retrieving their SDK key, and installing the "
        "EmoraTest JavaScript SDK on their storefront."
    )

    pdf.section_title("1.2", "Key Deliverables")
    pdf.bullet("Complete merchant authentication flow (register + login + logout)")
    pdf.bullet("React AuthContext provider with auto-login on page load")
    pdf.bullet("Protected dashboard routes with auth guard and redirect")
    pdf.bullet("4-step onboarding wizard with progress bar and copy-to-clipboard")
    pdf.bullet("Sidebar user info display with plan badge and logout button")
    pdf.bullet("API client updates for Bearer token injection in all requests")
    pdf.bullet("Frontend build verification and Docker deployment configuration")

    pdf.section_title("1.3", "Jira Stories Covered")
    pdf.body(
        "This epic addresses CONV-61 (Auth Context), CONV-62 (Login Page), "
        "CONV-63 (Registration Page), CONV-64 (Onboarding Wizard), "
        "CONV-65 (Protected Routes), CONV-66 (Sidebar User Info), "
        "CONV-67 (API Client Auth), and CONV-68 (Build & Deployment)."
    )

    pdf.section_title("1.4", "Architecture Context")
    pdf.body(
        "The onboarding flow sits at the boundary between public-facing pages "
        "(login, register) and the authenticated merchant dashboard. The auth "
        "layer is implemented as a React Context that wraps the entire application, "
        "providing a useAuth() hook for any component to access the current user, "
        "loading state, and auth actions (login, register, logout). The token is "
        "stored in localStorage and automatically attached to every API request via "
        "an Axios request interceptor."
    )

    pdf.code_block(
        "Public Routes          Authenticated Routes\n"
        "  /login       -->       /dashboard\n"
        "  /register    -->       /dashboard/sessions\n"
        "  /onboarding  -->       /dashboard/analytics\n"
        "                         /dashboard/experiments\n"
        "                         /dashboard/settings"
    )

    pdf.tip_box(
        "Architecture Note",
        "The AuthProvider wraps the root layout so every page has access to auth state.\n"
        "Protected routes check auth on mount and redirect to /login if no valid token."
    )


# -------------------------------------------------------------------
#  Chapter 2 - Auth Context Provider
# -------------------------------------------------------------------

def _ch2(pdf: CoursePDF) -> None:
    pdf.chapter_title("2", "Auth Context Provider")

    pdf.section_title("2.1", "React Context Pattern")
    pdf.body(
        "The auth system is built on the React Context API, a standard pattern for "
        "sharing global state across a component tree without prop drilling. The "
        "AuthContext is defined in src/contexts/auth.tsx and exports two key pieces: "
        "the AuthProvider component and the useAuth() custom hook."
    )

    pdf.section_title("2.2", "AuthProvider Component")
    pdf.body(
        "The AuthProvider wraps the application's root layout component. On mount, "
        "it checks localStorage for an existing JWT token. If found, it calls the "
        "/api/auth/me endpoint to validate the token and retrieve the current user "
        "profile. This enables automatic re-authentication when a merchant refreshes "
        "the page or returns to the app."
    )
    pdf.code_block(
        'export function AuthProvider({ children }: { children: React.ReactNode }) {\n'
        '  const [user, setUser] = useState<User | null>(null);\n'
        '  const [loading, setLoading] = useState(true);\n'
        '  const router = useRouter();\n'
        '\n'
        '  useEffect(() => {\n'
        '    const token = localStorage.getItem("token");\n'
        '    if (token) {\n'
        '      authMe()\n'
        '        .then((res) => setUser(res.data))\n'
        '        .catch(() => localStorage.removeItem("token"))\n'
        '        .finally(() => setLoading(false));\n'
        '    } else {\n'
        '      setLoading(false);\n'
        '    }\n'
        '  }, []);\n'
        '  // ... login, register, logout methods\n'
        '  return (\n'
        '    <AuthContext.Provider value={{ user, loading, login, register, logout }}>\n'
        '      {children}\n'
        '    </AuthContext.Provider>\n'
        '  );\n'
        '}'
    )

    pdf.section_title("2.3", "useAuth Hook")
    pdf.body(
        "The useAuth() hook provides a clean API for any component to access auth state. "
        "It returns the current user object (or null if unauthenticated), a loading boolean "
        "(true while the initial auth check is in progress), and action functions: login(), "
        "register(), and logout()."
    )
    pdf.code_block(
        'export function useAuth() {\n'
        '  const context = useContext(AuthContext);\n'
        '  if (!context) {\n'
        '    throw new Error("useAuth must be used within an AuthProvider");\n'
        '  }\n'
        '  return context;\n'
        '}'
    )

    pdf.section_title("2.4", "Token Management")
    pdf.body(
        "JWT tokens are stored in localStorage under the key 'token'. On successful "
        "login or registration, the token is saved immediately. On logout, it is removed. "
        "The Axios API client reads the token from localStorage on every request and "
        "attaches it as a Bearer token in the Authorization header."
    )
    pdf.bullet("Login: saves token to localStorage, sets user state, redirects to /dashboard")
    pdf.bullet("Register: saves token + SDK key to localStorage, redirects to /onboarding")
    pdf.bullet("Logout: removes token from localStorage, clears user state, redirects to /login")
    pdf.bullet("Page refresh: reads token from localStorage, calls /api/auth/me to restore session")

    pdf.warn_box(
        "Security Consideration",
        "localStorage tokens are vulnerable to XSS attacks. In production,\n"
        "consider migrating to HTTP-only cookies or a BFF (Backend-for-Frontend)\n"
        "pattern for token management."
    )


# -------------------------------------------------------------------
#  Chapter 3 - Login Page
# -------------------------------------------------------------------

def _ch3(pdf: CoursePDF) -> None:
    pdf.chapter_title("3", "Login Page")

    pdf.section_title("3.1", "Route Configuration")
    pdf.body(
        "The login page is accessible at /login and is a public route (no auth required). "
        "It is implemented as a Next.js page component at src/app/login/page.tsx. The page "
        "uses the 'use client' directive since it relies on React state and the useAuth hook."
    )

    pdf.section_title("3.2", "Form Fields")
    pdf.body("The login form captures two fields:")
    pdf.bullet("Email: text input with type='email', required validation, placeholder text")
    pdf.bullet("Password: text input with type='password', required validation, minimum 6 characters")

    pdf.code_block(
        'export default function LoginPage() {\n'
        '  const { login } = useAuth();\n'
        '  const [email, setEmail] = useState("");\n'
        '  const [password, setPassword] = useState("");\n'
        '  const [error, setError] = useState("");\n'
        '  const [loading, setLoading] = useState(false);\n'
        '\n'
        '  const handleSubmit = async (e: FormEvent) => {\n'
        '    e.preventDefault();\n'
        '    setError("");\n'
        '    setLoading(true);\n'
        '    try {\n'
        '      await login(email, password);\n'
        '    } catch (err: any) {\n'
        '      setError(err.response?.data?.detail || "Login failed");\n'
        '    } finally {\n'
        '      setLoading(false);\n'
        '    }\n'
        '  };\n'
        '  // ... return JSX form\n'
        '}'
    )

    pdf.section_title("3.3", "Error Handling")
    pdf.body(
        "The login page displays error messages returned from the API in a red alert box "
        "above the form. Common errors include 'Invalid credentials' (401) and network "
        "errors. The error state is cleared on each new submission attempt."
    )
    pdf.bullet("401 Unauthorized: 'Invalid email or password' message displayed")
    pdf.bullet("422 Validation Error: field-level error messages from the API")
    pdf.bullet("Network Error: 'Unable to connect to server' fallback message")

    pdf.section_title("3.4", "Redirect After Login")
    pdf.body(
        "On successful login, the auth context's login() function stores the JWT token "
        "in localStorage, fetches the user profile via /api/auth/me, sets the user state, "
        "and calls router.push('/dashboard') to redirect to the protected dashboard. If "
        "the user is already authenticated (token exists and is valid), the login page "
        "automatically redirects to /dashboard on mount."
    )

    pdf.tip_box(
        "UX Pattern",
        "The login button shows a loading spinner while the request is in flight,\n"
        "preventing double submissions and providing visual feedback to the user."
    )


# -------------------------------------------------------------------
#  Chapter 4 - Registration Page
# -------------------------------------------------------------------

def _ch4(pdf: CoursePDF) -> None:
    pdf.chapter_title("4", "Registration Page")

    pdf.section_title("4.1", "Route Configuration")
    pdf.body(
        "The registration page is accessible at /register and is a public route. "
        "It is implemented at src/app/register/page.tsx with the 'use client' directive. "
        "The page provides a comprehensive signup form for new merchants."
    )

    pdf.section_title("4.2", "Form Fields")
    pdf.body("The registration form captures four fields:")
    pdf.bullet("Email: text input with type='email', required, validated for proper email format")
    pdf.bullet("Password: text input with type='password', required, minimum 8 characters with strength indicator")
    pdf.bullet("Shop Domain: text input for the merchant's storefront URL (e.g., mystore.shopify.com)")
    pdf.bullet("GDPR Consent: checkbox that must be checked to proceed, with link to privacy policy")

    pdf.code_block(
        'interface RegisterFormData {\n'
        '  email: string;\n'
        '  password: string;\n'
        '  shop_domain: string;\n'
        '  gdpr_consent: boolean;\n'
        '}\n'
        '\n'
        'const handleSubmit = async (e: FormEvent) => {\n'
        '  e.preventDefault();\n'
        '  if (!formData.gdpr_consent) {\n'
        '    setError("You must accept the privacy policy");\n'
        '    return;\n'
        '  }\n'
        '  try {\n'
        '    await register(formData);\n'
        '  } catch (err: any) {\n'
        '    setError(err.response?.data?.detail || "Registration failed");\n'
        '  }\n'
        '};'
    )

    pdf.section_title("4.3", "Validation")
    pdf.body(
        "Client-side validation runs before submission. The email must be a valid format, "
        "the password must be at least 8 characters, the shop domain must not be empty, "
        "and GDPR consent must be checked. Server-side validation catches duplicates "
        "(409 Conflict if the email is already registered)."
    )

    pdf.section_title("4.4", "SDK Key Storage")
    pdf.body(
        "After a successful registration, the API returns both a JWT token and the "
        "merchant's unique SDK key. The registration handler stores the token in "
        "localStorage under 'token' and the SDK key under 'sdk_key'. The SDK key is "
        "then displayed during the onboarding wizard so the merchant can copy it and "
        "install the EmoraTest SDK on their storefront."
    )
    pdf.code_block(
        'const register = async (data: RegisterFormData) => {\n'
        '  const res = await authRegister(data);\n'
        '  localStorage.setItem("token", res.data.access_token);\n'
        '  localStorage.setItem("sdk_key", res.data.sdk_key);\n'
        '  const me = await authMe();\n'
        '  setUser(me.data);\n'
        '  router.push("/onboarding");\n'
        '};'
    )

    pdf.warn_box(
        "Important",
        "The SDK key is only returned once during registration. The merchant should\n"
        "copy it during onboarding. It can also be retrieved later from the Settings page."
    )


# -------------------------------------------------------------------
#  Chapter 5 - Onboarding Wizard
# -------------------------------------------------------------------

def _ch5(pdf: CoursePDF) -> None:
    pdf.chapter_title("5", "Onboarding Wizard")

    pdf.section_title("5.1", "Route & Layout")
    pdf.body(
        "The onboarding wizard is accessible at /onboarding and is shown immediately "
        "after registration. It is implemented at src/app/onboarding/page.tsx as a "
        "multi-step form wizard. The page uses a standalone layout without the dashboard "
        "sidebar, providing a focused, distraction-free experience."
    )

    pdf.section_title("5.2", "Wizard Steps")
    pdf.body("The wizard consists of 4 sequential steps:")

    pdf.subsection("Step 1: Welcome")
    pdf.body(
        "A welcome screen that greets the merchant by name and provides an overview "
        "of what the onboarding process covers. It sets expectations: 'In the next few "
        "steps, you will get your SDK key and learn how to install the EmoraTest "
        "tracking snippet on your website.' A single 'Get Started' button advances to step 2."
    )

    pdf.subsection("Step 2: Your SDK Key")
    pdf.body(
        "Displays the merchant's unique SDK key in a prominent, styled code block. "
        "The key is retrieved from localStorage (stored during registration). A "
        "'Copy to Clipboard' button uses the navigator.clipboard API to copy the key. "
        "Visual feedback (green checkmark, 'Copied!' text) confirms the copy action."
    )
    pdf.code_block(
        'const handleCopy = async () => {\n'
        '  await navigator.clipboard.writeText(sdkKey);\n'
        '  setCopied(true);\n'
        '  setTimeout(() => setCopied(false), 2000);\n'
        '};'
    )

    pdf.subsection("Step 3: Install SDK")
    pdf.body(
        "Provides the merchant with the exact HTML snippet to install on their website. "
        "The code block shows the script tag with the merchant's SDK key pre-filled. "
        "Installation instructions cover where to place the snippet (before the closing "
        "</body> tag) and how to verify the installation."
    )
    pdf.code_block(
        '<!-- EmoraTest SDK Installation -->\n'
        '<script\n'
        '  src="https://cdn.emoratest.ai/sdk/v1/tracker.min.js"\n'
        '  data-key="YOUR_SDK_KEY"\n'
        '  async\n'
        '></script>'
    )

    pdf.subsection("Step 4: Done")
    pdf.body(
        "A success screen with a confetti animation congratulating the merchant. "
        "It confirms that their account is set up and the SDK is ready to collect data. "
        "A 'Go to Dashboard' button navigates to /dashboard."
    )

    pdf.section_title("5.3", "Progress Bar")
    pdf.body(
        "A horizontal progress bar at the top of the wizard indicates the current step "
        "out of 4. Each step is represented by a numbered circle connected by lines. "
        "Completed steps show a green checkmark, the current step is highlighted in "
        "primary blue, and future steps are gray. The progress bar updates reactively "
        "as the merchant advances through the steps."
    )
    pdf.code_block(
        'function ProgressBar({ currentStep, totalSteps }: Props) {\n'
        '  return (\n'
        '    <div className="flex items-center justify-center gap-2">\n'
        '      {Array.from({ length: totalSteps }, (_, i) => (\n'
        '        <>\n'
        '          <div className={cn(\n'
        '            "w-8 h-8 rounded-full flex items-center justify-center",\n'
        '            i < currentStep ? "bg-green-500 text-white" :\n'
        '            i === currentStep ? "bg-primary text-white" :\n'
        '            "bg-gray-200 text-gray-500"\n'
        '          )}>\n'
        '            {i < currentStep ? <Check /> : i + 1}\n'
        '          </div>\n'
        '          {i < totalSteps - 1 && <div className="w-12 h-0.5 bg-gray-200" />}\n'
        '        </>\n'
        '      ))}\n'
        '    </div>\n'
        '  );\n'
        '}'
    )

    pdf.tip_box(
        "Copy-to-Clipboard Best Practice",
        "The navigator.clipboard API requires a secure context (HTTPS).\n"
        "In development (localhost), it works by default. In production, ensure\n"
        "the site is served over HTTPS for clipboard access to function."
    )


# -------------------------------------------------------------------
#  Chapter 6 - Protected Dashboard Routes
# -------------------------------------------------------------------

def _ch6(pdf: CoursePDF) -> None:
    pdf.chapter_title("6", "Protected Dashboard Routes")

    pdf.section_title("6.1", "Auth Guard Pattern")
    pdf.body(
        "All dashboard routes are wrapped in an auth guard that checks for a valid "
        "authentication token before rendering the page content. The guard is implemented "
        "in the dashboard layout component (src/app/dashboard/layout.tsx), which serves "
        "as the parent layout for all /dashboard/* routes."
    )

    pdf.section_title("6.2", "Implementation")
    pdf.body(
        "The dashboard layout uses the useAuth() hook to access the current user and "
        "loading state. On mount, if loading is true, a full-page loading spinner is "
        "displayed. Once loading completes, if there is no authenticated user, the layout "
        "redirects to /login using Next.js router.push(). Only when a valid user exists "
        "does the layout render the sidebar and page content."
    )
    pdf.code_block(
        'export default function DashboardLayout({ children }: Props) {\n'
        '  const { user, loading } = useAuth();\n'
        '  const router = useRouter();\n'
        '\n'
        '  useEffect(() => {\n'
        '    if (!loading && !user) {\n'
        '      router.push("/login");\n'
        '    }\n'
        '  }, [loading, user, router]);\n'
        '\n'
        '  if (loading) {\n'
        '    return (\n'
        '      <div className="flex h-screen items-center justify-center">\n'
        '        <Spinner size="lg" />\n'
        '      </div>\n'
        '    );\n'
        '  }\n'
        '\n'
        '  if (!user) return null;\n'
        '\n'
        '  return (\n'
        '    <div className="flex h-screen">\n'
        '      <Sidebar />\n'
        '      <main className="flex-1 overflow-y-auto p-6">{children}</main>\n'
        '    </div>\n'
        '  );\n'
        '}'
    )

    pdf.section_title("6.3", "Protected Routes List")
    pdf.body("The following routes are protected by the dashboard auth guard:")
    pdf.bullet("/dashboard - Overview page with key metrics and recent sessions")
    pdf.bullet("/dashboard/sessions - Session list with filtering and pagination")
    pdf.bullet("/dashboard/sessions/[id] - Individual session detail view")
    pdf.bullet("/dashboard/analytics - Analytics charts and conversion funnels")
    pdf.bullet("/dashboard/experiments - A/B test experiment management")
    pdf.bullet("/dashboard/interventions - Intervention rules and triggers")
    pdf.bullet("/dashboard/settings - Account settings and SDK key management")

    pdf.section_title("6.4", "Loading Spinner")
    pdf.body(
        "The loading spinner is a centered, animated SVG component that displays while "
        "the AuthProvider is checking the stored token against the /api/auth/me endpoint. "
        "This prevents a flash of the login page for already-authenticated users. The "
        "spinner typically displays for 100-300ms on fast connections."
    )

    pdf.warn_box(
        "Race Condition Prevention",
        "The auth guard returns null (renders nothing) between the loading=false\n"
        "and redirect execution. This prevents a brief flash of dashboard content\n"
        "for unauthenticated users while router.push() is processing."
    )


# -------------------------------------------------------------------
#  Chapter 7 - Sidebar User Info & Logout
# -------------------------------------------------------------------

def _ch7(pdf: CoursePDF) -> None:
    pdf.chapter_title("7", "Sidebar User Info & Logout")

    pdf.section_title("7.1", "User Info Display")
    pdf.body(
        "The dashboard sidebar displays the authenticated merchant's information at the "
        "bottom of the navigation panel. This section shows the user's email address "
        "(truncated with ellipsis if too long) and their current plan badge (e.g., 'Free', "
        "'Pro', 'Enterprise'). The plan badge is color-coded: green for active plans, "
        "gray for the free tier."
    )
    pdf.code_block(
        '<div className="border-t px-4 py-3">\n'
        '  <p className="text-sm font-medium text-gray-900 truncate">\n'
        '    {user.email}\n'
        '  </p>\n'
        '  <p className="text-xs text-gray-500 mt-0.5">\n'
        '    <span className={cn(\n'
        '      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",\n'
        '      user.plan === "free" ? "bg-gray-100 text-gray-600" :\n'
        '      "bg-green-100 text-green-700"\n'
        '    )}>\n'
        '      {user.plan}\n'
        '    </span>\n'
        '  </p>\n'
        '</div>'
    )

    pdf.section_title("7.2", "Logout Button")
    pdf.body(
        "Below the user info, a logout button is displayed. Clicking it calls the "
        "logout() function from the useAuth() hook, which clears the JWT token from "
        "localStorage, resets the user state to null, and redirects to /login via "
        "router.push('/login')."
    )
    pdf.code_block(
        'const handleLogout = () => {\n'
        '  logout();\n'
        '};\n'
        '\n'
        '// In AuthProvider:\n'
        'const logout = () => {\n'
        '  localStorage.removeItem("token");\n'
        '  localStorage.removeItem("sdk_key");\n'
        '  setUser(null);\n'
        '  router.push("/login");\n'
        '};'
    )

    pdf.section_title("7.3", "Sidebar Navigation Links")
    pdf.body(
        "The sidebar provides navigation links to all dashboard sections. The active "
        "link is highlighted with a blue background and white text. Each link includes "
        "an icon (from lucide-react) and a text label. The sidebar is responsive: on "
        "mobile viewports, it collapses into a hamburger menu."
    )
    pdf.bullet("Overview (LayoutDashboard icon) - /dashboard")
    pdf.bullet("Sessions (Users icon) - /dashboard/sessions")
    pdf.bullet("Analytics (BarChart3 icon) - /dashboard/analytics")
    pdf.bullet("Experiments (FlaskConical icon) - /dashboard/experiments")
    pdf.bullet("Interventions (Zap icon) - /dashboard/interventions")
    pdf.bullet("Settings (Settings icon) - /dashboard/settings")


# -------------------------------------------------------------------
#  Chapter 8 - API Client Updates
# -------------------------------------------------------------------

def _ch8(pdf: CoursePDF) -> None:
    pdf.chapter_title("8", "API Client Updates")

    pdf.section_title("8.1", "Bearer Token Injection")
    pdf.body(
        "The API client (src/lib/api.ts) uses Axios with a request interceptor that "
        "automatically attaches the JWT token to every outgoing request. The interceptor "
        "reads the token from localStorage and adds it as a Bearer token in the "
        "Authorization header. This ensures that all API calls from the dashboard are "
        "authenticated without requiring each component to manually pass credentials."
    )
    pdf.code_block(
        'import axios from "axios";\n'
        '\n'
        'const api = axios.create({\n'
        '  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",\n'
        '});\n'
        '\n'
        'api.interceptors.request.use((config) => {\n'
        '  const token = localStorage.getItem("token");\n'
        '  if (token) {\n'
        '    config.headers.Authorization = `Bearer ${token}`;\n'
        '  }\n'
        '  return config;\n'
        '});'
    )

    pdf.section_title("8.2", "Auth API Functions")
    pdf.body(
        "The API client exports dedicated functions for each auth-related endpoint. "
        "These functions encapsulate the HTTP method, URL, and request body, providing "
        "a clean interface for the AuthProvider and page components."
    )
    pdf.code_block(
        '// Auth API functions\n'
        'export const authRegister = (data: RegisterPayload) =>\n'
        '  api.post("/api/auth/register", data);\n'
        '\n'
        'export const authLogin = (email: string, password: string) =>\n'
        '  api.post("/api/auth/login", { email, password });\n'
        '\n'
        'export const authMe = () =>\n'
        '  api.get("/api/auth/me");\n'
        '\n'
        'export const authLogout = () =>\n'
        '  api.post("/api/auth/logout");\n'
        '\n'
        'export const authRefreshToken = () =>\n'
        '  api.post("/api/auth/refresh");'
    )

    pdf.section_title("8.3", "Response Interceptor")
    pdf.body(
        "A response interceptor handles 401 Unauthorized responses globally. When any "
        "API call returns a 401 status, the interceptor automatically removes the stored "
        "token and redirects to /login. This handles token expiration gracefully without "
        "requiring each component to implement its own error handling for expired tokens."
    )
    pdf.code_block(
        'api.interceptors.response.use(\n'
        '  (response) => response,\n'
        '  (error) => {\n'
        '    if (error.response?.status === 401) {\n'
        '      localStorage.removeItem("token");\n'
        '      if (typeof window !== "undefined") {\n'
        '        window.location.href = "/login";\n'
        '      }\n'
        '    }\n'
        '    return Promise.reject(error);\n'
        '  }\n'
        ');'
    )

    pdf.section_title("8.4", "API Endpoint Summary")
    pdf.body("The following auth-related endpoints are used by the frontend:")

    cols = [("Method", 25), ("Endpoint", 65), ("Description", 55), ("Auth", 25)]
    pdf.table_header(cols)
    widths = [25, 65, 55, 25]
    rows = [
        ["POST", "/api/auth/register", "Create new merchant", "No"],
        ["POST", "/api/auth/login", "Authenticate merchant", "No"],
        ["GET", "/api/auth/me", "Get current user profile", "Yes"],
        ["POST", "/api/auth/logout", "Invalidate session", "Yes"],
        ["POST", "/api/auth/refresh", "Refresh JWT token", "Yes"],
    ]
    for row in rows:
        pdf.table_row(row, widths)


# -------------------------------------------------------------------
#  Chapter 9 - User Flow
# -------------------------------------------------------------------

def _ch9(pdf: CoursePDF) -> None:
    pdf.chapter_title("9", "User Flow")

    pdf.section_title("9.1", "Complete Merchant Journey")
    pdf.body(
        "This chapter documents the complete end-to-end flow a merchant experiences "
        "from first visiting the platform to actively using the dashboard. Understanding "
        "this flow is critical for testing, debugging, and future feature development."
    )

    pdf.section_title("9.2", "New Merchant: Registration Flow")
    pdf.numbered(1, "Merchant visits /register page")
    pdf.numbered(2, "Fills in email, password, shop domain, and accepts GDPR consent")
    pdf.numbered(3, "Clicks 'Create Account' button")
    pdf.numbered(4, "Frontend calls POST /api/auth/register with form data")
    pdf.numbered(5, "Backend creates merchant account, generates SDK key, returns JWT token")
    pdf.numbered(6, "Frontend stores token and SDK key in localStorage")
    pdf.numbered(7, "Frontend redirects to /onboarding (Step 1: Welcome)")
    pdf.numbered(8, "Merchant clicks 'Get Started', advances to Step 2: SDK Key")
    pdf.numbered(9, "Merchant copies SDK key using the copy button")
    pdf.numbered(10, "Merchant advances to Step 3: Install SDK, sees the HTML snippet")
    pdf.numbered(11, "Merchant advances to Step 4: Done, sees success confirmation")
    pdf.numbered(12, "Merchant clicks 'Go to Dashboard', enters the protected dashboard")

    pdf.section_title("9.3", "Returning Merchant: Login Flow")
    pdf.numbered(1, "Merchant visits /login page")
    pdf.numbered(2, "Enters email and password")
    pdf.numbered(3, "Clicks 'Sign In' button")
    pdf.numbered(4, "Frontend calls POST /api/auth/login with credentials")
    pdf.numbered(5, "Backend validates credentials, returns JWT token")
    pdf.numbered(6, "Frontend stores token in localStorage, fetches user profile")
    pdf.numbered(7, "Frontend redirects to /dashboard")

    pdf.section_title("9.4", "Auto-Login: Page Refresh Flow")
    pdf.numbered(1, "Merchant refreshes the browser or returns to the app")
    pdf.numbered(2, "AuthProvider mounts, finds token in localStorage")
    pdf.numbered(3, "AuthProvider calls GET /api/auth/me with Bearer token")
    pdf.numbered(4, "If valid: user state is set, dashboard renders normally")
    pdf.numbered(5, "If expired/invalid: token is removed, merchant is redirected to /login")

    pdf.section_title("9.5", "Logout Flow")
    pdf.numbered(1, "Merchant clicks 'Logout' button in sidebar")
    pdf.numbered(2, "logout() function clears token and sdk_key from localStorage")
    pdf.numbered(3, "User state is set to null")
    pdf.numbered(4, "router.push('/login') redirects to login page")
    pdf.numbered(5, "Dashboard auth guard prevents re-entry without valid token")

    pdf.section_title("9.6", "Flow Diagram")
    pdf.code_block(
        "+----------+     +-----------+     +------------+     +-----------+\n"
        "| Register | --> | Onboarding| --> |  Dashboard | --> |  Logout   |\n"
        "+----------+     +-----------+     +------------+     +-----------+\n"
        "     |                                    ^                  |\n"
        "     |                                    |                  v\n"
        "     |            +----------+            |           +-----------+\n"
        "     +----------> |  Login   | ---------->+           |  /login   |\n"
        "                  +----------+                        +-----------+"
    )

    pdf.tip_box(
        "Testing Tip",
        "Use browser DevTools > Application > Local Storage to inspect\n"
        "the 'token' and 'sdk_key' values at each step of the flow.\n"
        "This is invaluable for debugging auth issues during development."
    )


# -------------------------------------------------------------------
#  Chapter 10 - Frontend Build & Deployment
# -------------------------------------------------------------------

def _ch10(pdf: CoursePDF) -> None:
    pdf.chapter_title("10", "Frontend Build & Deployment")

    pdf.section_title("10.1", "Next.js Build Verification")
    pdf.body(
        "Before deployment, the frontend must pass a full Next.js production build. "
        "The build process compiles TypeScript, tree-shakes unused code, generates "
        "optimized bundles, and pre-renders static pages. Any type errors or import "
        "issues will cause the build to fail."
    )
    pdf.code_block(
        '# Run production build\n'
        'npm run build\n'
        '\n'
        '# Expected output:\n'
        '#   - Compiled successfully\n'
        '#   - Generating static pages\n'
        '#   - Collecting page data\n'
        '#   - Finalizing page optimization\n'
        '#\n'
        '# Key pages generated:\n'
        '#   /login            (client-side)\n'
        '#   /register         (client-side)\n'
        '#   /onboarding       (client-side)\n'
        '#   /dashboard        (client-side)\n'
        '#   /dashboard/[...]  (client-side)'
    )

    pdf.section_title("10.2", "Docker Setup")
    pdf.body(
        "The frontend is containerized using a multi-stage Dockerfile. The first stage "
        "installs dependencies and builds the Next.js application. The second stage "
        "copies only the production artifacts into a minimal Node.js image, reducing "
        "the final image size."
    )
    pdf.code_block(
        '# Stage 1: Build\n'
        'FROM node:20-alpine AS builder\n'
        'WORKDIR /app\n'
        'COPY package*.json ./\n'
        'RUN npm ci\n'
        'COPY . .\n'
        'RUN npm run build\n'
        '\n'
        '# Stage 2: Production\n'
        'FROM node:20-alpine AS runner\n'
        'WORKDIR /app\n'
        'COPY --from=builder /app/.next/standalone ./\n'
        'COPY --from=builder /app/.next/static ./.next/static\n'
        'COPY --from=builder /app/public ./public\n'
        'EXPOSE 3000\n'
        'CMD ["node", "server.js"]'
    )

    pdf.section_title("10.3", "Environment Configuration")
    pdf.body(
        "The frontend requires the following environment variables to be configured. "
        "These can be set in a .env.local file for local development or injected via "
        "Docker environment variables / Kubernetes ConfigMaps for production."
    )
    pdf.code_block(
        '# .env.local\n'
        'NEXT_PUBLIC_API_URL=http://localhost:8000\n'
        'NEXT_PUBLIC_APP_NAME=EmoraTest\n'
        'NEXT_PUBLIC_SDK_CDN_URL=https://cdn.emoratest.ai/sdk/v1\n'
        'NEXT_PUBLIC_ENABLE_ANALYTICS=true'
    )

    pdf.section_title("10.4", "Deployment Checklist")
    pdf.body("Before deploying to production, verify the following:")
    pdf.numbered(1, "npm run build completes without errors")
    pdf.numbered(2, "npm run lint passes with zero warnings")
    pdf.numbered(3, "All environment variables are configured in the target environment")
    pdf.numbered(4, "The API backend is reachable from the frontend container")
    pdf.numbered(5, "CORS is configured on the backend to allow the frontend origin")
    pdf.numbered(6, "HTTPS is enabled for production (required for clipboard API, secure cookies)")
    pdf.numbered(7, "Docker image builds successfully and starts without errors")
    pdf.numbered(8, "Health check endpoint /api/health returns 200 OK")

    pdf.section_title("10.5", "CI/CD Integration")
    pdf.body(
        "The frontend build is integrated into the CI/CD pipeline. On every push to "
        "the main branch, GitHub Actions runs the lint, type-check, and build steps. "
        "If all checks pass, the Docker image is built and pushed to the container "
        "registry, ready for deployment to staging or production environments."
    )
    pdf.code_block(
        '# .github/workflows/frontend.yml (excerpt)\n'
        'jobs:\n'
        '  build:\n'
        '    runs-on: ubuntu-latest\n'
        '    steps:\n'
        '      - uses: actions/checkout@v4\n'
        '      - uses: actions/setup-node@v4\n'
        '        with:\n'
        '          node-version: 20\n'
        '      - run: npm ci\n'
        '      - run: npm run lint\n'
        '      - run: npm run build\n'
        '      - name: Build Docker image\n'
        '        run: docker build -t emoratest-frontend .'
    )

    pdf.warn_box(
        "Production Reminder",
        "Never commit .env files to the repository. Use environment variables\n"
        "injected at runtime. The .gitignore already excludes .env* files.\n"
        "Rotate the JWT secret key before going live."
    )


# -------------------------------------------------------------------
#  Main
# -------------------------------------------------------------------

def main() -> None:
    pdf = CoursePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    _cover(pdf)
    _toc(pdf)
    _ch1(pdf)
    _ch2(pdf)
    _ch3(pdf)
    _ch4(pdf)
    _ch5(pdf)
    _ch6(pdf)
    _ch7(pdf)
    _ch8(pdf)
    _ch9(pdf)
    _ch10(pdf)

    import pathlib
    out = pathlib.Path(__file__).resolve().parent / "Epic7_Merchant_Onboarding.pdf"
    pdf.output(str(out))
    print(f"PDF generated: {out}")


if __name__ == "__main__":
    main()
