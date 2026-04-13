"""Generate Epic 3 Course-Style Documentation PDF — JavaScript SDK.

Run:  python docs/generate_epic3_report.py

Produces: docs/Epic3_JavaScript_SDK.pdf
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
        self.cell(0, 8, "EmoraTest - Epic 3: JavaScript SDK", align="L")
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
        lines = text.split("\n")
        h = 10 + len(lines) * 5.5 + 4
        if self.get_y() + h > self.h - 25:
            self.add_page()
        y0 = self.get_y()
        self.set_fill_color(*bg)
        self.rect(x, y0, w, h, style="F")
        self.set_draw_color(*border_color)
        self.set_line_width(0.8)
        self.line(x, y0, x, y0 + h)
        self.set_xy(x + 6, y0 + 3)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*border_color)
        self.cell(0, 5.5, title, new_x="LMARGIN", new_y="NEXT")
        self.set_x(x + 6)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*self.DARK)
        for line in lines:
            self.cell(0, 5.5, line[:90], new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 6)
        self.set_y(y0 + h + 3)


def build_pdf():
    pdf = CoursePDF("P", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Cover Page ──────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*CoursePDF.PRIMARY)
    pdf.cell(0, 14, "EmoraTest", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(*CoursePDF.DARK)
    pdf.cell(0, 10, "Epic 3: JavaScript SDK", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*CoursePDF.GRAY)
    pdf.cell(0, 7, "Browser-Side Behavioral Event Capture", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "CONV-28 through CONV-35", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_draw_color(*CoursePDF.PRIMARY)
    pdf.set_line_width(0.5)
    mid = pdf.w / 2
    pdf.line(mid - 40, pdf.get_y(), mid + 40, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*CoursePDF.GRAY)
    topics = [
        "Ch 1: SDK Architecture & Build Pipeline",
        "Ch 2: TypeScript Types & Configuration",
        "Ch 3: Cryptographic Hashing & Utilities",
        "Ch 4: HTTP Transport & sendBeacon",
        "Ch 5: Event Queue & Batching Strategy",
        "Ch 6: Session Management & Persistence",
        "Ch 7: DOM Event Collectors",
        "Ch 8: Exit Intent & Visibility Detection",
        "Ch 9: Backend API Endpoints (FastAPI)",
        "Ch 10: Testing Strategy (Vitest + Pytest)",
    ]
    for t in topics:
        pdf.cell(0, 6, t, align="C", new_x="LMARGIN", new_y="NEXT")

    # ════════════════════════════════════════════════════════════
    # Chapter 1: SDK Architecture & Build Pipeline
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("1", "SDK Architecture & Build Pipeline")

    pdf.section_title("1.1", "Why a Custom SDK?")
    pdf.body(
        "Third-party analytics tools (Google Analytics, Hotjar) send data to their own servers. "
        "EmoraTest needs raw behavioral events flowing directly into our ML pipeline, with "
        "sub-second granularity on mouse velocity, scroll retreat patterns, and exit intent signals. "
        "A custom SDK gives us full control over what data is captured, how it is batched, and "
        "where it is sent."
    )

    pdf.section_title("1.2", "Project Structure")
    pdf.code_block(
        "sdk/\n"
        "  src/\n"
        "    index.ts       -- Public API: init(), destroy(), reportOutcome()\n"
        "    types.ts       -- TypeScript interfaces (RawEvent, Config, etc.)\n"
        "    utils.ts       -- sha256, uuid4, throttle, getElementId\n"
        "    transport.ts   -- HTTP fetch + sendBeacon for API calls\n"
        "    event-queue.ts -- Buffered event queue with periodic flush\n"
        "    session.ts     -- Session lifecycle + sessionStorage\n"
        "    collectors.ts  -- DOM event listeners (mouse, click, scroll, etc.)\n"
        "  tests/           -- Vitest test suite (74 tests)\n"
        "  dist/            -- Build output (UMD + ESM + .d.ts)\n"
        "  rollup.config.mjs\n"
        "  tsconfig.json\n"
        "  vitest.config.ts"
    )

    pdf.section_title("1.3", "Build Pipeline with Rollup")
    pdf.body(
        "Rollup is a module bundler optimized for libraries (vs Webpack which targets apps). "
        "We produce three outputs from a single entry point:"
    )
    pdf.numbered(1, "UMD (emoratest.umd.js) - works with <script> tags, AMD, and CommonJS")
    pdf.numbered(2, "ESM (emoratest.esm.js) - for modern bundlers (Vite, Webpack 5, esbuild)")
    pdf.numbered(3, "TypeScript declarations (index.d.ts) - enables type-safe integration")

    pdf.body(
        "The UMD build uses Terser for minification and exposes a global 'EmoraTest' object "
        "so merchants can use it with a simple <script> tag without any build tooling."
    )

    pdf.code_block(
        "// rollup.config.mjs (simplified)\n"
        "export default [\n"
        "  {\n"
        '    input: "src/index.ts",\n'
        "    output: {\n"
        '      file: "dist/emoratest.umd.js",\n'
        '      format: "umd",\n'
        '      name: "EmoraTest",  // window.EmoraTest\n'
        "    },\n"
        "    plugins: [typescript(), resolve(), terser()],\n"
        "  },\n"
        "  // ... ESM and DTS outputs\n"
        "];"
    )

    pdf.tip_box(
        "Key Concept: UMD vs ESM",
        "UMD (Universal Module Definition) wraps your code so it works everywhere:\n"
        "browser globals, AMD (RequireJS), and CommonJS (Node). ESM (ES Modules) is\n"
        "the modern standard with static imports/exports that enable tree-shaking."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 2: TypeScript Types & Configuration
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("2", "TypeScript Types & Configuration")

    pdf.section_title("2.1", "The Type System as Documentation")
    pdf.body(
        "TypeScript types serve as living documentation. When a merchant integrates our SDK, "
        "their IDE shows exactly what options are available and what each event looks like. "
        "This is why we define strict interfaces rather than using 'any'."
    )

    pdf.subsection("Event Types (matching database constraints)")
    pdf.code_block(
        "// types.ts\n"
        "export type EventType =\n"
        '  | "mouse_move" | "click" | "scroll"\n'
        '  | "exit_intent" | "visibility";\n'
        "\n"
        "export interface RawEvent {\n"
        "  type: EventType;\n"
        "  ts: string;        // ISO 8601\n"
        "  x?: number | null;\n"
        "  y?: number | null;\n"
        "  velocity?: number | null;\n"
        "  element_id?: string | null;\n"
        "  metadata?: Record<string, unknown> | null;\n"
        "}"
    )

    pdf.section_title("2.2", "Configuration with Sensible Defaults")
    pdf.body(
        "The SDK exposes a EmoraTestConfig interface with only one required field (sdkKey). "
        "Everything else has production-ready defaults. Internally we 'resolve' the config "
        "into a ResolvedConfig where all fields are required."
    )
    pdf.code_block(
        "// User provides (partial):\n"
        "{ sdkKey: 'sk_live_abc123' }\n"
        "\n"
        "// SDK resolves (complete):\n"
        "{\n"
        "  sdkKey: 'sk_live_abc123',\n"
        "  sdkKeyHash: 'a1b2c3...',  // SHA-256\n"
        "  apiUrl: 'https://shop.com',\n"
        "  flushIntervalMs: 2000,\n"
        "  maxBatchSize: 50,\n"
        "  mouseMoveThrottleMs: 100,\n"
        "  debug: false,\n"
        "  disabled: false,\n"
        "}"
    )

    pdf.tip_box(
        "Design Pattern: Partial -> Resolved Config",
        "This pattern (user provides partial, SDK fills defaults) is standard in\n"
        "production SDKs. It keeps the API simple for merchants while giving the\n"
        "internal code guaranteed types. The nullish coalescing (??) operator\n"
        "handles the default assignment cleanly."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 3: Cryptographic Hashing & Utilities
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("3", "Cryptographic Hashing & Utilities")

    pdf.section_title("3.1", "Why Hash the SDK Key?")
    pdf.body(
        "The merchant's SDK key is a secret. Sending it in plaintext over the wire "
        "would expose it to anyone inspecting network traffic. Instead, we SHA-256 hash "
        "it client-side and send only the hash. The backend stores the same hash (computed "
        "at key creation time) and matches them."
    )
    pdf.body(
        "This is the same principle as password hashing: the secret never leaves the "
        "client in its original form. Even if someone intercepts the hash, they cannot "
        "reverse it to get the original key."
    )

    pdf.section_title("3.2", "Web Crypto API")
    pdf.code_block(
        "export async function sha256(message: string): Promise<string> {\n"
        "  // Use Web Crypto API (available in all modern browsers)\n"
        "  const encoder = new TextEncoder();\n"
        "  const data = encoder.encode(message);\n"
        "  const hash = await crypto.subtle.digest('SHA-256', data);\n"
        "  return Array.from(new Uint8Array(hash))\n"
        "    .map(b => b.toString(16).padStart(2, '0'))\n"
        "    .join('');\n"
        "}"
    )
    pdf.body(
        "The Web Crypto API is the browser's built-in cryptographic toolkit. It returns "
        "an ArrayBuffer, which we convert to a hex string. The function is async because "
        "crypto.subtle.digest() returns a Promise (the browser may use hardware acceleration)."
    )

    pdf.section_title("3.3", "The Throttle Function")
    pdf.body(
        "Mouse move events fire 60+ times per second. Sending all of them would flood "
        "the queue and waste bandwidth. Throttling ensures we capture at most one event "
        "per N milliseconds while still capturing the final position."
    )
    pdf.code_block(
        "export function throttle(fn, ms) {\n"
        "  let last = 0;\n"
        "  let timer = null;\n"
        "  return function(...args) {\n"
        "    const now = Date.now();\n"
        "    const remaining = ms - (now - last);\n"
        "    if (remaining <= 0) {\n"
        "      // Enough time passed - fire immediately\n"
        "      clearTimeout(timer); timer = null;\n"
        "      last = now;\n"
        "      fn.apply(this, args);\n"
        "    } else if (!timer) {\n"
        "      // Schedule trailing call\n"
        "      timer = setTimeout(() => { ... }, remaining);\n"
        "    }\n"
        "  };\n"
        "}"
    )

    pdf.warn_box(
        "Throttle vs Debounce",
        "Throttle: fires at regular intervals during activity. Use for continuous\n"
        "  events like mousemove, scroll, resize.\n"
        "Debounce: fires only AFTER activity stops. Use for discrete events\n"
        "  like search input, window resize-end.\n"
        "We use throttle because we need periodic samples DURING mouse movement."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 4: HTTP Transport & sendBeacon
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("4", "HTTP Transport & sendBeacon")

    pdf.section_title("4.1", "The Transport Class")
    pdf.body(
        "The Transport class is the SDK's HTTP client. It wraps fetch() for normal "
        "requests and navigator.sendBeacon() for page unload scenarios. All requests "
        "include the X-SDK-Key header with the hashed key."
    )

    pdf.subsection("API Endpoints")
    pdf.bullet("POST /api/v1/sessions - Create a new tracking session")
    pdf.bullet("PUT /api/v1/sessions/:id/end - End a session")
    pdf.bullet("PUT /api/v1/sessions/:id/outcome - Report purchase/abandon")
    pdf.bullet("POST /api/v1/events/batch - Send a batch of behavioral events")

    pdf.section_title("4.2", "The Page Unload Problem")
    pdf.body(
        "When a user closes a tab or navigates away, the browser cancels all pending "
        "fetch() requests. This means any events still in the queue would be lost. "
        "This is a critical problem for analytics SDKs because the most valuable "
        "events (exit intent, final scroll position) happen right before the user leaves."
    )

    pdf.subsection("Solution: navigator.sendBeacon()")
    pdf.body(
        "sendBeacon() is a browser API specifically designed for this use case. It "
        "guarantees the request will be sent even after the page starts unloading. "
        "The trade-off is that it is fire-and-forget (no response, no error handling). "
        "We use it as a last resort during beforeunload and visibilitychange events."
    )

    pdf.code_block(
        "// Transport.sendBeacon() implementation\n"
        "sendBeacon(payload: BatchPayload): boolean {\n"
        "  const blob = new Blob(\n"
        "    [JSON.stringify(payload)],\n"
        '    { type: "application/json" }\n'
        "  );\n"
        "  // sdk_key as query param (no headers in sendBeacon)\n"
        "  return navigator.sendBeacon(\n"
        "    `${this.baseUrl}/api/v1/events/batch?sdk_key=hash`,\n"
        "    blob\n"
        "  );\n"
        "}"
    )

    pdf.tip_box(
        "Why Query Param for sendBeacon?",
        "sendBeacon() does not support custom headers. So the SDK key hash\n"
        "is sent as a query parameter instead. The backend's get_sdk_key_header()\n"
        "function accepts both X-SDK-Key header and sdk_key query param,\n"
        "specifically to support this sendBeacon fallback."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 5: Event Queue & Batching Strategy
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("5", "Event Queue & Batching Strategy")

    pdf.section_title("5.1", "Why Batch Events?")
    pdf.body(
        "Individual HTTP requests per event would create thousands of requests per "
        "session. Batching reduces network overhead, server load, and battery drain "
        "on mobile devices. The EventQueue buffers events and flushes them periodically."
    )

    pdf.subsection("Queue Configuration")
    pdf.bullet("flushIntervalMs: 2000 (flush every 2 seconds)")
    pdf.bullet("maxBatchSize: 50 (flush when queue reaches 50 events)")
    pdf.bullet("On page unload: flush everything via sendBeacon()")

    pdf.section_title("5.2", "Failure Recovery")
    pdf.body(
        "When a batch fails to send (network error, server down), the events are "
        "re-queued at the front of the queue. This ensures events are sent in order "
        "and nothing is lost during temporary outages."
    )
    pdf.code_block(
        "async flush(): Promise<void> {\n"
        "  const events = this.queue.splice(0, maxBatchSize);\n"
        "  try {\n"
        "    await transport.sendEvents({ session_id, events });\n"
        "  } catch (err) {\n"
        "    // Re-queue at front on failure\n"
        "    this.queue.unshift(...events);\n"
        "  }\n"
        "}"
    )

    pdf.warn_box(
        "Memory Consideration",
        "If the backend is down for an extended period, the queue grows\n"
        "unboundedly. In a production system, you would add a max queue\n"
        "size (e.g., 1000 events) and drop oldest events when exceeded.\n"
        "This prevents memory leaks on long-running single-page apps."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 6: Session Management & Persistence
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("6", "Session Management & Persistence")

    pdf.section_title("6.1", "What is a Session?")
    pdf.body(
        "A session represents a single user visit. It starts when the SDK initializes "
        "and ends when the user navigates away. Sessions are identified by UUID v4 and "
        "stored on the backend with a 90-day expiration for GDPR compliance."
    )

    pdf.section_title("6.2", "sessionStorage Persistence")
    pdf.body(
        "When a user navigates between pages on the same site (SPA or not), we want "
        "to maintain the same session. sessionStorage persists across same-tab navigations "
        "but clears when the tab is closed. This is perfect for our use case."
    )
    pdf.code_block(
        "// On init: check for existing session\n"
        "const stored = sessionStorage.getItem('__emoratest_session');\n"
        "if (stored && stored.merchantId === merchantId) {\n"
        "  // Resume existing session (no API call needed)\n"
        "  return JSON.parse(stored);\n"
        "}\n"
        "// Otherwise: create new session via API\n"
        "const session = await transport.createSession({...});\n"
        "sessionStorage.setItem('__emoratest_session', JSON.stringify(session));"
    )

    pdf.tip_box(
        "sessionStorage vs localStorage",
        "sessionStorage: scoped to the tab, cleared on close. Perfect for sessions.\n"
        "localStorage: persists forever, shared across tabs. Would create problems\n"
        "  with multiple tabs having the same session ID, and stale sessions\n"
        "  persisting after the user intended to leave."
    )

    pdf.section_title("6.3", "Graceful Degradation")
    pdf.body(
        "If the backend is unreachable during session creation, the SDK still creates "
        "a local session and captures events. This means data collection continues even "
        "if the first API call fails -- events will be sent when connectivity returns."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 7: DOM Event Collectors
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("7", "DOM Event Collectors")

    pdf.section_title("7.1", "Architecture: Collectors as Plugins")
    pdf.body(
        "Each collector is a standalone function that attaches DOM listeners and returns "
        "a cleanup function. This pattern makes collectors composable and easy to test "
        "independently. The SDK activates all collectors on init() and calls their "
        "cleanup functions on destroy()."
    )
    pdf.code_block(
        "type Cleanup = () => void;\n"
        "\n"
        "function collectClicks(queue: EventQueue): Cleanup {\n"
        '  const handler = (e) => queue.push({ type: "click", ... });\n'
        '  document.addEventListener("click", handler, { passive: true });\n'
        '  return () => document.removeEventListener("click", handler);\n'
        "}"
    )

    pdf.section_title("7.2", "Mouse Move Collector")
    pdf.body(
        "Captures cursor position and calculates velocity (pixels/second). Velocity is "
        "a key ML feature: high velocity suggests scanning/uncertainty, while low velocity "
        "suggests focused reading/intent."
    )
    pdf.code_block(
        "// Velocity calculation\n"
        "const dt = (now - lastTime) / 1000;  // seconds\n"
        "const dx = ev.clientX - lastX;\n"
        "const dy = ev.clientY - lastY;\n"
        "const dist = Math.sqrt(dx*dx + dy*dy);\n"
        "const velocity = dt > 0 ? dist / dt : 0;"
    )

    pdf.section_title("7.3", "Click Collector with Rage Click Detection")
    pdf.body(
        "A 'rage click' is when a user clicks the same area 3+ times within 2 seconds. "
        "This is a strong signal of frustration (the button is not responding, or the "
        "user is confused about what is clickable)."
    )
    pdf.code_block(
        "// Rage click detection algorithm\n"
        "recentClicks.push({ x, y, time: now });\n"
        "// Remove clicks older than 2 seconds\n"
        "while (recentClicks[0]?.time < now - 2000) recentClicks.shift();\n"
        "// Count clicks within 50px radius\n"
        "const nearby = recentClicks.filter(c =>\n"
        "  Math.sqrt((c.x-x)**2 + (c.y-y)**2) <= 50\n"
        ");\n"
        "const isRageClick = nearby.length >= 3;"
    )

    pdf.section_title("7.4", "Scroll Collector")
    pdf.body(
        "Tracks scroll direction, delta (pixels), viewport percentage, and 'scroll retreat' "
        "(user scrolled down then back up). Scroll retreat is a key behavioral signal: "
        "it indicates the user is reconsidering or re-reading content they already passed."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 8: Exit Intent & Visibility Detection
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("8", "Exit Intent & Visibility Detection")

    pdf.section_title("8.1", "What is Exit Intent?")
    pdf.body(
        "Exit intent is the behavioral pattern that predicts a user is about to leave. "
        "E-commerce sites use this to trigger last-chance offers (discount popups, "
        "free shipping reminders). Our SDK detects three types of exit intent:"
    )
    pdf.numbered(1, "Mouse leaving viewport top (desktop) - cursor moves toward browser "
                    "chrome/address bar")
    pdf.numbered(2, "Back button / history navigation - user pressed the back button")
    pdf.numbered(3, "Tab switch (visibility hidden) - user switched to another tab")

    pdf.section_title("8.2", "Desktop vs Mobile")
    pdf.body(
        "On desktop, mouse position is the primary signal (mouseout event with clientY <= 0). "
        "On mobile, there is no cursor. Instead, we rely on the Page Visibility API "
        "(document.visibilityState changes to 'hidden') which fires when the user "
        "switches apps, tabs, or the browser goes to background."
    )

    pdf.code_block(
        "// Exit intent: mouse leaves viewport top\n"
        "document.addEventListener('mouseout', (e) => {\n"
        "  if (e.clientY <= 0) {\n"
        "    queue.push({\n"
        "      type: 'exit_intent',\n"
        "      metadata: { trigger: 'mouse_leave' }\n"
        "    });\n"
        "  }\n"
        "});\n"
        "\n"
        "// Visibility change (mobile + desktop)\n"
        "document.addEventListener('visibilitychange', () => {\n"
        "  if (document.visibilityState === 'hidden') {\n"
        "    queue.push({ type: 'exit_intent',\n"
        "      metadata: { trigger: 'tab_switch' } });\n"
        "  }\n"
        "});"
    )

    pdf.warn_box(
        "iOS Safari: No beforeunload",
        "iOS Safari does not reliably fire the 'beforeunload' event. This is why\n"
        "we also listen to 'visibilitychange' for flushing events. The SDK uses\n"
        "both listeners to maximize data capture reliability across all platforms."
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 9: Backend API Endpoints
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("9", "Backend API Endpoints (FastAPI)")

    pdf.section_title("9.1", "Endpoint Architecture")
    pdf.body(
        "The backend provides 4 REST endpoints for the SDK, all protected by "
        "SDK key authentication. The endpoints use async SQLAlchemy for non-blocking "
        "database operations."
    )

    pdf.subsection("POST /api/v1/sessions")
    pdf.body(
        "Creates a new session. Generates a UUID v4 server-side, sets a 90-day "
        "expiration, and returns the session_id to the SDK."
    )

    pdf.subsection("PUT /api/v1/sessions/{id}/end")
    pdf.body(
        "Sets ended_at timestamp. Uses UPDATE...RETURNING to atomically check "
        "ownership and update in a single query."
    )

    pdf.subsection("PUT /api/v1/sessions/{id}/outcome")
    pdf.body(
        "Reports whether the session ended in 'purchase' or 'abandon'. This is the "
        "ground truth label for ML training."
    )

    pdf.subsection("POST /api/v1/events/batch")
    pdf.body(
        "Bulk inserts up to 200 events. Verifies session ownership first, then uses "
        "db.add_all() for efficient batch insertion."
    )

    pdf.section_title("9.2", "SDK Key Authentication")
    pdf.code_block(
        "async def authenticate_sdk_key(db, sdk_key_hash):\n"
        '    """Look up merchant by SDK key hash."""\n'
        "    result = await db.execute(\n"
        "        select(Merchant).where(\n"
        "            Merchant.sdk_key_hash == sdk_key_hash,\n"
        "            Merchant.is_active.is_(True),\n"
        "        )\n"
        "    )\n"
        "    merchant = result.scalar_one_or_none()\n"
        "    if merchant is None:\n"
        '        raise HTTPException(401, "Invalid or inactive SDK key")\n'
        "    return merchant"
    )

    pdf.section_title("9.3", "Pydantic Validation")
    pdf.body(
        "Request schemas use Pydantic v2 with regex patterns and constraints. "
        "This ensures invalid data is rejected at the API boundary before touching "
        "the database."
    )
    pdf.code_block(
        "class EventItem(BaseModel):\n"
        "    type: str = Field(\n"
        "        ...,\n"
        "        pattern=r'^(mouse_move|click|scroll|exit_intent|visibility)$'\n"
        "    )\n"
        "    ts: datetime\n"
        "    x: float | None = None\n"
        "    element_id: str | None = Field(None, max_length=128)\n"
        "    metadata: dict | None = None\n"
        "\n"
        "class EventBatchRequest(BaseModel):\n"
        "    session_id: str\n"
        "    events: list[EventItem] = Field(\n"
        "        ..., min_length=1, max_length=200\n"
        "    )"
    )

    # ════════════════════════════════════════════════════════════
    # Chapter 10: Testing Strategy
    # ════════════════════════════════════════════════════════════
    pdf.chapter_title("10", "Testing Strategy")

    pdf.section_title("10.1", "SDK Tests (Vitest + happy-dom)")
    pdf.body(
        "The SDK runs in a browser environment, but tests run in Node.js. "
        "happy-dom provides a lightweight DOM implementation (document, window, "
        "sessionStorage, events) so we can test collectors and session management "
        "without a real browser."
    )

    pdf.subsection("Test Coverage (74 tests)")
    pdf.bullet("utils.test.ts (18 tests) - sha256, uuid4, throttle, getElementId")
    pdf.bullet("transport.test.ts (10 tests) - fetch mocking, sendBeacon, error handling")
    pdf.bullet("event-queue.test.ts (11 tests) - batching, periodic flush, failure recovery")
    pdf.bullet("session.test.ts (13 tests) - create, resume, end, storage persistence")
    pdf.bullet("collectors.test.ts (15 tests) - mouse, click, scroll, exit intent, visibility")
    pdf.bullet("index.test.ts (7 tests) - init/destroy lifecycle, disabled mode")

    pdf.section_title("10.2", "Backend Tests (Pytest + Mocks)")
    pdf.body(
        "Backend tests use FastAPI's TestClient with dependency overrides. The database "
        "is replaced with AsyncMock, and authenticate_sdk_key is patched with "
        "unittest.mock.patch. This tests endpoint logic (routing, validation, status codes) "
        "without needing a PostgreSQL connection."
    )

    pdf.subsection("Test Coverage (24 tests)")
    pdf.bullet("Session create - success, missing key, invalid body, invalid device type")
    pdf.bullet("Session end - success, not found, invalid UUID, missing key")
    pdf.bullet("Session outcome - purchase, abandon, invalid value, missing key")
    pdf.bullet("Event batch - success, all event types, invalid type, empty, too many, "
               "session not found")
    pdf.bullet("Auth - missing SDK key, header extraction")
    pdf.bullet("Schema validation - element_id max length, outcome pattern, metadata dict")

    pdf.section_title("10.3", "Key Testing Pattern: Dependency Override")
    pdf.code_block(
        "# Override database dependency\n"
        "mock_db = AsyncMock()\n"
        "async def override_get_db():\n"
        "    yield mock_db\n"
        "app.dependency_overrides[get_db] = override_get_db\n"
        "\n"
        "# Patch auth function (called directly, not via Depends)\n"
        '@patch("app.api.sdk.authenticate_sdk_key",\n'
        "       new_callable=AsyncMock,\n"
        "       return_value=make_merchant())\n"
        "def test_endpoint(self, mock_auth):\n"
        "    response = client.post('/api/v1/sessions', ...)\n"
        "    assert response.status_code == 200"
    )

    pdf.tip_box(
        "Depends() vs Direct Calls",
        "FastAPI's app.dependency_overrides only works for Depends() parameters.\n"
        "authenticate_sdk_key() is called directly inside endpoint functions, so\n"
        "we use unittest.mock.patch() to mock it. This is a common gotcha when\n"
        "testing FastAPI apps with mixed dependency injection patterns."
    )

    # ── Save ────────────────────────────────────────────────
    output_path = "docs/Epic3_JavaScript_SDK.pdf"
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    build_pdf()
