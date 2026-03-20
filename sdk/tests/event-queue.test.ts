/**
 * Tests for EventQueue (CONV-35).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { EventQueue } from "../src/event-queue";
import type { Transport } from "../src/transport";
import type { RawEvent } from "../src/types";

function createMockTransport(): Transport {
  return {
    createSession: vi.fn(),
    sendEvents: vi.fn().mockResolvedValue(undefined),
    endSession: vi.fn(),
    sendBeacon: vi.fn().mockReturnValue(true),
    sendBeaconEnd: vi.fn(),
  } as unknown as Transport;
}

function makeEvent(type: RawEvent["type"] = "click"): RawEvent {
  return { type, ts: "2026-01-01T00:00:00.000Z", x: 10, y: 20 };
}

describe("EventQueue", () => {
  let transport: ReturnType<typeof createMockTransport>;
  let queue: EventQueue;

  beforeEach(() => {
    vi.useFakeTimers();
    transport = createMockTransport();
    queue = new EventQueue(transport, 2000, 5, false);
  });

  afterEach(() => {
    queue.stop();
    vi.useRealTimers();
  });

  describe("push", () => {
    it("adds events to the queue", () => {
      queue.setSessionId("sess-1");
      queue.push(makeEvent());
      expect(queue.size).toBe(1);
    });

    it("triggers flush when maxBatchSize is reached", async () => {
      queue.setSessionId("sess-1");
      for (let i = 0; i < 5; i++) {
        queue.push(makeEvent());
      }
      // Flush is async, give it a tick
      await vi.advanceTimersByTimeAsync(0);
      expect(transport.sendEvents).toHaveBeenCalledTimes(1);
      expect(queue.size).toBe(0);
    });
  });

  describe("flush", () => {
    it("sends events to transport", async () => {
      queue.setSessionId("sess-1");
      queue.push(makeEvent("click"));
      queue.push(makeEvent("scroll"));

      await queue.flush();

      expect(transport.sendEvents).toHaveBeenCalledWith({
        session_id: "sess-1",
        events: expect.arrayContaining([
          expect.objectContaining({ type: "click" }),
          expect.objectContaining({ type: "scroll" }),
        ]),
      });
      expect(queue.size).toBe(0);
    });

    it("does nothing when queue is empty", async () => {
      queue.setSessionId("sess-1");
      await queue.flush();
      expect(transport.sendEvents).not.toHaveBeenCalled();
    });

    it("does nothing when sessionId is not set", async () => {
      queue.push(makeEvent());
      await queue.flush();
      expect(transport.sendEvents).not.toHaveBeenCalled();
    });

    it("re-queues events on transport failure", async () => {
      (transport.sendEvents as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("Network error"),
      );
      queue.setSessionId("sess-1");
      queue.push(makeEvent());
      queue.push(makeEvent());

      await queue.flush();

      // Events should be back in the queue
      expect(queue.size).toBe(2);
    });

    it("flushes at most maxBatchSize events per call", async () => {
      queue.setSessionId("sess-1");
      // Push 4 events (below auto-flush threshold of 5)
      for (let i = 0; i < 4; i++) {
        queue.push(makeEvent());
      }
      expect(queue.size).toBe(4);

      // Manually flush — should send all 4 (< maxBatchSize)
      await queue.flush();
      expect(transport.sendEvents).toHaveBeenCalledTimes(1);
      const call = (transport.sendEvents as ReturnType<typeof vi.fn>).mock
        .calls[0][0];
      expect(call.events).toHaveLength(4);
      expect(queue.size).toBe(0);
    });
  });

  describe("periodic flush", () => {
    it("flushes on interval when started", async () => {
      queue.setSessionId("sess-1");
      queue.start();
      queue.push(makeEvent());

      await vi.advanceTimersByTimeAsync(2000);
      expect(transport.sendEvents).toHaveBeenCalledTimes(1);
    });

    it("does not flush after stop", async () => {
      queue.setSessionId("sess-1");
      queue.start();
      queue.push(makeEvent());
      queue.stop();

      await vi.advanceTimersByTimeAsync(5000);
      expect(transport.sendEvents).not.toHaveBeenCalled();
    });
  });

  describe("flushBeacon", () => {
    it("sends all events via beacon", () => {
      queue.setSessionId("sess-1");
      queue.push(makeEvent());
      queue.push(makeEvent());

      queue.flushBeacon();

      expect(transport.sendBeacon).toHaveBeenCalledWith({
        session_id: "sess-1",
        events: expect.arrayContaining([
          expect.objectContaining({ type: "click" }),
        ]),
      });
      expect(queue.size).toBe(0);
    });

    it("does nothing when queue is empty", () => {
      queue.setSessionId("sess-1");
      queue.flushBeacon();
      expect(transport.sendBeacon).not.toHaveBeenCalled();
    });
  });
});
