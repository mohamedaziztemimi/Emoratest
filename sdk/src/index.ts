/**
 * EmoraTest SDK — main entry point.
 *
 * Usage (script tag):
 *   <script src="https://cdn.emoratest.com/sdk/emoratest.min.js"></script>
 *   <script>
 *     EmoraTest.init({ sdkKey: 'your-key-here' });
 *   </script>
 *
 * Usage (npm):
 *   import { init } from '@emoratest/sdk';
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
import type {
  EmoraTestConfig,
  FlagEvaluationRequest,
  FlagEvaluationResponse,
  FlagEvaluationResult,
} from "./types";
import { sha256, uuid4 } from "./utils";

// Re-export types for consumers
export type {
  EmoraTestConfig,
  RawEvent,
  BatchPayload,
  SessionCreatePayload,
  SessionCreateResponse,
  FlagEvaluationRequest,
  FlagEvaluationResponse,
  FlagEvaluationResult,
} from "./types";

// ── Module state ──────────────────────────────────────────────

let config: EmoraTestConfig | null = null;
let transport: Transport | null = null;
let queue: EventQueue | null = null;
let sessionManager: SessionManager | null = null;
let cleanups: (() => void)[] = [];
let initialized = false;

// ── Feature Flag state ────────────────────────────────────────

const VISITOR_ID_KEY = "emoratest_visitor_id";
let visitorId: string | null = null;
let activeVariants: Record<string, string | null> = {};
const flagCache: Record<string, FlagEvaluationResult> = {};

// ── Public API ────────────────────────────────────────────────

/**
 * Initialize the EmoraTest SDK.
 * Call this once per page load. Starts session tracking and event capture.
 */
