/**
 * Event collectors — capture DOM events and transform them into RawEvents (CONV-31, CONV-32).
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

type Cleanup = () => void;

// ── Mouse Move Collector ──────────────────────────────────────

export function collectMouseMove(
  queue: EventQueue,
  throttleMs: number,
): Cleanup {
  let lastX = 0;
  let lastY = 0;
  let lastTime = 0;

  const handler = throttle((e: unknown) => {
    const ev = e as MouseEvent;
    const now = Date.now();
    const dt = lastTime > 0 ? (now - lastTime) / 1000 : 0;
    const dx = ev.clientX - lastX;
    const dy = ev.clientY - lastY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const velocity = dt > 0 ? dist / dt : 0;

    const event: RawEvent = {
      type: "mouse_move",
      ts: isoNow(),
      x: ev.clientX,
      y: ev.clientY,
      velocity: Math.round(velocity * 100) / 100,
      element_id: getElementId(ev.target as Element),
    };

    queue.push(event);

    lastX = ev.clientX;
    lastY = ev.clientY;
    lastTime = now;
  }, throttleMs);

  document.addEventListener("mousemove", handler, { passive: true });
  return () => document.removeEventListener("mousemove", handler);
}

// ── Click Collector ───────────────────────────────────────────

export function collectClicks(queue: EventQueue): Cleanup {
  const recentClicks: { x: number; y: number; time: number }[] = [];

  const handler = (e: MouseEvent) => {
    const now = Date.now();

    // Track for rage-click detection
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

    const event: RawEvent = {
      type: "click",
      ts: isoNow(),
      x: e.clientX,
      y: e.clientY,
      element_id: getElementId(e.target as Element),
      metadata: isRageClick
        ? { rage_click: true, click_count: nearby.length }
        : null,
    };

    queue.push(event);
  };

  document.addEventListener("click", handler, { passive: true });
  return () => document.removeEventListener("click", handler);
}

// ── Scroll Collector ──────────────────────────────────────────

export function collectScroll(queue: EventQueue): Cleanup {
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

    const event: RawEvent = {
      type: "scroll",
      ts: isoNow(),
      metadata: {
        direction,
        delta: Math.round(Math.abs(delta)),
        viewport_pct: viewportPct,
        is_retreat: direction === "up" && lastDirection === "down",
      },
    };

    queue.push(event);
    lastScrollY = currentY;
    lastDirection = direction;
  }, 200); // Throttle scroll events to every 200ms

  window.addEventListener("scroll", handler, { passive: true });
  return () => window.removeEventListener("scroll", handler);
}

// ── Exit Intent Collector (CONV-32) ───────────────────────────

export function collectExitIntent(queue: EventQueue): Cleanup {
  const cleanups: Cleanup[] = [];

  // 1. Mouse leaving viewport top (desktop)
  const mouseLeaveHandler = (e: MouseEvent) => {
    if (e.clientY <= 0) {
      queue.push({
        type: "exit_intent",
        ts: isoNow(),
        x: e.clientX,
        y: e.clientY,
        metadata: { trigger: "mouse_leave" },
      });
    }
  };
  document.addEventListener("mouseout", mouseLeaveHandler);
  cleanups.push(() =>
    document.removeEventListener("mouseout", mouseLeaveHandler),
  );

  // 2. Back button / history navigation
  const popstateHandler = () => {
    queue.push({
      type: "exit_intent",
      ts: isoNow(),
      metadata: { trigger: "back_button" },
    });
  };
  window.addEventListener("popstate", popstateHandler);
  cleanups.push(() => window.removeEventListener("popstate", popstateHandler));

  return () => cleanups.forEach((fn) => fn());
}

// ── Visibility Collector (CONV-32) ────────────────────────────

export function collectVisibility(queue: EventQueue): Cleanup {
  const handler = () => {
    const state = document.visibilityState as "visible" | "hidden";

    queue.push({
      type: "visibility",
      ts: isoNow(),
      metadata: { state },
    });

    // Tab switch counts as exit intent
    if (state === "hidden") {
      queue.push({
        type: "exit_intent",
        ts: isoNow(),
        metadata: { trigger: "tab_switch" },
      });
    }
  };

  document.addEventListener("visibilitychange", handler);
  return () => document.removeEventListener("visibilitychange", handler);
}
