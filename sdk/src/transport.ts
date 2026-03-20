/**
 * Transport layer — handles HTTP communication with the backend API (CONV-33).
 *
 * Uses fetch() for normal requests and navigator.sendBeacon() for page
 * unload scenarios (sendBeacon is fire-and-forget but reliable during unload).
 */

import type { BatchPayload, SessionCreatePayload, SessionCreateResponse } from "./types";

export class Transport {
  private readonly baseUrl: string;
  private readonly headers: Record<string, string>;

  constructor(apiUrl: string, sdkKeyHash: string) {
    this.baseUrl = apiUrl.replace(/\/+$/, "");
    this.headers = {
      "Content-Type": "application/json",
      "X-SDK-Key": sdkKeyHash,
    };
  }

  /** POST /api/v1/sessions — create a new session. */
  async createSession(
    payload: SessionCreatePayload,
  ): Promise<SessionCreateResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/sessions`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Session create failed: ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as SessionCreateResponse;
  }

  /** POST /api/v1/events/batch — send a batch of events. */
  async sendEvents(payload: BatchPayload): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/v1/events/batch`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Event batch failed: ${res.status} ${res.statusText}`);
    }
  }

  /** PUT /api/v1/sessions/:id/end — end a session. */
  async endSession(sessionId: string): Promise<void> {
    const res = await fetch(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/end`,
      {
        method: "PUT",
        headers: this.headers,
      },
    );

    if (!res.ok) {
      throw new Error(`Session end failed: ${res.status} ${res.statusText}`);
    }
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
}
