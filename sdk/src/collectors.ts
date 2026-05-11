/**
 * Event collectors — capture DOM events and transform them into RawEvents (CONV-31, CONV-32).
 *
 * ── CRITICAL: COLLECTION vs STORAGE SEPARATION ────────────────────────
 *
 * These collectors maintain INTERNAL STATE that is ALWAYS updated, regardless
 * of event storage limits. This ensures behavioral analytics quality:
 *
 *   COLLECTION (always active):
 *   - Event listeners are never removed
 *   - Rage click buffer tracks recent clicks
 *   - Mouse state tracks position for velocity
 *   - Scroll state tracks direction and retreats
 *
 *   STORAGE (limited by MAX_EVENTS_PER_SESSION):
 *   - High priority events (click, exit_intent, visibility, mouse_summary)
 *     are ALWAYS stored, even after limit
 *   - Low priority events (mouse_move, scroll) are dropped after limit
 *   - mouse_summary provides aggregated data to preserve velocity signals
 *
 * This separation means: after 1000 events, we still detect rage clicks,
 * still compute velocity, and still store summaries of mouse behavior.
 *
 * ───────────────────────────────────────────────────────────────────────
 *
 * Each collector attaches browser event listeners and pushes RawEvents
 * to the EventQueue. Collectors are designed to be:
 *   - Non-blocking (throttled, passive listeners)
 *   - Minimal DOM impact (no layout thrashing)
 *   - Rich enough for ML feature extraction
 */

import type { EventQueue } from "./event-queue";
import type { RawEvent } from "./types";
import { getElementId, isoNow, throttle } from "./utils";
import { enrichEventElement } from "./semantic";

type Cleanup = () => void;
type MetadataProvider = () => Record<string, unknown> | null;

// Default metadata provider (returns null)
const defaultMetadataProvider: MetadataProvider = () => null;

// ── Mouse Move Collector ──────────────────────────────────────
//
// INTERNAL STATE (always maintained, never affected by event limit):
//   - lastX, lastY: for velocity calculation
//   - lastTime: for velocity calculation
//   - velocitySamples: rolling buffer for aggregation (up to 100 samples)
//
// STORAGE (limited by MAX_EVENTS_PER_SESSION):
//   - mouse_move events: dropped after limit (low priority)
//   - mouse_summary events: ALWAYS stored (high priority)
//     Provides aggregated velocity data even after 1000 events

export function collectMouseMove(
  queue: EventQueue,
  throttleMs: number,
  getMetadata: MetadataProvider = defaultMetadataProvider,
): Cleanup {
  let lastX = 0;
  let lastY = 0;
  let lastTime = 0;

  // INTERNAL STATE for aggregation (NOT affected by event limit)
  // Maintains up to 100 velocity samples for summary generation
  const velocitySamples: number[] = [];
  const MAX_SAMPLES = 100;
  let lastSummaryTime = Date.now();
  const SUMMARY_INTERVAL_MS = 5000; // Emit summary every 5 seconds

  const handler = throttle((e: unknown) => {
    const ev = e as MouseEvent;
    const now = Date.now();
    const dt = lastTime > 0 ? (now - lastTime) / 1000 : 0;
    const dx = ev.clientX - lastX;
    const dy = ev.clientY - lastY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const velocity = dt > 0 ? dist / dt : 0;

    // ALWAYS update internal state (collection vs storage separation)
    velocitySamples.push(velocity);
    if (velocitySamples.length > MAX_SAMPLES) {
      velocitySamples.shift();
    }

    // Extract semantic information from element under cursor (lightweight)
    const semantic = enrichEventElement(ev.target as Element);

    const providerMetadata = getMetadata();
    const metadata = providerMetadata
      ? { ...providerMetadata }
      : null;

    // Try to store raw event (may be dropped after limit)
    const rawEvent: RawEvent = {
      type: "mouse_move",
      ts: isoNow(),
      x: ev.clientX,
      y: ev.clientY,
      velocity: Math.round(velocity * 100) / 100,
      // Backward compatibility
      element_id: getElementId(ev.target as Element),
      // Semantic enrichment
      label: semantic.label,
      element_type: semantic.element_type,
      section: semantic.section,
      selector: semantic.selector,
      metadata,
    };

    queue.push(rawEvent);

    // Emit summary periodically (HIGH PRIORITY - always stored)
    // This preserves velocity signals even after 1000 events
    if (now - lastSummaryTime >= SUMMARY_INTERVAL_MS && velocitySamples.length > 0) {
      const sum = velocitySamples.reduce((a, b) => a + b, 0);
      const avg = Math.round((sum / velocitySamples.length) * 100) / 100;
      const max = Math.round(Math.max(...velocitySamples) * 100) / 100;

      // Detect pattern: erratic vs smooth
      const variance = velocitySamples.reduce((acc, v) => acc + Math.pow(v - avg, 2), 0) / velocitySamples.length;
      const pattern = variance > 10000 ? "erratic" : avg > 500 ? "fast" : "smooth";

      const summaryEvent: RawEvent = {
        type: "mouse_summary",
        ts: isoNow(),
        metadata: {
          avg_velocity: avg,
          max_velocity: max,
          sample_count: velocitySamples.length,
          movement_pattern: pattern,
          ...metadata,
        },
      };

      queue.push(summaryEvent);
      lastSummaryTime = now;
    }

    lastX = ev.clientX;
    lastY = ev.clientY;
    lastTime = now;
  }, throttleMs);

  document.addEventListener("mousemove", handler, { passive: true });
  return () => document.removeEventListener("mousemove", handler);
}

