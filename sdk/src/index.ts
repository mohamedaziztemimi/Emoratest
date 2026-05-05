/**
 * EmoraTest SDK — main entry point.
 *
 * Quick Start (script tag):
 *   <script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
 *   <script>
 *     EmoraTest.init({ sdkKey: 'your-key-here' });
 *   </script>
 *
 * GDPR/Consent Mode (EU users):
 *   <script src="https://emoratest.com/static/sdk/emoratest.umd.js"></script>
 *   <script>
 *     EmoraTest.init({ sdkKey: 'your-key-here', requireConsent: true });
 *     // Later, when user accepts:
 *     // document.cookie = 'emoratest_consent=accepted; max-age=31536000; path=/';
 *     // EmoraTest.enableTracking();
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
import { initSurvey } from "./survey";
import { EventQueue } from "./event-queue";
import { SessionManager } from "./session";
import { Transport } from "./transport";
import type { SurveyTrigger, SurveyPosition } from "./survey";
import type {
  EmoraTestConfig,
  FlagEvaluationRequest,
  FlagEvaluationResponse,
  FlagEvaluationResult,
  OutcomeType,
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
  OutcomeType,
} from "./types";

// ── Module state ──────────────────────────────────────────────

let config: EmoraTestConfig | null = null;
let transport: Transport | null = null;
let queue: EventQueue | null = null;
let sessionManager: SessionManager | null = null;
let cleanups: (() => void)[] = [];
let initialized = false;
let pendingInit: EmoraTestConfig | null = null; // Store config when waiting for consent
let consentGiven = false;

// ── Feature Flag state ────────────────────────────────────────

const VISITOR_ID_KEY = "emoratest_visitor_id";
let visitorId: string | null = null;
let activeVariants: Record<string, string | null> = {};
const flagCache: Record<string, FlagEvaluationResult> = {};

// ── Auto-detection based on URL patterns ────────────────────────

/** Auto-detect outcome from URL patterns. Call this after init() or it runs automatically. */
export function detectOutcomeFromUrl(): void {
  if (!initialized || !sessionManager) return;

  const url = window.location.href.toLowerCase();
  const pathname = window.location.pathname.toLowerCase();
  const searchParams = new URLSearchParams(window.location.search.toLowerCase());

  // Define pattern → outcome mappings (expanded for e-commerce)
  const patterns: Array<{ pattern: RegExp; outcome: OutcomeType; description: string }> = [
    // Purchase/Order completion (expanded patterns)
    {
      pattern: /\/success|\/thank-?you|\/confirmation|\/complete|\/order-confirmation/i,
      outcome: "purchase",
      description: "purchase confirmation page"
    },
    {
      pattern: /\/order\/success|\/order\/confirm|\/order\/confirmed|\/order\/complete/i,
      outcome: "purchase",
      description: "order success page"
    },
    {
      pattern: /\/checkout\/success|\/checkout\/complete|\/checkout\/thank/i,
      outcome: "purchase",
      description: "checkout success page"
    },
    {
      pattern: /\/cart\/success|\/cart\/complete|\/cart\/thank/i,
      outcome: "purchase",
      description: "cart success page"
    },
    {
      pattern: /\/payment\/success|\/payment\/complete|\/payment\/confirmed/i,
      outcome: "purchase",
      description: "payment success page"
    },
    // International patterns
    { pattern: /\/merci|\/danke|\/gracias|\/grazie|\/obrigado/i, outcome: "purchase", description: "international thank you" },

    // Signup
    { pattern: /\/signup\/success|\/registered|\/sign-?up\/success|\/signup\/complete/i, outcome: "signup", description: "signup success" },

    // Checkout completed (for multi-step checkouts)
    {
      pattern: /\/checkout\/success|\/checkout\/complete|\/order\/confirm/i,
      outcome: "checkout_completed",
      description: "checkout completed"
    },

    // Demo booked
    { pattern: /\/demo\/booked|\/demo\/confirm|\/meeting\/scheduled/i, outcome: "demo_booked", description: "demo booked" },

    // Lead generated
    { pattern: /\/lead\/success|\/submitted|\/form\/success/i, outcome: "lead_generated", description: "lead form submitted" },

    // Trial started
    { pattern: /\/trial\/started|\/subscribed|\/welcome/i, outcome: "trial_started", description: "trial started" },
  ];

  // Check each pattern
  for (const { pattern, outcome, description } of patterns) {
    if (pattern.test(url) || pattern.test(pathname)) {
      reportOutcome(outcome);
      if (config?.debug) {
        console.debug(`[EmoraTest] Auto-detected outcome: ${outcome} (${description})`);
        console.debug(`[EmoraTest] URL checked: ${pathname}`);
      }
      return;
    }
  }

  // Check query parameters for success indicators
  const successParams = ["order=confirmed", "status=success", "payment=complete", "checkout=complete", "order=success"];
  for (const param of successParams) {
    if (url.includes(`?${param}`) || url.includes(`&${param}`)) {
      reportOutcome("purchase");
      if (config?.debug) {
        console.debug(`[EmoraTest] Auto-detected outcome: purchase (query param: ${param})`);
        console.debug(`[EmoraTest] URL checked: ${url}`);
      }
      return;
    }
  }

  if (config?.debug) {
    console.debug(`[EmoraTest] No outcome pattern matched for URL: ${pathname}`);
  }
}

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

  // Consent mode: if requireConsent is true, wait for consent before tracking
  // Otherwise, start tracking immediately (default behavior)
  const requireConsent = userConfig.requireConsent === true;
  const consentCookie = getConsentCookie();

  if (requireConsent && consentCookie !== "accepted") {
    // Consent not given - store config and wait for enableTracking()
    pendingInit = userConfig;
    if (userConfig.debug) {
      console.debug("[EmoraTest] requireConsent enabled. Waiting for user consent. Call enableTracking() after consent.");
    }
    return;
  }

  consentGiven = true;

  // Store config with resolved defaults
  config = {
    sdkKey: userConfig.sdkKey,
    apiUrl: userConfig.apiUrl ?? "https://emoratest.com",
    flushIntervalMs: userConfig.flushIntervalMs ?? 2000,
    maxBatchSize: userConfig.maxBatchSize ?? 50,
    mouseMoveThrottleMs: userConfig.mouseMoveThrottleMs ?? 100,
    debug: userConfig.debug ?? false,
    disabled: false,
    samplingRate: userConfig.samplingRate ?? 1.0,  // Default to 100% tracking
    environment: userConfig.environment ?? "production",  // Default to production
  } as EmoraTestConfig & {
    apiUrl: string;
    flushIntervalMs: number;
    maxBatchSize: number;
    mouseMoveThrottleMs: number;
    debug: boolean;
    disabled: false;
    samplingRate: number;
    environment: "test" | "production";
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
  // Pass sampling rate and environment from config
  const session = await sessionManager.start(config.samplingRate!, config.environment!);
  queue.setSessionId(session.sessionId);
  // Store device/country context for session auto-creation fallback
  queue.setDeviceType(sessionManager.getDeviceType());
  queue.setCountryCode(sessionManager.getCountryCode());
  queue.start();

  // Initialize micro-survey if backend config says it's enabled
  if (session.fullResponse?.survey?.enabled) {
    const surveyCfg = session.fullResponse.survey;
    // Convert backend format to SDK format
    const surveyConfig = {
      trigger: (surveyCfg.trigger || "exit_intent") as SurveyTrigger,
      pageFilter: surveyCfg.pages || [],
      sampleRate: surveyCfg.sample_rate ?? 0.1,
      position: "bottom-right" as SurveyPosition,
    };
    initSurvey(surveyConfig, config.apiUrl!, config.sdkKey);
  }

  // Attach event collectors
  cleanups = [
    collectMouseMove(queue, config.mouseMoveThrottleMs!, getActiveVariants),
    collectClicks(queue, getActiveVariants),
    collectScroll(queue, getActiveVariants),
    collectExitIntent(queue, getActiveVariants),
    collectVisibility(queue, getActiveVariants),
  ];

  // Handle page unload — close session and flush events
  // For single-page apps, the session closes. For multi-page, it persists.
  const unloadHandler = () => {
    // Flush events
    if (queue) {
      queue.flushBeacon();
    }
    // Close session via beacon (marks as abandon if no outcome set)
    if (sessionManager) {
      sessionManager.endBeacon();
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

  // Auto-detect outcome based on URL patterns
  detectOutcomeFromUrl?.();
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

/** Check if the monthly session limit has been reached. */
export function isLimitReached(): boolean {
  return transport?.limitReached ?? false;
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
  outcome: OutcomeType,
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

/** Get consent cookie value for GDPR compliance. */
function getConsentCookie(): "accepted" | "rejected" | null {
  if (typeof document === "undefined") return null;

  const cookies = document.cookie.split(";").map((c) => c.trim());
  const consentCookie = cookies.find((c) => c.startsWith("emoratest_consent="));
  if (!consentCookie) return null;

  const value = consentCookie.split("=")[1];
  if (value === "accepted" || value === "rejected") {
    return value;
  }
  return null;
}

/**
 * Enable tracking after user consent is given.
 * Call this after setting the emoratest_consent cookie to 'accepted'.
 * Only works when requireConsent: true was passed to init().
 */
export async function enableTracking(): Promise<void> {
  if (initialized) {
    console.warn("[EmoraTest] Already initialized. Call destroy() first.");
    return;
  }

  if (!pendingInit) {
    console.warn("[EmoraTest] No pending initialization. Call init() first with requireConsent: true.");
    return;
  }

  const userConfig = pendingInit;
  pendingInit = null;

  // Verify consent was given
  const consentCookie = getConsentCookie();
  if (consentCookie !== "accepted") {
    console.warn("[EmoraTest] Consent not accepted. Cannot enable tracking. Set emoratest_consent=accepted cookie first.");
    return;
  }

  consentGiven = true;

  // Store config with resolved defaults
  config = {
    sdkKey: userConfig.sdkKey,
    apiUrl: userConfig.apiUrl ?? "https://emoratest.com",
    flushIntervalMs: userConfig.flushIntervalMs ?? 2000,
    maxBatchSize: userConfig.maxBatchSize ?? 50,
    mouseMoveThrottleMs: userConfig.mouseMoveThrottleMs ?? 100,
    debug: userConfig.debug ?? false,
    disabled: false,
    samplingRate: userConfig.samplingRate ?? 1.0,  // Default to 100% tracking
    environment: userConfig.environment ?? "production",  // Default to production
  } as EmoraTestConfig & {
    apiUrl: string;
    flushIntervalMs: number;
    maxBatchSize: number;
    mouseMoveThrottleMs: number;
    debug: boolean;
    disabled: false;
    samplingRate: number;
    environment: "test" | "production";
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
  // Pass sampling rate and environment from config
  const session = await sessionManager.start(config.samplingRate!, config.environment!);
  queue.setSessionId(session.sessionId);
  // Store device/country context for session auto-creation fallback
  queue.setDeviceType(sessionManager.getDeviceType());
  queue.setCountryCode(sessionManager.getCountryCode());
  queue.start();

  // Initialize micro-survey if backend config says it's enabled
  if (session.fullResponse?.survey?.enabled) {
    const surveyCfg = session.fullResponse.survey;
    // Convert backend format to SDK format
    const surveyConfig = {
      trigger: (surveyCfg.trigger || "exit_intent") as SurveyTrigger,
      pageFilter: surveyCfg.pages || [],
      sampleRate: surveyCfg.sample_rate ?? 0.1,
      position: "bottom-right" as SurveyPosition,
    };
    initSurvey(surveyConfig, config.apiUrl!, config.sdkKey);
  }

  // Attach event collectors
  cleanups = [
    collectMouseMove(queue, config.mouseMoveThrottleMs!, getActiveVariants),
    collectClicks(queue, getActiveVariants),
    collectScroll(queue, getActiveVariants),
    collectExitIntent(queue, getActiveVariants),
    collectVisibility(queue, getActiveVariants),
  ];

  // Handle page unload — close session and flush events
  const unloadHandler = () => {
    if (queue) {
      queue.flushBeacon();
    }
    if (sessionManager) {
      sessionManager.endBeacon();
    }
  };

  window.addEventListener("beforeunload", unloadHandler);
  cleanups.push(() =>
    window.removeEventListener("beforeunload", unloadHandler),
  );

  // Handle page visibility for mobile
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
    console.debug("[EmoraTest] Initialized after consent", {
      sessionId: session.sessionId,
      apiUrl: config.apiUrl,
    });
  }

  // Auto-detect outcome based on URL patterns
  detectOutcomeFromUrl?.();
}
