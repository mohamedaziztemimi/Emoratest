/**
 * Event queue with periodic flushing and priority-based filtering.
 *
 * ── COLLECTION vs STORAGE SEPARATION ─────────────────────────────────
 *
 * This queue handles STORAGE only. COLLECTION happens in collectors.ts.
 *
 * COLLECTORS (always active, never stop listening):
 *   - Maintain internal buffers (rage clicks, velocity samples)
 *   - Compute behavioral signals (rage_click, movement_pattern)
 *   - Pass events to queue.push() regardless of limit
 *
 * QUEUE (filters based on priority and limit):
 *   - HIGH PRIORITY events: ALWAYS stored (click, exit_intent, visibility, mouse_summary)
 *   - LOW PRIORITY events: Dropped after MAX_EVENTS_PER_SESSION (mouse_move, scroll)
 *
 * This ensures behavioral analytics quality even after 1000 events:
 *   - Rage click detection works (clicks are high priority)
 *   - Velocity signals preserved (mouse_summary is high priority)
 *   - Exit intent captured (exit_intent is high priority)
 *
 * ────────────────────────────────────────────────────────────────────────
 *
 * Events are queued locally and flushed to the backend every N ms
 * or when the queue reaches maxBatchSize. On page unload, remaining
 * events are sent via navigator.sendBeacon().
 */

import type { RawEvent, EventType, HIGH_PRIORITY_EVENTS, LOW_PRIORITY_EVENTS, MousePathPoint } from "./types";
import type { Transport } from "./transport";
import type { MousePathTracker } from "./collectors";

export class EventQueue {
  private queue: RawEvent[] = [];
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private sessionId: string | null = null;
  private readonly transport: Transport;
  private readonly flushIntervalMs: number;
  private readonly maxBatchSize: number;
  private readonly debug: boolean;
  private readonly maxEvents: number;
  private eventCount = 0;
  private isStopped = false;
  // Store session context for auto-creation fallback
  private deviceType: string | null = null;
  private countryCode: string | null = null;
  // Mouse path tracker for replay data
  private mousePathTracker: MousePathTracker | null = null;

  // Import types dynamically for priority checking
  // Fallback sets in case dynamic import fails (mouse_summary is high priority)
  private highPriorityEvents: Set<EventType> = new Set(["click", "exit_intent", "visibility", "mouse_summary"]);
  private lowPriorityEvents: Set<EventType> = new Set(["mouse_move", "scroll"]);

  constructor(
    transport: Transport,
    flushIntervalMs: number,
    maxBatchSize: number,
    debug: boolean,
    maxEvents: number = 1000,
  ) {
    this.transport = transport;
    this.flushIntervalMs = flushIntervalMs;
    this.maxBatchSize = maxBatchSize;
    this.debug = debug;
    this.maxEvents = maxEvents;

    // Load priority sets
    import("./types").then((types) => {
      this.highPriorityEvents = types.HIGH_PRIORITY_EVENTS as unknown as Set<EventType>;
      this.lowPriorityEvents = types.LOW_PRIORITY_EVENTS as unknown as Set<EventType>;
    });
  }

  /** Set the active session ID (events require this). */
  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  /** Set device type for session auto-creation fallback. */
  setDeviceType(deviceType: string | null): void {
    this.deviceType = deviceType;
  }

  /** Set country code for session auto-creation fallback. */
  setCountryCode(countryCode: string | null): void {
    this.countryCode = countryCode;
  }

  /** Set the mouse path tracker for replay data. */
  setMousePathTracker(tracker: MousePathTracker | null): void {
    this.mousePathTracker = tracker;
  }

  /** Get the current event count. */
  getEventCount(): number {
    return this.eventCount;
  }

  /** Check if event limit has been reached. */
  isAtLimit(): boolean {
    return this.eventCount >= this.maxEvents;
  }

  /** Check if should track an event based on type and limit. */
  shouldTrack(eventType: EventType): boolean {
    // Always allow high priority events
    if (this.highPriorityEvents.has(eventType)) {
      return true;
    }

    // Check limit for low priority events
    if (this.lowPriorityEvents.has(eventType)) {
      return this.eventCount < this.maxEvents;
    }

    // Default: allow if under limit
    return this.eventCount < this.maxEvents;
  }

  /** Add an event to the queue. Returns true if queued, false if dropped. */
  push(event: RawEvent): boolean {
    if (this.isStopped) return false;

    // Check if we should track this event
    if (!this.shouldTrack(event.type)) {
      if (this.debug) {
        console.debug(`[EmoraTest] Event dropped (limit): ${event.type}`);
      }
      return false;
    }

    this.queue.push(event);
    this.eventCount++;

    if (this.debug && this.eventCount >= this.maxEvents) {
      console.debug(`[EmoraTest] Event limit reached: ${this.eventCount} >= ${this.maxEvents}`);
    }

    if (this.debug) {
      console.debug("[EmoraTest] Event queued:", event.type, `count: ${this.eventCount}/${this.maxEvents}`);
    }

    if (this.queue.length >= this.maxBatchSize) {
      this.flush().catch(this.logError);
    }

    return true;
  }

  /** Start the periodic flush timer. */
  start(): void {
    if (this.flushTimer) return;

    this.flushTimer = setInterval(() => {
      if (!this.isStopped) {
        this.flush().catch(this.logError);
      }
    }, this.flushIntervalMs);

    // Also flush on tab visibility change (user switching away)
    const visibilityHandler = () => {
      if (document.visibilityState === "hidden" && !this.isStopped) {
        this.flushBeacon();
      }
    };

    document.addEventListener("visibilitychange", visibilityHandler);
  }

  /** Stop the flush timer and prevent further queuing. */
  stop(): void {
    this.isStopped = true;
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  /** Flush all queued events to the backend. */
  async flush(): Promise<void> {
    if (this.queue.length === 0 || !this.sessionId) return;

    const events = this.queue.splice(0, this.maxBatchSize);

    if (this.debug) {
      console.debug(`[EmoraTest] Flushing ${events.length} events`);
    }

    // Get current page URL for session tracking
    const pageUrl = typeof window !== "undefined" ? window.location.href : undefined;

    try {
      await this.transport.sendEvents({
        session_id: this.sessionId,
        events,
        page_url: pageUrl,
        device_type: this.deviceType,
        country_code: this.countryCode,
        mouse_path: this.mousePathTracker?.getPath() ?? undefined,
        // Include page metadata for replay
        ...(this.mousePathTracker?.getPageMetadata() ?? {}),
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

    // Get current page URL for session tracking
    const pageUrl = typeof window !== "undefined" ? window.location.href : undefined;

    this.transport.sendBeacon({
      session_id: this.sessionId,
      events,
      page_url: pageUrl,
      device_type: this.deviceType,
      country_code: this.countryCode,
      mouse_path: this.mousePathTracker?.getPath() ?? undefined,
      // Include page metadata for replay
      ...(this.mousePathTracker?.getPageMetadata() ?? {}),
    });
  }

  /** Number of events currently queued. */
  get size(): number {
    return this.queue.length;
  }

  /** Get total events tracked this session. */
  getTotalTracked(): number {
    return this.eventCount;
  }

  private logError = (err: unknown): void => {
    if (this.debug) {
      console.error("[EmoraTest] Flush error:", err);
    }
  };
}
