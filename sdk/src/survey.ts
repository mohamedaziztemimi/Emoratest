/**
 * Micro-survey widget for collecting direct user emotion feedback.
 *
 * Shows a small, non-intrusive widget asking users to rate their experience.
 * Results are sent to the backend for analysis and ML model training.
 */

import { getSessionId } from "./index";

export type SurveyTrigger = "exit_intent" | "scroll_75" | "time_30s";
export type SurveyPosition = "bottom-right" | "bottom-left";
export type FeedbackRating = "negative" | "neutral" | "positive";

export interface SurveyConfig {
  /** When to show the survey */
  trigger: SurveyTrigger;
  /** Only show on these page paths (empty = all pages) */
  pageFilter: string[];
  /** What % of sessions see the survey (0-1) */
  sampleRate: number;
  /** Widget position on screen */
  position: SurveyPosition;
}

export interface FeedbackPayload {
  rating: FeedbackRating;
  page_url: string;
}

// ── Widget styling (inline to avoid external CSS dependencies) ─────

const WIDGET_STYLES = `
  position: fixed;
  z-index: 2147483647;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: opacity 0.3s ease, transform 0.3s ease;
`;

const BUTTON_STYLES = `
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 24px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  background: #f5f5f5;
`;

const BUTTON_HOVER_STYLES = `
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
`;

// ── State ─────────────────────────────────────────────────────────

let surveyConfig: SurveyConfig | null = null;
let widgetShown = false;
let widgetElement: HTMLDivElement | null = null;
let cleanupTrigger: (() => void) | null = null;
let apiUrl = "";
let sdkKey = "";

// ── Public API ─────────────────────────────────────────────────────

/**
 * Initialize the micro-survey with the given configuration.
 * Call this after SDK init() if survey config is provided.
 */
export function initSurvey(config: SurveyConfig, apiBaseUrl: string, key: string): void {
  surveyConfig = config;
  apiUrl = apiBaseUrl;
  sdkKey = key;

  // Check sampling rate
  if (Math.random() > config.sampleRate) {
    return; // Not in sample
  }

  // Check page filter
  if (config.pageFilter.length > 0) {
    const currentPath = window.location.pathname;
    if (!config.pageFilter.some(path => currentPath.includes(path))) {
      return; // Not on filtered page
    }
  }

  // Set up trigger based on configuration
  setupTrigger(config.trigger);
}

/**
 * Show the micro-survey widget immediately.
 * Can be called manually for custom trigger logic.
 */
export function showMicroSurvey(): void {
  if (widgetShown || !surveyConfig) return;

  const widget = createWidget();
  document.body.appendChild(widget);
  widgetElement = widget;
  widgetShown = true;

  // Animate in
  requestAnimationFrame(() => {
    const position = surveyConfig!.position;
    const startX = position === "bottom-right" ? "20px" : "-20px";
    widget.style.transform = `translateX(${startX})`;
    widget.style.opacity = "0";

    requestAnimationFrame(() => {
      widget.style.transform = "translateX(0)";
      widget.style.opacity = "1";
    });
  });
}

// ── Internal functions ───────────────────────────────────────────────

