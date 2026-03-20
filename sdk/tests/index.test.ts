/**
 * Tests for SDK main entry point (CONV-35).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { init, destroy, getSessionId, isInitialized } from "../src/index";

// Mock fetch globally
const mockFetch = vi.fn().mockResolvedValue(
  new Response(JSON.stringify({ session_id: "test-session" }), { status: 200 }),
);

describe("SDK init/destroy lifecycle", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
    vi.stubGlobal("navigator", {
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
      sendBeacon: vi.fn().mockReturnValue(true),
    });
    mockFetch.mockClear();
  });

  afterEach(async () => {
    await destroy();
    vi.restoreAllMocks();
  });

  it("initializes successfully with valid config", async () => {
    await init({ sdkKey: "test-key", apiUrl: "https://api.test.com" });

    expect(isInitialized()).toBe(true);
    expect(getSessionId()).toBeDefined();
  });

  it("warns on double initialization", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    await init({ sdkKey: "test-key", apiUrl: "https://api.test.com" });
    await init({ sdkKey: "test-key", apiUrl: "https://api.test.com" });

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining("Already initialized"),
    );
  });

  it("does nothing when disabled", async () => {
    await init({ sdkKey: "test-key", disabled: true });

    expect(isInitialized()).toBe(false);
  });

  it("throws without sdkKey", async () => {
    await expect(init({ sdkKey: "" })).rejects.toThrow("sdkKey is required");
  });

  it("destroys cleanly", async () => {
    await init({ sdkKey: "test-key", apiUrl: "https://api.test.com" });
    await destroy();

    expect(isInitialized()).toBe(false);
    expect(getSessionId()).toBeNull();
  });

  it("destroy is safe to call when not initialized", async () => {
    await expect(destroy()).resolves.toBeUndefined();
  });

  it("getSessionId returns null before init", () => {
    expect(getSessionId()).toBeNull();
  });
});
