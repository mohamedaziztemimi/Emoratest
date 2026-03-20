/**
 * Utility functions for the Conversiono SDK.
 */

/**
 * SHA-256 hash using Web Crypto API (available in all modern browsers).
 * Falls back to a simple hash if crypto.subtle is unavailable (e.g., HTTP).
 */
export async function sha256(message: string): Promise<string> {
  if (typeof crypto !== "undefined" && crypto.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(message);
    const hash = await crypto.subtle.digest("SHA-256", data);
    return Array.from(new Uint8Array(hash))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }
  // Fallback: simple djb2-based hash (NOT cryptographic, for non-HTTPS dev only)
  let h = 5381;
  for (let i = 0; i < message.length; i++) {
    h = ((h << 5) + h + message.charCodeAt(i)) >>> 0;
  }
  return h.toString(16).padStart(64, "0");
}

/** Generate a UUID v4. */
export function uuid4(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/** ISO 8601 timestamp with milliseconds. */
export function isoNow(): string {
  return new Date().toISOString();
}

/** Throttle a function to fire at most once every `ms` milliseconds. */
export function throttle<T extends (...args: unknown[]) => void>(
  fn: T,
  ms: number,
): T {
  let last = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;

  return function (this: unknown, ...args: unknown[]) {
    const now = Date.now();
    const remaining = ms - (now - last);

    if (remaining <= 0) {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      last = now;
      fn.apply(this, args);
    } else if (!timer) {
      timer = setTimeout(() => {
        last = Date.now();
        timer = null;
        fn.apply(this, args);
      }, remaining);
    }
  } as T;
}

/** Get a short CSS-like selector for an element. */
export function getElementId(el: Element | null): string | null {
  if (!el || !el.tagName) return null;
  if (el.id) return `#${el.id}`;

  const tag = el.tagName.toLowerCase();
  const classes = Array.from(el.classList).slice(0, 3).join(".");
  const name = (el as HTMLInputElement).name;

  if (name) return `${tag}[name="${name}"]`;
  if (classes) return `${tag}.${classes}`;
  return tag;
}

/** Detect device type from user agent. */
export function detectDeviceType(): "desktop" | "mobile" | "tablet" {
  const ua = navigator.userAgent.toLowerCase();
  if (/tablet|ipad|playbook|silk/.test(ua)) return "tablet";
  if (/mobile|iphone|ipod|android.*mobile|opera m(ob|in)i/.test(ua))
    return "mobile";
  return "desktop";
}

/** Attempt to get country code from Intl API (best-effort). */
export function detectCountryCode(): string | null {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    // Common timezone → country mappings
    const map: Record<string, string> = {
      "America/New_York": "US",
      "America/Chicago": "US",
      "America/Los_Angeles": "US",
      "Europe/London": "GB",
      "Europe/Paris": "FR",
      "Europe/Berlin": "DE",
      "Asia/Tokyo": "JP",
      "Australia/Sydney": "AU",
      "America/Toronto": "CA",
    };
    return map[tz] ?? null;
  } catch {
    return null;
  }
}