// ── Click Collector ───────────────────────────────────────────
//
// INTERNAL STATE (always maintained, never affected by event limit):
//   - recentClicks: buffer of last 2 seconds of clicks
//
// CRITICAL: Rage click detection works even after 1000 events because:
//   1. The recentClicks buffer is local to this collector (not in EventQueue)
//   2. Click events are HIGH PRIORITY - always stored even after limit
//   3. Rage click metadata is computed and stored with every click

export function collectClicks(
  queue: EventQueue,
  getMetadata: MetadataProvider = defaultMetadataProvider,
): Cleanup {
  // INTERNAL BUFFER for rage click detection (NOT affected by event limit)
  const recentClicks: { x: number; y: number; time: number }[] = [];

  const handler = (e: MouseEvent) => {
    const now = Date.now();

    // ALWAYS track for rage-click detection (collection vs storage separation)
    recentClicks.push({ x: e.clientX, y: e.clientY, time: now });

    // Remove clicks older than 2 seconds
    while (recentClicks.length > 0 && now - recentClicks[0].time > 2000) {
      recentClicks.shift();
    }

    // Check for rage click: 3+ clicks within 2s in 50px radius
    const nearby = recentClicks.filter((c) => {
      const dx = c.x - e.clientX;
      const dy = c.y - e.clientY;
      return Math.sqrt(dx * dx + dy * dy) <= 50;
    });
    const isRageClick = nearby.length >= 3;

    // Extract semantic information from the clicked element
    const semantic = enrichEventElement(e.target as Element);

    const providerMetadata = getMetadata();
    const baseMetadata = isRageClick
      ? { rage_click: true, click_count: nearby.length }
      : null;

    // Merge all metadata
    const metadata: Record<string, unknown> = {
      ...(baseMetadata || {}),
      ...(providerMetadata || {}),
      // Include data-* attributes in metadata
      ...(semantic.data_attrs && Object.keys(semantic.data_attrs).length > 0
        ? semantic.data_attrs
        : {}),
    };

    // Add role if detected (e.g., CTA)
    if (semantic.role) {
      metadata.role = semantic.role;
    }

    const event: RawEvent = {
      type: "click",
      ts: isoNow(),
      x: e.clientX,
      y: e.clientY,
      // Backward compatibility: keep element_id
      element_id: getElementId(e.target as Element),
      // Semantic enrichment (NEW)
      label: semantic.label,
      element_type: semantic.element_type,
      section: semantic.section,
      selector: semantic.selector,
      metadata: Object.keys(metadata).length > 0 ? metadata : null,
    };

    // Click is HIGH PRIORITY - always stored, even after MAX_EVENTS_PER_SESSION
    // This ensures rage click metadata is never lost
    queue.push(event);
  };

  document.addEventListener("click", handler, { passive: true });
  return () => document.removeEventListener("click", handler);
}

