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

    // Create new session
    const sessionId = uuid4();
    const startedAt = isoNow();

    try {
      await this.transport.createSession({
        page_url: window.location.href,
        started_at: startedAt,
        country_code: detectCountryCode(),
        device_type: detectDeviceType(),
      });
    } catch (err) {
      if (this.debug) {
        console.error("[EmoraTest] Session creation failed:", err);
      }
      // Still track locally even if backend is down
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
