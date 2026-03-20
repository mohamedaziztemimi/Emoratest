/**
 * Conversiono SDK — main entry point.
 *
 * Usage (script tag):
 *   <script src="https://cdn.conversiono.com/sdk/conversiono.min.js"></script>
 *   <script>
 *     Conversiono.init({ sdkKey: 'your-key-here' });
 *   </script>
 *
 * Usage (npm):
 *   import { init } from '@conversiono/sdk';
 *   init({ sdkKey: 'your-key-here' });
 */

import {
  collectClicks,
  collectExitIntent,
  collectMouseMove,
  collectScroll,
  collectVisibility,
} from "./collectors";
import { EventQueue } from "./event-queue";
import { SessionManager } from "./session";
import { Transport } from "./transport";
import type { ConversionoConfig, ResolvedConfig } from "./types";
import { sha256 } from "./utils";

// Re-export types for consumers
export type {
  ConversionoConfig,
  RawEvent,
  BatchPayload,
  SessionCreatePayload,
  SessionCreateResponse,
} from "./types";

// ── Module state ──────────────────────────────────────────────

let config: ResolvedConfig | null = null;
let transport: Transport | null = null;
let queue: EventQueue | null = null;
let sessionManager: SessionManager | null = null;
let cleanups: (() => void)[] = [];
let initialized = false;

// ── Public API ────────────────────────────────────────────────

/**
 * Initialize the Conversiono SDK.
 * Call this once per page load. Starts session tracking and event capture.
 */
export async function init(userConfig: ConversionoConfig): Promise<void> {
  if (initialized) {
    console.warn("[Conversiono] Already initialized. Call destroy() first.");
    return;
  }

  if (userConfig.disabled) {
    if (userConfig.debug) console.debug("[Conversiono] Disabled by config");
    return;
  }

  // Validate
  if (!userConfig.sdkKey) {
    throw new Error("[Conversiono] sdkKey is required");
  }

  // Resolve config with defaults
  const sdkKeyHash = await sha256(userConfig.sdkKey);

  config = {
    sdkKey: userConfig.sdkKey,
    sdkKeyHash,
    apiUrl: userConfig.apiUrl ?? window.location.origin,
    flushIntervalMs: userConfig.flushIntervalMs ?? 2000,
    maxBatchSize: userConfig.maxBatchSize ?? 50,
    mouseMoveThrottleMs: userConfig.mouseMoveThrottleMs ?? 100,
    debug: userConfig.debug ?? false,
    disabled: false,
  };

  // Set up components
  transport = new Transport(config.apiUrl, config.sdkKeyHash);
  queue = new EventQueue(
    transport,
    config.flushIntervalMs,
    config.maxBatchSize,
    config.debug,
  );
  sessionManager = new SessionManager(transport, config.debug);

  // Create session — use sdkKeyHash as merchantId placeholder
  // (backend resolves actual merchant_id from the SDK key)
  const session = await sessionManager.start(config.sdkKeyHash);
  queue.setSessionId(session.sessionId);
  queue.start();

  // Attach event collectors
  cleanups = [
    collectMouseMove(queue, config.mouseMoveThrottleMs),
    collectClicks(queue),
    collectScroll(queue),
    collectExitIntent(queue),
    collectVisibility(queue),
  ];

  // Handle page unload
  const unloadHandler = () => {
    if (queue) queue.flushBeacon();
    if (sessionManager) sessionManager.endBeacon();
  };

  window.addEventListener("beforeunload", unloadHandler);
  cleanups.push(() =>
    window.removeEventListener("beforeunload", unloadHandler),
  );

  // Handle page visibility for mobile (no beforeunload on iOS)
  const mobileUnloadHandler = () => {
    if (document.visibilityState === "hidden") {
      if (queue) queue.flushBeacon();
    }
  };
  document.addEventListener("visibilitychange", mobileUnloadHandler);
  cleanups.push(() =>
    document.removeEventListener("visibilitychange", mobileUnloadHandler),
  );

  initialized = true;

  if (config.debug) {
    console.debug("[Conversiono] Initialized", {
      sessionId: session.sessionId,
      apiUrl: config.apiUrl,
    });
  }
}

/** Stop tracking and clean up all resources. */
export async function destroy(): Promise<void> {
  if (!initialized) return;

  // Flush remaining events
  if (queue) {
    await queue.flush();
    queue.stop();
  }

  // End session
  if (sessionManager) {
    await sessionManager.end();
  }

  // Remove event listeners
  cleanups.forEach((fn) => fn());
  cleanups = [];

  config = null;
  transport = null;
  queue = null;
  sessionManager = null;
  initialized = false;
}

/** Get the current session ID (for custom event correlation). */
export function getSessionId(): string | null {
  return sessionManager?.getSessionId() ?? null;
}

/** Check if the SDK is currently initialized and tracking. */
export function isInitialized(): boolean {
  return initialized;
}

/** Manually report a conversion outcome. */
export async function reportOutcome(
  outcome: "purchase" | "abandon",
): Promise<void> {
  if (!initialized || !transport || !sessionManager) return;

  const sessionId = sessionManager.getSessionId();
  if (!sessionId) return;

  try {
    await fetch(
      `${config!.apiUrl}/api/v1/sessions/${sessionId}/outcome`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-SDK-Key": config!.sdkKeyHash,
        },
        body: JSON.stringify({ outcome }),
      },
    );
  } catch (err) {
    if (config?.debug) {
      console.error("[Conversiono] Failed to report outcome:", err);
    }
  }
}
