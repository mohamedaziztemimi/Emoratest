/**
 * Tests for SDK utility functions (CONV-35).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  sha256,
  uuid4,
  isoNow,
  throttle,
  getElementId,
  detectDeviceType,
  detectCountryCode,
} from "../src/utils";

describe("sha256", () => {
  it("returns a 64-character hex string", async () => {
    const hash = await sha256("test-key");
    expect(hash).toMatch(/^[0-9a-f]{64}$/);
  });

  it("produces consistent hashes for the same input", async () => {
    const h1 = await sha256("my-sdk-key");
    const h2 = await sha256("my-sdk-key");
    expect(h1).toBe(h2);
  });

  it("produces different hashes for different inputs", async () => {
    const h1 = await sha256("key-a");
    const h2 = await sha256("key-b");
    expect(h1).not.toBe(h2);
  });
});

describe("uuid4", () => {
  it("returns a valid UUID v4 format", () => {
    const id = uuid4();
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  });

  it("generates unique IDs", () => {
    const ids = new Set(Array.from({ length: 100 }, () => uuid4()));
    expect(ids.size).toBe(100);
  });
});

describe("isoNow", () => {
  it("returns a valid ISO 8601 string", () => {
    const ts = isoNow();
    expect(new Date(ts).toISOString()).toBe(ts);
  });

  it("returns current time within 1 second", () => {
    const ts = isoNow();
    const diff = Math.abs(Date.now() - new Date(ts).getTime());
    expect(diff).toBeLessThan(1000);
  });
});

describe("throttle", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("calls the function immediately on first invocation", () => {
    const fn = vi.fn();
    const throttled = throttle(fn, 100);
    throttled();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("suppresses calls within the throttle window", () => {
    const fn = vi.fn();
    const throttled = throttle(fn, 100);
    throttled();
    throttled();
    throttled();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("fires trailing call after throttle window", () => {
    const fn = vi.fn();
    const throttled = throttle(fn, 100);
    throttled();
    throttled(); // queued
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it("allows calls after the throttle window", () => {
    const fn = vi.fn();
    const throttled = throttle(fn, 100);
    throttled();
    vi.advanceTimersByTime(101);
    throttled();
    expect(fn).toHaveBeenCalledTimes(2);
  });
});

describe("getElementId", () => {
  it("returns null for null element", () => {
    expect(getElementId(null)).toBeNull();
  });

  it("returns #id for elements with id", () => {
    const el = document.createElement("button");
    el.id = "submit-btn";
    expect(getElementId(el)).toBe("#submit-btn");
  });

  it("returns tag[name=...] for named inputs", () => {
    const el = document.createElement("input");
    el.name = "email";
    expect(getElementId(el)).toBe('input[name="email"]');
  });

  it("returns tag.class for elements with classes", () => {
    const el = document.createElement("div");
    el.classList.add("card", "primary");
    expect(getElementId(el)).toBe("div.card.primary");
  });

  it("returns just the tag for plain elements", () => {
    const el = document.createElement("span");
    expect(getElementId(el)).toBe("span");
  });
});

describe("detectDeviceType", () => {
  it("returns 'desktop' for standard user agent", () => {
    // happy-dom default UA is desktop-like
    expect(detectDeviceType()).toBe("desktop");
  });
});

describe("detectCountryCode", () => {
  it("returns a string or null", () => {
    const result = detectCountryCode();
    expect(result === null || typeof result === "string").toBe(true);
  });
});
