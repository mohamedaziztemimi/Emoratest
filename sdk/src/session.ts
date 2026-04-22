/**
 * Session manager — creates and tracks session lifecycle with outcome priority.
 *
 * A session starts when the SDK initializes and ends when the user
 * navigates away or the page is closed. The session ID is stored in
 * sessionStorage so it persists across same-tab navigations.
 *
 * Features:
 * - Outcome priority system (purchase > signup > abandon)
 * - Session sampling (only track N% of sessions)
 * - Event limit tracking
 * - Session duration tracking
 */

import type { Transport } from "./transport";
import type { OutcomeType, OutcomeWithPriority, getOutcomePriority, shouldOverrideOutcome } from "./types";
import { detectCountryCode, detectDeviceType, isoNow, uuid4 } from "./utils";

const SESSION_KEY = "__emoratest_session";
const SAMPLING_DECISION_KEY = "__emoratest_sampled";

export interface SessionInfo {
  sessionId: string;
  startedAt: string;
  sampledIn: boolean; // Whether this session is being tracked (sampling)
}

export interface SessionState {
  currentOutcome: OutcomeType | null;
  outcomeReported: boolean;
  eventCount: number;
  sessionEnded: boolean;
}

export class SessionManager {
  private session: SessionInfo | null = null;
  private state: SessionState = {
    currentOutcome: null,
    outcomeReported: false,
    eventCount: 0,
    sessionEnded: false,
  };
  private readonly transport: Transport;
  private readonly debug: boolean;
  private readonly maxEvents: number;
  private readonly maxDuration: number;

  constructor(
    transport: Transport,
    debug: boolean,
    maxEvents: number = 1000,
    maxDuration: number = 30 * 60 * 1000,
  ) {
    this.transport = transport;
    this.debug = debug;
    this.maxEvents = maxEvents;
    this.maxDuration = maxDuration;
  }

  /** Check if this session is being tracked (sampling). */
  isTracked(): boolean {
    return this.session?.sampledIn ?? false;
  }

  /** Check if session has exceeded max duration. */
  isExpired(): boolean {
    if (!this.session) return true;
    const elapsed = Date.now() - new Date(this.session.startedAt).getTime();
    return elapsed >= this.maxDuration;
  }

  /** Get the elapsed time since session start in ms. */
  getElapsedMs(): number {
    if (!this.session) return 0;
    return Date.now() - new Date(this.session.startedAt).getTime();
  }

  /** Get or create a session with sampling decision. */
  async start(samplingRate: number = 0.2): Promise<SessionInfo> {
    // Check sessionStorage for existing session
    const stored = this.loadFromStorage();
    if (stored) {
      this.session = stored;
      if (this.debug) {
        console.debug("[EmoraTest] Resumed session:", stored.sessionId, "tracked:", stored.sampledIn);
      }
      return stored;
    }

    // Make sampling decision (persisted so same decision across page navs)
    const sampledIn = this.makeSamplingDecision(samplingRate);

    // Only create session on backend if sampled in
    let sessionId: string;
    const startedAt = isoNow();

    if (sampledIn) {
      try {
        const response = await this.transport.createSession({
          page_url: window.location.href,
          started_at: startedAt,
          country_code: detectCountryCode(),
          device_type: detectDeviceType(),
        });
        sessionId = response.session_id;
      } catch (err) {
        if (this.debug) {
          console.error("[EmoraTest] Session creation failed:", err);
        }
        this.clearStorage();
        sessionId = uuid4();
      }
    } else {
      // Not sampled - generate a client ID but don't create backend session
      sessionId = uuid4();
      if (this.debug) {
        console.debug("[EmoraTest] Session NOT sampled (skipping tracking)");
      }
    }

    this.session = { sessionId, startedAt, sampledIn };
    this.saveToStorage(this.session);

    if (this.debug) {
      console.debug("[EmoraTest] New session:", sessionId, "sampled:", sampledIn);
    }

    return this.session;
  }

  /** End the current session. */
  async end(): Promise<void> {
    if (!this.session || this.state.sessionEnded) return;

    this.state.sessionEnded = true;

    // Only send to backend if sampled in
    if (this.session.sampledIn) {
      // Set outcome to "abandon" ONLY if no other outcome was set
      const finalOutcome = this.state.currentOutcome ?? "abandon";

      try {
        // Send outcome and end together if not already reported
        if (!this.state.outcomeReported) {
          await this.transport.endSessionWithOutcome(this.session.sessionId, finalOutcome);
        } else {
          await this.transport.endSession(this.session.sessionId);
        }
      } catch {
        // Best effort — also try beacon
        this.transport.sendBeaconClose(this.session.sessionId);
      }
    }

    this.clearStorage();
    this.session = null;
    this.state = {
      currentOutcome: null,
      outcomeReported: false,
      eventCount: 0,
      sessionEnded: false,
    };
  }

