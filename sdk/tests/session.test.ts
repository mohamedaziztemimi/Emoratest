/**
 * Tests for SessionManager (CONV-35).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { SessionManager } from "../src/session";
import type { Transport } from "../src/transport";

function createMockTransport(): Transport {
  return {
    createSession: vi.fn().mockResolvedValue({ session_id: "server-sess-id" }),
    sendEvents: vi.fn(),
    endSession: vi.fn().mockResolvedValue(undefined),
    sendBeacon: vi.fn(),
    sendBeaconEnd: vi.fn().mockReturnValue(true),
  } as unknown as Transport;
}

describe("SessionManager", () => {
  let transport: ReturnType<typeof createMockTransport>;
  let manager: SessionManager;

  beforeEach(() => {
    transport = createMockTransport();
    manager = new SessionManager(transport, false);
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  describe("start", () => {
    it("creates a new session and calls transport", async () => {
      const session = await manager.start("merchant-1");

      expect(session.sessionId).toBeDefined();
      expect(session.merchantId).toBe("merchant-1");
      expect(session.startedAt).toBeDefined();
      expect(transport.createSession).toHaveBeenCalledWith(
        expect.objectContaining({
          merchant_id: "merchant-1",
          page_url: expect.any(String),
          started_at: expect.any(String),
        }),
      );
    });

    it("saves session to sessionStorage", async () => {
      await manager.start("merchant-1");

      const stored = sessionStorage.getItem("__emoratest_session");
      expect(stored).not.toBeNull();
      const parsed = JSON.parse(stored!);
      expect(parsed.merchantId).toBe("merchant-1");
    });

    it("resumes existing session from sessionStorage", async () => {
      const existingSession = {
        sessionId: "existing-id",
        merchantId: "merchant-1",
        startedAt: "2026-01-01T00:00:00.000Z",
      };
      sessionStorage.setItem(
        "__emoratest_session",
        JSON.stringify(existingSession),
      );

      const session = await manager.start("merchant-1");

      expect(session.sessionId).toBe("existing-id");
      // Should NOT call transport for resumed session
      expect(transport.createSession).not.toHaveBeenCalled();
    });

    it("creates new session if stored session has different merchantId", async () => {
      const existingSession = {
        sessionId: "old-id",
        merchantId: "other-merchant",
        startedAt: "2026-01-01T00:00:00.000Z",
      };
      sessionStorage.setItem(
        "__emoratest_session",
        JSON.stringify(existingSession),
      );

      const session = await manager.start("merchant-1");

      expect(session.sessionId).not.toBe("old-id");
      expect(transport.createSession).toHaveBeenCalled();
    });

    it("still creates local session if transport fails", async () => {
      (transport.createSession as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("Network error"),
      );

      const session = await manager.start("merchant-1");

      expect(session.sessionId).toBeDefined();
      expect(session.merchantId).toBe("merchant-1");
    });
  });

  describe("end", () => {
    it("calls transport.endSession", async () => {
      await manager.start("merchant-1");
      const sid = manager.getSessionId();

      await manager.end();

      expect(transport.endSession).toHaveBeenCalledWith(sid);
    });

    it("clears sessionStorage", async () => {
      await manager.start("merchant-1");
      await manager.end();

      expect(sessionStorage.getItem("__emoratest_session")).toBeNull();
    });

    it("nulls the session", async () => {
      await manager.start("merchant-1");
      await manager.end();
      expect(manager.getSessionId()).toBeNull();
    });

    it("does nothing if no session exists", async () => {
      await manager.end();
      expect(transport.endSession).not.toHaveBeenCalled();
    });

    it("falls back to beacon if endSession fails", async () => {
      await manager.start("merchant-1");
      (transport.endSession as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("fail"),
      );

      await manager.end();

      expect(transport.sendBeaconEnd).toHaveBeenCalled();
    });
  });

  describe("endBeacon", () => {
    it("sends beacon end and clears session", async () => {
      await manager.start("merchant-1");
      const sid = manager.getSessionId();

      manager.endBeacon();

      expect(transport.sendBeaconEnd).toHaveBeenCalledWith(sid);
      expect(manager.getSessionId()).toBeNull();
    });
  });

  describe("getSessionId", () => {
    it("returns null before start", () => {
      expect(manager.getSessionId()).toBeNull();
    });

    it("returns session ID after start", async () => {
      await manager.start("merchant-1");
      expect(manager.getSessionId()).toBeDefined();
    });
  });
});
