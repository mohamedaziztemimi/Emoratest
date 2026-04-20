/**
 * Session manager — creates and tracks session lifecycle (CONV-30).
 *
 * A session starts when the SDK initializes and ends when the user
 * navigates away or the page is closed. The session ID is stored in
 * sessionStorage so it persists across same-tab navigations.
 */

import type { Transport } from "./transport";
import { detectCountryCode, detectDeviceType, isoNow, uuid4 } from "./utils";

const SESSION_KEY = "__emoratest_session";

export interface SessionInfo {
  sessionId: string;
  startedAt: string;
}

export class SessionManager {
  private session: SessionInfo | null = null;
  private readonly transport: Transport;
  private readonly debug: boolean;
  private outcomeReported = false;

  constructor(transport: Transport, debug: boolean) {
    this.transport = transport;
    this.debug = debug;
  }

  /** Get or create a session. */
  async start(): Promise<SessionInfo> {
    // Check sessionStorage for existing session
    const stored = this.loadFromStorage();
    if (stored) {
      this.session = stored;
      if (this.debug) {
        console.debug("[EmoraTest] Resumed session:", stored.sessionId);
      }
      return stored;
    }

    // Create new session via backend — backend generates the session_id
    const startedAt = isoNow();
    let sessionId: string;

    try {
      const response = await this.transport.createSession({
        page_url: window.location.href,
        started_at: startedAt,
        country_code: detectCountryCode(),
        device_type: detectDeviceType(),
      });
      // Use the session_id returned from backend
      sessionId = response.session_id;
    } catch (err) {
      if (this.debug) {
        console.error("[EmoraTest] Session creation failed:", err);
      }
      // Clear any stored session data to prevent reuse of broken state
      this.clearStorage();
      // Fallback: generate client-side if backend is down
      sessionId = uuid4();
    }

    this.session = { sessionId, startedAt };
    this.saveToStorage(this.session);

    if (this.debug) {
      console.debug("[EmoraTest] New session:", sessionId);
    }

    return this.session;
  }

  /** End the current session. */
  async end(): Promise<void> {
    if (!this.session) return;

    try {
      await this.transport.endSession(this.session.sessionId);
    } catch {
      // Best effort — also try beacon
      this.transport.sendBeaconEnd(this.session.sessionId);
    }

    this.clearStorage();
    this.session = null;
  }

  /** End session via beacon (for page unload). */
  endBeacon(): void {
    if (!this.session) return;
    this.transport.sendBeaconEnd(this.session.sessionId);
    this.clearStorage();
    this.session = null;
  }

  /** Report outcome via beacon (for page unload - sets outcome to 'abandon'). */
  reportOutcomeBeacon(outcome: "purchase" | "abandon"): void {
    if (!this.session) return;
    this.transport.sendBeaconOutcome(this.session.sessionId, outcome);
    if (outcome === "purchase") {
      this.outcomeReported = true;
    }
  }

  /**
   * Combined close via beacon — ends session AND sets outcome to 'abandon' in one call.
   * More reliable than calling both reportOutcomeBeacon and endBeacon separately.
   */
  closeBeacon(): void {
    if (!this.session) return;
    this.transport.sendBeaconClose(this.session.sessionId);
    this.clearStorage();
    this.session = null;
  }

  /** Mark outcome as reported (prevents double-reporting on page unload). */
  markOutcomeReported(): void {
    this.outcomeReported = true;
  }

  /** Check if outcome was already reported. */
  isOutcomeReported(): boolean {
    return this.outcomeReported;
  }

  /** Get the current session ID. */
  getSessionId(): string | null {
    return this.session?.sessionId ?? null;
  }

  /** Get the current session info. */
  getSession(): SessionInfo | null {
    return this.session;
  }

  // ── Storage helpers ─────────────────────────────────────────

  private loadFromStorage(): SessionInfo | null {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      return JSON.parse(raw) as SessionInfo;
    } catch {
      return null;
    }
  }

  private saveToStorage(session: SessionInfo): void {
    try {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch {
      // sessionStorage unavailable (incognito, etc.)
    }
  }

  private clearStorage(): void {
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch {
      // ignore
    }
  }
}