  /** Report an outcome with priority checking. */
  async reportOutcome(outcome: OutcomeType): Promise<boolean> {
    if (!this.session || !this.session.sampledIn) return false;

    // Check if new outcome has higher priority than current
    if (this.state.currentOutcome) {
      // Import priority functions
      const { getOutcomePriority, shouldOverrideOutcome } = await import("./types");
      const currentPriority = getOutcomePriority(this.state.currentOutcome);
      const incomingPriority = getOutcomePriority(outcome);

      if (this.debug) {
        console.debug(`[EmoraTest] Outcome priority check: current="${this.state.currentOutcome}" (${currentPriority}), incoming="${outcome}" (${incomingPriority})`);
      }

      if (incomingPriority <= currentPriority) {
        // Lower or equal priority - don't override
        if (this.debug) {
          console.debug(`[EmoraTest] Outcome "${outcome}" ignored - current "${this.state.currentOutcome}" has higher/equal priority`);
        }
        return false;
      }
    }

    // Higher priority - update outcome
    this.state.currentOutcome = outcome;

    try {
      const response = await fetch(
        `${this.transport.apiUrl}/api/v1/sessions/${this.session.sessionId}/outcome`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "X-SDK-Key": this.transport.sdkKey,
          },
          body: JSON.stringify({ outcome }),
        },
      );

      if (response.ok) {
        this.state.outcomeReported = true;
        if (this.debug) {
          console.debug(`[EmoraTest] Outcome updated: ${outcome}`);
        }
        return true;
      }
    } catch (err) {
      if (this.debug) {
        console.error("[EmoraTest] Failed to report outcome:", err);
      }
    }

    return false;
  }

  /** Get the current outcome. */
  getCurrentOutcome(): OutcomeType | null {
    return this.state.currentOutcome;
  }

  /** Check if outcome was already reported. */
  isOutcomeReported(): boolean {
    return this.state.outcomeReported;
  }

  /** Mark outcome as reported (prevents double-reporting on page unload). */
  markOutcomeReported(): void {
    this.state.outcomeReported = true;
  }

  /** Increment event count. Returns true if under limit. */
  incrementEventCount(): boolean {
    this.state.eventCount++;
    return this.state.eventCount <= this.maxEvents;
  }

  /** Check if should track (sampled in AND under event limit AND not expired). */
  shouldTrack(): boolean {
    if (!this.session) return false;
    if (!this.session.sampledIn) return false;
    if (this.isExpired()) return false;
    if (this.state.eventCount >= this.maxEvents) return false;
    return true;
  }

  /** Check if should track high-priority events (even after limit). */
  shouldTrackHighPriority(): boolean {
    if (!this.session) return false;
    if (!this.session.sampledIn) return false;
    if (this.isExpired()) return false;
    return true;
  }

  /** Get the current session ID. */
  getSessionId(): string | null {
    return this.session?.sessionId ?? null;
  }

  /** Get the current session info. */
  getSession(): SessionInfo | null {
    return this.session;
  }

  /** Get the current event count. */
  getEventCount(): number {
    return this.state.eventCount;
  }

  /** Get sampling decision for this session. */
  isSampledIn(): boolean {
    return this.session?.sampledIn ?? false;
  }

  /** End session via beacon (for page unload). */
  endBeacon(): void {
    if (!this.session || this.state.sessionEnded) return;

    this.state.sessionEnded = true;

    if (this.session.sampledIn) {
      // Set outcome to "abandon" ONLY if no other outcome was set
      const finalOutcome = this.state.currentOutcome ?? "abandon";
      this.transport.sendBeaconClose(this.session.sessionId);
    }

    this.clearStorage();
    this.session = null;
  }

  // ── Storage helpers ─────────────────────────────────────────────

  private loadFromStorage(): SessionInfo | null {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as SessionInfo;
      // Handle legacy sessions without sampledIn field
      if (typeof parsed.sampledIn !== "boolean") {
        parsed.sampledIn = true; // Legacy sessions were always tracked
      }
      return parsed;
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

  /** Make and persist sampling decision. */
  private makeSamplingDecision(rate: number): boolean {
    try {
      // Check if we already decided
      const existing = localStorage.getItem(SAMPLING_DECISION_KEY);
      if (existing !== null) {
        return existing === "true";
      }

      // Make new decision
      const sampledIn = Math.random() < rate;
      localStorage.setItem(SAMPLING_DECISION_KEY, sampledIn ? "true" : "false");

      if (this.debug) {
        console.debug(`[EmoraTest] Sampling decision: ${sampledIn ? "TRACKED" : "SKIPPED"} (rate: ${rate})`);
      }

      return sampledIn;
    } catch {
      // localStorage unavailable - default to tracking
      return true;
    }
  }
}