function createWidget(): HTMLDivElement {
  const container = document.createElement("div");
  container.id = "emoratest-survey-widget";

  // Position based on config
  const positionStyles =
    surveyConfig?.position === "bottom-left"
      ? "bottom: 20px; left: 20px;"
      : "bottom: 20px; right: 20px;";

  container.setAttribute(
    "style",
    WIDGET_STYLES + positionStyles + "max-width: 280px;"
  );

  // Question text
  const question = document.createElement("div");
  question.textContent = "How was your experience on this page?";
  question.setAttribute(
    "style",
    "font-size: 14px; font-weight: 600; color: #111; margin-bottom: 12px; text-align: center;"
  );
  container.appendChild(question);

  // Emoji buttons container
  const buttonContainer = document.createElement("div");
  buttonContainer.setAttribute(
    "style",
    "display: flex; gap: 12px; justify-content: center;"
  );
  container.appendChild(buttonContainer);

  // Create emoji buttons
  const emojis = [
    { emoji: "😟", rating: "negative" as FeedbackRating },
    { emoji: "😐", rating: "neutral" as FeedbackRating },
    { emoji: "😊", rating: "positive" as FeedbackRating },
  ];

  emojis.forEach(({ emoji, rating }) => {
    const button = document.createElement("button");
    button.textContent = emoji;
    button.setAttribute("style", BUTTON_STYLES);
    button.setAttribute("aria-label", rating);

    // Hover effects
    button.addEventListener("mouseenter", () => {
      button.setAttribute("style", BUTTON_STYLES + BUTTON_HOVER_STYLES);
    });
    button.addEventListener("mouseleave", () => {
      button.setAttribute("style", BUTTON_STYLES);
    });

    // Click handler
    button.addEventListener("click", () => handleFeedback(rating));

    buttonContainer.appendChild(button);
  });

  // Close button
  const closeBtn = document.createElement("button");
  closeBtn.innerHTML = "&times;";
  closeBtn.setAttribute(
    "style",
    "position: absolute; top: 8px; right: 8px; width: 24px; height: 24px; border: none; background: transparent; cursor: pointer; font-size: 18px; color: #999; padding: 0;"
  );
  closeBtn.addEventListener("click", hideWidget);
  container.appendChild(closeBtn);

  return container;
}

function handleFeedback(rating: FeedbackRating): void {
  // Send feedback to backend
  sendFeedback(rating);

  // Show thanks message
  if (widgetElement) {
    const container = widgetElement;
    container.innerHTML = "";

    const thanks = document.createElement("div");
    thanks.textContent = "Thanks!";
    thanks.setAttribute(
      "style",
      "font-size: 14px; font-weight: 600; color: #10B981; text-align: center; padding: 8px;"
    );
    container.appendChild(thanks);
  }

  // Hide after delay
  setTimeout(hideWidget, 1500);
}

async function sendFeedback(rating: FeedbackRating): Promise<void> {
  const sessionId = getSessionId();
  if (!sessionId) return;

  const payload: FeedbackPayload = {
    rating,
    page_url: window.location.href,
  };

  try {
    await fetch(`${apiUrl}/api/v1/sessions/${sessionId}/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-SDK-Key": sdkKey,
      },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    // Silent fail - don't disrupt user experience
    console.error("[EmoraTest] Failed to send feedback:", err);
  }
}

function hideWidget(): void {
  if (!widgetElement) return;

  const position = surveyConfig?.position === "bottom-left" ? "-20px" : "20px";
  widgetElement.style.transform = `translateX(${position})`;
  widgetElement.style.opacity = "0";

  setTimeout(() => {
    widgetElement?.remove();
    widgetElement = null;
    widgetShown = false;
  }, 300);
}

function setupTrigger(trigger: SurveyTrigger): void {
  // Remove existing trigger if any
  if (cleanupTrigger) {
    cleanupTrigger();
    cleanupTrigger = null;
  }

  switch (trigger) {
    case "exit_intent":
      setupExitIntentTrigger();
      break;
    case "scroll_75":
      setupScrollTrigger();
      break;
    case "time_30s":
      setupTimeTrigger();
      break;
  }
}

function setupExitIntentTrigger(): void {
  const handler = (e: MouseEvent) => {
    // Show when mouse leaves viewport from top
    if (e.clientY <= 0 && !widgetShown) {
      showMicroSurvey();
    }
  };

  document.addEventListener("mouseout", handler);
  cleanupTrigger = () => document.removeEventListener("mouseout", handler);
}

function setupScrollTrigger(): void {
  let triggered = false;

  const handler = () => {
    if (triggered || widgetShown) return;

    const scrollPct =
      (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;

    if (scrollPct >= 75) {
      triggered = true;
      showMicroSurvey();
    }
  };

  window.addEventListener("scroll", handler, { passive: true });
  cleanupTrigger = () => window.removeEventListener("scroll", handler);
}

function setupTimeTrigger(): void {
  const timeoutId = setTimeout(() => {
    if (!widgetShown) {
      showMicroSurvey();
    }
  }, 30000); // 30 seconds

  cleanupTrigger = () => clearTimeout(timeoutId);
}