export async function init(userConfig: EmoraTestConfig): Promise<void> {
  if (initialized) {
    console.warn("[EmoraTest] Already initialized. Call destroy() first.");
    return;
  }

  if (userConfig.disabled) {
    if (userConfig.debug) console.debug("[EmoraTest] Disabled by config");
    return;
  }

  // Validate
  if (!userConfig.sdkKey) {
    throw new Error("[EmoraTest] sdkKey is required");
  }

  // Store config with resolved defaults
  config = {
    sdkKey: userConfig.sdkKey,
    apiUrl: userConfig.apiUrl ?? "https://emoratest.com",
    flushIntervalMs: userConfig.flushIntervalMs ?? 2000,
    maxBatchSize: userConfig.maxBatchSize ?? 50,
    mouseMoveThrottleMs: userConfig.mouseMoveThrottleMs ?? 100,
    debug: userConfig.debug ?? false,
    disabled: false,
  } as EmoraTestConfig & {
    apiUrl: string;
    flushIntervalMs: number;
    maxBatchSize: number;
    mouseMoveThrottleMs: number;
    debug: boolean;
    disabled: false;
  };

  // Set up components - send RAW SDK key, backend will hash it server-side
  transport = new Transport(config.apiUrl!, config.sdkKey);
  queue = new EventQueue(
    transport,
    config.flushIntervalMs!,
    config.maxBatchSize!,
    config.debug!,
  );
  sessionManager = new SessionManager(transport, config.debug!);

  // Create session — backend uses X-SDK-Key header to find merchant
  const session = await sessionManager.start();
  queue.setSessionId(session.sessionId);
  queue.start();

  // Attach event collectors
  cleanups = [
    collectMouseMove(queue, config.mouseMoveThrottleMs!, getActiveVariants),
    collectClicks(queue, getActiveVariants),
    collectScroll(queue, getActiveVariants),
    collectExitIntent(queue, getActiveVariants),
    collectVisibility(queue, getActiveVariants),
  ];

  // Handle page unload — only flush events, do NOT end session
  // Session persists in sessionStorage for multi-page navigation
  const unloadHandler = () => {
    // Only flush events — do NOT end the session
    // Session persists in sessionStorage for multi-page navigation
    if (queue) {
      queue.flushBeacon();
    }
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
    console.debug("[EmoraTest] Initialized", {
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

// ── Feature Flag Methods ─────────────────────────────────────────

/** Get or create persistent visitor ID (stored in localStorage). */
function getOrCreateVisitorId(): string {
  if (visitorId) return visitorId;

  try {
    const stored = localStorage.getItem(VISITOR_ID_KEY);
    if (stored) {
      visitorId = stored;
      return visitorId;
    }
  } catch {
    // localStorage might be disabled
  }

  const newId = uuid4();
  visitorId = newId;

  try {
    localStorage.setItem(VISITOR_ID_KEY, newId);
  } catch {
    // localStorage might be disabled
  }

  return visitorId;
}

/**
 * Evaluate a feature flag for the current visitor.
 *
 * Uses deterministic hashing so the same visitor always gets the same variant.
 * Results are cached in memory for the session.
 *
 * @param flagKey - The feature flag key to evaluate
 * @returns Promise resolving to { assigned: boolean, variant: string | null }
 */
export async function evaluateFlag(
  flagKey: string,
): Promise<FlagEvaluationResult> {
  if (!initialized || !config) {
    throw new Error("[EmoraTest] SDK not initialized. Call init() first.");
  }

  // Check cache first
  if (flagCache[flagKey]) {
    return flagCache[flagKey];
  }

  const visitorIdValue = getOrCreateVisitorId();
  const sessionId = getSessionId();

  const payload: FlagEvaluationRequest = {
    user_context: {
      visitor_id: visitorIdValue,
      ...(sessionId && { session_id: sessionId }),
    },
    environment: "production",
  };

  try {
    const response = await fetch(`${config.apiUrl}/api/v1/flags/sdk/${flagKey}/evaluate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-SDK-Key": config.sdkKey,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(`[EmoraTest] Flag evaluation failed: ${error.detail || response.statusText}`);
    }

    const data: FlagEvaluationResponse = await response.json();

    // Store in active variants for event metadata
    if (data.enabled && data.variant) {
      activeVariants[flagKey] = data.variant;
    }

    const result: FlagEvaluationResult = {
      assigned: data.enabled,
      variant: data.variant,
    };

    // Cache the result
    flagCache[flagKey] = result;

    if (config.debug) {
      console.debug("[EmoraTest] Flag evaluated", { flagKey, result });
    }

    return result;
  } catch (err) {
    if (config.debug) {
      console.error("[EmoraTest] Flag evaluation error:", err);
    }
    // Return default (not assigned) on error
    return { assigned: false, variant: null };
  }
}

/**
 * Get just the variant for a flag (convenience method).
 * Returns the variant string or null if not assigned.
 *
 * @param flagKey - The feature flag key
 * @returns Variant string or null
 */
export async function getVariant(flagKey: string): Promise<string | null> {
  const result = await evaluateFlag(flagKey);
  return result.variant;
}

/**
 * Get all active variant assignments for this session.
 * Returns format suitable for event metadata.
 */
function getActiveVariants(): Record<string, unknown> | null {
  const variants = Object.entries(activeVariants).filter(([_, v]) => v !== null);
  if (variants.length === 0) return null;
  return { variants: Object.fromEntries(variants) };
}

/** Manually report a conversion outcome. */
export async function reportOutcome(
  outcome: "purchase" | "abandon",
): Promise<void> {
  if (!initialized || !config || !sessionManager) return;

  const sessionId = sessionManager.getSessionId();
  if (!sessionId) return;

  try {
    const response = await fetch(
      `${config.apiUrl}/api/v1/sessions/${sessionId}/outcome`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-SDK-Key": config.sdkKey,
        },
        body: JSON.stringify({ outcome }),
      },
    );
    if (response.ok) {
      // Mark outcome as reported to prevent double-reporting on page unload
      sessionManager.markOutcomeReported();
    }
  } catch (err) {
    if (config.debug) {
      console.error("[EmoraTest] Failed to report outcome:", err);
    }
  }
}