// ── Scroll Collector ──────────────────────────────────────────
//
// INTERNAL STATE (always maintained, never affected by event limit):
//   - lastScrollY, lastDirection: for retreat detection
//
// STORAGE (limited by MAX_EVENTS_PER_SESSION):
//   - scroll events are LOW PRIORITY - dropped after limit
//   - Direction and retreat patterns are still computed internally

export function collectScroll(
  queue: EventQueue,
  getMetadata: MetadataProvider = defaultMetadataProvider,
): Cleanup {
  // INTERNAL STATE for scroll direction tracking (NOT affected by event limit)
  let lastScrollY = window.scrollY;
  let lastDirection: "up" | "down" | null = null;

  const handler = throttle(() => {
    const currentY = window.scrollY;
    const delta = currentY - lastScrollY;
    if (Math.abs(delta) < 5) return; // ignore micro-scrolls

    const direction: "up" | "down" = delta > 0 ? "down" : "up";
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const viewportPct =
      docHeight > 0 ? Math.round((currentY / docHeight) * 10000) / 100 : 0;

    const providerMetadata = getMetadata();
    const metadata: Record<string, unknown> = {
      direction,
      delta: Math.round(Math.abs(delta)),
      viewport_pct: viewportPct,
      is_retreat: direction === "up" && lastDirection === "down",
      ...(providerMetadata || {}),
    };

    const event: RawEvent = {
      type: "scroll",
      ts: isoNow(),
      metadata,
    };

    // Try to store (may be dropped after limit - scroll is LOW PRIORITY)
    queue.push(event);
    lastScrollY = currentY;
    lastDirection = direction;
  }, 200); // Throttle scroll events to every 200ms

  window.addEventListener("scroll", handler, { passive: true });
  return () => window.removeEventListener("scroll", handler);
}

// ── Exit Intent Collector (CONV-32) ───────────────────────────

export function collectExitIntent(
  queue: EventQueue,
  getMetadata: MetadataProvider = defaultMetadataProvider,
): Cleanup {
  const cleanups: Cleanup[] = [];

  // 1. Mouse leaving viewport top (desktop)
  const mouseLeaveHandler = (e: MouseEvent) => {
    if (e.clientY <= 0) {
      const providerMetadata = getMetadata();
      queue.push({
        type: "exit_intent",
        ts: isoNow(),
        x: e.clientX,
        y: e.clientY,
        metadata: { trigger: "mouse_leave", ...(providerMetadata || {}) },
      });
    }
  };
  document.addEventListener("mouseout", mouseLeaveHandler);
  cleanups.push(() =>
    document.removeEventListener("mouseout", mouseLeaveHandler),
  );

  // 2. Back button / history navigation
  const popstateHandler = () => {
    const providerMetadata = getMetadata();
    queue.push({
      type: "exit_intent",
      ts: isoNow(),
      metadata: { trigger: "back_button", ...(providerMetadata || {}) },
    });
  };
  window.addEventListener("popstate", popstateHandler);
  cleanups.push(() => window.removeEventListener("popstate", popstateHandler));

  return () => cleanups.forEach((fn) => fn());
}

// ── Visibility Collector (CONV-32) ────────────────────────────

export function collectVisibility(
  queue: EventQueue,
  getMetadata: MetadataProvider = defaultMetadataProvider,
): Cleanup {
  const handler = () => {
    const state = document.visibilityState as "visible" | "hidden";
    const providerMetadata = getMetadata();

    queue.push({
      type: "visibility",
      ts: isoNow(),
      metadata: { state, ...(providerMetadata || {}) },
    });

    // Tab switch counts as exit intent
    if (state === "hidden") {
      queue.push({
        type: "exit_intent",
        ts: isoNow(),
        metadata: { trigger: "tab_switch", ...(providerMetadata || {}) },
      });
    }
  };

  document.addEventListener("visibilitychange", handler);
  return () => document.removeEventListener("visibilitychange", handler);
}

// ── End of collectors ────────────────────────────────────────────────
// Mouse path replay functions have been removed - will be replaced with rrweb
