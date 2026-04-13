/**
 * Tests for SDK Transport layer (CONV-35).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { Transport } from "../src/transport";

describe("Transport", () => {
  let transport: Transport;
  const API_URL = "https://api.emoratest.com";
  const SDK_KEY_HASH = "abc123hash";

  beforeEach(() => {
    transport = new Transport(API_URL, SDK_KEY_HASH);
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("createSession", () => {
    it("sends POST to /api/v1/sessions with correct headers", async () => {
      const mockResponse = { session_id: "test-session-id" };
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockResponse), { status: 200 }),
      );

      const result = await transport.createSession({
        merchant_id: "m-1",
        page_url: "https://shop.com/cart",
        started_at: "2026-01-01T00:00:00.000Z",
        country_code: "US",
        device_type: "desktop",
      });

      expect(fetchSpy).toHaveBeenCalledWith(
        `${API_URL}/api/v1/sessions`,
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-SDK-Key": SDK_KEY_HASH,
          },
        }),
      );
      expect(result.session_id).toBe("test-session-id");
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Unauthorized", { status: 401, statusText: "Unauthorized" }),
      );

      await expect(
        transport.createSession({
          merchant_id: "m-1",
          page_url: "https://shop.com",
          started_at: "2026-01-01T00:00:00.000Z",
        }),
      ).rejects.toThrow("Session create failed: 401");
    });
  });

  describe("sendEvents", () => {
    it("sends POST to /api/v1/events/batch", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ status: "ok", count: 1 }), { status: 200 }),
      );

      await transport.sendEvents({
        session_id: "sess-1",
        events: [
          {
            type: "click",
            ts: "2026-01-01T00:00:00.000Z",
            x: 100,
            y: 200,
          },
        ],
      });

      expect(fetchSpy).toHaveBeenCalledWith(
        `${API_URL}/api/v1/events/batch`,
        expect.objectContaining({ method: "POST" }),
      );
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Error", { status: 500, statusText: "Server Error" }),
      );

      await expect(
        transport.sendEvents({
          session_id: "sess-1",
          events: [{ type: "click", ts: "2026-01-01T00:00:00.000Z" }],
        }),
      ).rejects.toThrow("Event batch failed: 500");
    });
  });

  describe("endSession", () => {
    it("sends PUT to /api/v1/sessions/:id/end", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ status: "ended" }), { status: 200 }),
      );

      await transport.endSession("sess-1");

      expect(fetchSpy).toHaveBeenCalledWith(
        `${API_URL}/api/v1/sessions/sess-1/end`,
        expect.objectContaining({ method: "PUT" }),
      );
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Not found", { status: 404, statusText: "Not Found" }),
      );

      await expect(transport.endSession("bad-id")).rejects.toThrow(
        "Session end failed: 404",
      );
    });
  });

  describe("sendBeacon", () => {
    it("sends a beacon with JSON blob", () => {
      const beaconSpy = vi.fn().mockReturnValue(true);
      vi.stubGlobal("navigator", { sendBeacon: beaconSpy });

      const result = transport.sendBeacon({
        session_id: "sess-1",
        events: [{ type: "click", ts: "2026-01-01T00:00:00.000Z" }],
      });

      expect(result).toBe(true);
      expect(beaconSpy).toHaveBeenCalledWith(
        `${API_URL}/api/v1/events/batch?sdk_key=${SDK_KEY_HASH}`,
        expect.any(Blob),
      );
    });

    it("returns false if sendBeacon is unavailable", () => {
      vi.stubGlobal("navigator", {});
      const result = transport.sendBeacon({
        session_id: "sess-1",
        events: [],
      });
      expect(result).toBe(false);
    });
  });

  describe("sendBeaconEnd", () => {
    it("sends a beacon to end session", () => {
      const beaconSpy = vi.fn().mockReturnValue(true);
      vi.stubGlobal("navigator", { sendBeacon: beaconSpy });

      const result = transport.sendBeaconEnd("sess-1");

      expect(result).toBe(true);
      expect(beaconSpy).toHaveBeenCalledWith(
        `${API_URL}/api/v1/sessions/sess-1/end?sdk_key=${SDK_KEY_HASH}`,
        expect.any(Blob),
      );
    });
  });

  describe("URL normalization", () => {
    it("strips trailing slashes from API URL", async () => {
      const t = new Transport("https://api.com///", SDK_KEY_HASH);
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ session_id: "s1" }), { status: 200 }),
      );

      await t.createSession({
        merchant_id: "m",
        page_url: "https://shop.com",
        started_at: "2026-01-01T00:00:00.000Z",
      });

      expect(fetchSpy).toHaveBeenCalledWith(
        "https://api.com/api/v1/sessions",
        expect.anything(),
      );
    });
  });
});
