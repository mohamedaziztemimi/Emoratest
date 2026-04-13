/**
 * Event queue with periodic flushing (CONV-33).
 *
 * Events are queued locally and flushed to the backend every N ms
 * or when the queue reaches maxBatchSize. On page unload, remaining
 * events are sent via navigator.sendBeacon().
 */

import type { RawEvent } from "./types";
import type { Transport } from "./transport";

export class EventQueue {
  private queue: RawEvent[] = [];
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private sessionId: string | null = null;
  private readonly transport: Transport;
  private readonly flushIntervalMs: number;
  private readonly maxBatchSize: number;
  private readonly debug: boolean;

  constructor(
    transport: Transport,
    flushIntervalMs: number,
    maxBatchSize: number,
    debug: boolean,
  ) {
    this.transport = transport;
    this.flushIntervalMs = flushIntervalMs;
    this.maxBatchSize = maxBatchSize;
    this.debug = debug;
  }

  /** Set the active session ID (events require this). */
  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  /** Start the periodic flush timer. */
  start(): void {
    if (this.flushTimer) return;
    this.flushTimer = setInterval(() => {
      this.flush().catch(this.logError);
    }, this.flushIntervalMs);
  }

  /** Stop the flush timer. */
  stop(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  /** Add an event to the queue. Triggers flush if batch is full. */
  push(event: RawEvent): void {
    this.queue.push(event);

    if (this.debug) {
      console.debug("[EmoraTest] Event queued:", event.type, event);
    }

    if (this.queue.length >= this.maxBatchSize) {
      this.flush().catch(this.logError);
    }
  }

  /** Flush all queued events to the backend. */
  async flush(): Promise<void> {
    if (this.queue.length === 0 || !this.sessionId) return;

    const events = this.queue.splice(0, this.maxBatchSize);

    if (this.debug) {
      console.debug(`[EmoraTest] Flushing ${events.length} events`);
    }

    try {
      await this.transport.sendEvents({
        session_id: this.sessionId,
        events,
      });
    } catch (err) {
      // Re-queue on failure (at the front)
      this.queue.unshift(...events);
      this.logError(err);
    }
  }

  /** Flush remaining events via sendBeacon (for page unload). */
  flushBeacon(): void {
    if (this.queue.length === 0 || !this.sessionId) return;

    const events = this.queue.splice(0);

    if (this.debug) {
      console.debug(
        `[EmoraTest] Beacon flush: ${events.length} events`,
      );
    }

    this.transport.sendBeacon({
      session_id: this.sessionId,
      events,
    });
  }

  /** Number of events currently queued. */
  get size(): number {
    return this.queue.length;
  }

  private logError = (err: unknown): void => {
    if (this.debug) {
      console.error("[EmoraTest] Flush error:", err);
    }
  };
}
