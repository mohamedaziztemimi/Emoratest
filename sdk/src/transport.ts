/**
 * Transport layer — handles HTTP communication with the backend API (CONV-33).
 *
 * Uses fetch() for normal requests and navigator.sendBeacon() for page
 * unload scenarios (sendBeacon is fire-and-forget but reliable during unload).
 */

import type { BatchPayload, SessionCreatePayload, SessionCreateResponse, OutcomeType } from "./types";

export class Transport {
  private readonly baseUrl: string;
  private readonly headers: Record<string, string>;
  public disabled = false;
  public limitReached = false;

  constructor(apiUrl: string, sdkKeyHash: string) {
    this.baseUrl = apiUrl.replace(/\/+$/, "");
    this.headers = {
      "Content-Type": "application/json",
      "X-SDK-Key": sdkKeyHash,
    };
  }

  /** Check if response is 401 and disable the SDK if so. */
  private handleAuthError(res: Response): void {
    if (res.status === 401 && !this.disabled) {
      this.disabled = true;
      console.error(
        "[EmoraTest] Invalid SDK key. Check your API key at https://your-dashboard/settings",
      );
    }
  }

  /** Check if response is 429 (session limit reached). */
  private handleLimitReached(res: Response): void {
    if (res.status === 429 && !this.limitReached) {
      this.limitReached = true;
      console.warn("[EmoraTest] Monthly session limit reached. Tracking has been paused.");
    }
  }

  /** POST /api/v1/sessions — create a new session. */
  async createSession(
    payload: SessionCreatePayload,
  ): Promise<SessionCreateResponse> {
    if (this.disabled || this.limitReached) {
      throw new Error("SDK disabled due to invalid API key or session limit reached");
    }

    const res = await fetch(`${this.baseUrl}/api/v1/sessions`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      this.handleAuthError(res);
      this.handleLimitReached(res);
      throw new Error(`Session create failed: ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as SessionCreateResponse;
  }

  /** POST /api/v1/events/batch — send a batch of events. */
  async sendEvents(payload: BatchPayload): Promise<void> {
    if (this.disabled) {
      return; // Silent fail - don't spam logs
    }

    const res = await fetch(`${this.baseUrl}/api/v1/events/batch`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      this.handleAuthError(res);
      throw new Error(`Event batch failed: ${res.status} ${res.statusText}`);
    }
  }

  /** PUT /api/v1/sessions/:id/end — end a session. */
  async endSession(sessionId: string): Promise<void> {
    if (this.disabled) {
      return; // Silent fail
    }

    const res = await fetch(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/end`,
      {
        method: "PUT",
        headers: this.headers,
      },
    );

    if (!res.ok) {
      this.handleAuthError(res);
      throw new Error(`Session end failed: ${res.status} ${res.statusText}`);
    }
  }

  /** PUT /api/v1/sessions/:id/outcome — report an outcome. */
  async reportOutcome(sessionId: string, outcome: OutcomeType): Promise<void> {
    if (this.disabled) {
      return; // Silent fail
    }

    const res = await fetch(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/outcome`,
      {
        method: "PUT",
        headers: this.headers,
        body: JSON.stringify({ outcome }),
      },
    );

    if (!res.ok) {
      this.handleAuthError(res);
      throw new Error(`Outcome report failed: ${res.status} ${res.statusText}`);
    }
  }

  /** Combined: end session WITH outcome. */
  async endSessionWithOutcome(sessionId: string, outcome: OutcomeType): Promise<void> {
    if (this.disabled) {
      return; // Silent fail
    }

    // First report outcome, then end session
    await this.reportOutcome(sessionId, outcome);
    await this.endSession(sessionId);
  }

  /**
   * Send events via sendBeacon (for page unload).
   * Returns true if the browser accepted the beacon.
   */
  sendBeacon(payload: BatchPayload): boolean {
    if (typeof navigator === "undefined" || !navigator.sendBeacon) return false;
    const blob = new Blob([JSON.stringify(payload)], {
      type: "application/json",
    });
    return navigator.sendBeacon(
      `${this.baseUrl}/api/v1/events/batch?sdk_key=${this.headers["X-SDK-Key"]}`,
      blob,
    );
  }

  /**
   * End session via sendBeacon (for page unload).
   */
  sendBeaconEnd(sessionId: string): boolean {
    if (typeof navigator === "undefined" || !navigator.sendBeacon) return false;
    const blob = new Blob([JSON.stringify({})], { type: "application/json" });
    return navigator.sendBeacon(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/end?sdk_key=${this.headers["X-SDK-Key"]}`,
      blob,
    );
  }

  /**
   * Report outcome via sendBeacon (for page unload).
   */
  sendBeaconOutcome(sessionId: string, outcome: "purchase" | "abandon"): boolean {
    if (typeof navigator === "undefined" || !navigator.sendBeacon) return false;
    const data = JSON.stringify({ outcome });
    const blob = new Blob([data], { type: "application/json" });
    return navigator.sendBeacon(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/outcome?sdk_key=${this.headers["X-SDK-Key"]}`,
      blob,
    );
  }

  /**
   * Combined close via sendBeacon — ends session AND sets outcome to 'abandon' in one call.
   * More reliable than making two separate beacon calls during page unload.
   */
  sendBeaconClose(sessionId: string): boolean {
    if (typeof navigator === "undefined" || !navigator.sendBeacon) return false;
    const blob = new Blob([JSON.stringify({})], { type: "application/json" });
    return navigator.sendBeacon(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/close?sdk_key=${this.headers["X-SDK-Key"]}`,
      blob,
    );
  }
}
