/**
 * rrweb DOM recorder — captures page interactions for session replay.
 *
 * Uses rrweb library to record DOM mutations, user interactions, and
 * visual changes. Records up to 60 seconds with a 10,000 event limit.
 *
 * Privacy: All input values are masked by default. Elements with
 * data-emoratest-mask attribute are also masked.
 *
 * STORAGE: Replay data is stored in session_replay_data table.
 * TODO: Implement 30-day auto-delete for old replay data.
 */

import { record } from "rrweb";

// RRWeb event compatible with Record<string, unknown>
export type RRWebEvent = Record<string, unknown> & {
  type: number;
  timestamp: number;
};

export interface RRWebRecording {
  events: Record<string, unknown>[];
  durationMs: number;
  eventsCount: number;
}

/** Maximum recording duration in milliseconds (60 seconds) */
const MAX_DURATION_MS = 60 * 1000;

/** Maximum number of events before auto-stopping */
const MAX_EVENTS = 10000;

/** Maximum payload size in bytes (5MB) */
const MAX_PAYLOAD_BYTES = 5 * 1024 * 1024;

export class RRWebRecorder {
  private events: RRWebEvent[] = [];
  private startTime: number = 0;
  private isRecordingFlag: boolean = false;
  private stopper: (() => void) | null = null;
  private timeoutId: ReturnType<typeof setTimeout> | null = null;

  /** Start recording DOM events. */
  start(): void {
    if (this.isRecordingFlag) {
      return; // Already recording
    }

    this.events = [];
    this.startTime = Date.now();
    this.isRecordingFlag = true;

    try {
      // Start rrweb recording with privacy masking
      this.stopper = record({
        emit: (event) => {
          if (!this.isRecordingFlag) return;

          this.events.push(event as RRWebEvent);

          // Auto-stop if we hit max events
          if (this.events.length >= MAX_EVENTS) {
            this.stop();
          }
        },
        // Privacy: Mask all input values by default
        maskAllInputs: true,
        // Additional privacy: mask elements with data-emoratest-mask attribute
        maskTextSelector: '[data-emoratest-mask]',
        // Don't record canvas (performance + privacy)
        recordCanvas: false,
        // Don't record cross-origin iframes (privacy/security)
        recordCrossOriginIframes: false,
      }) as (() => void) | null;

      // Auto-stop after 60 seconds
      this.timeoutId = setTimeout(() => {
        this.stop();
      }, MAX_DURATION_MS);
    } catch (err) {
      // Recording failed silently - don't break event tracking
      this.isRecordingFlag = false;
      this.cleanup();
    }
  }

  /** Stop recording and return the captured events. */
  stop(): RRWebRecording | null {
    if (!this.isRecordingFlag) {
      return null;
    }

    this.isRecordingFlag = false;
    this.cleanup();

    const durationMs = Date.now() - this.startTime;
    const eventsCount = this.events.length;

    // Check payload size (silently skip if too large)
    const payloadSize = this.getPayloadSize();

    if (payloadSize > MAX_PAYLOAD_BYTES) {
      // Recording too large, silently discard
      return null;
    }

    return {
      events: this.events as unknown as Record<string, unknown>[],
      durationMs,
      eventsCount,
    };
  }

  /** Get the recorded events array without stopping. */
  getEvents(): RRWebEvent[] {
    return [...this.events];
  }

  /** Get the current recording duration in milliseconds. */
  getDuration(): number {
    if (!this.isRecordingFlag) return 0;
    return Date.now() - this.startTime;
  }

  /** Check if currently recording. */
  isRecording(): boolean {
    return this.isRecordingFlag;
  }

  /** Calculate the approximate JSON payload size in bytes. */
  private getPayloadSize(): number {
    try {
      const json = JSON.stringify(this.events);
      return new Blob([json]).size;
    } catch {
      // Fallback estimate: ~200 bytes per event
      return this.events.length * 200;
    }
  }

  /** Clean up resources. */
  private cleanup(): void {
    if (this.stopper) {
      try {
        this.stopper();
      } catch {
        // Ignore errors during stop
      }
      this.stopper = null;
    }

    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }
}
