import { describe, expect, it, vi } from "vitest";

import { createEvent, listEvents } from "./v2-api";

describe("Events V2 API client", () => {
  it("uses the canonical collection endpoint", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [] }), { status: 200 }),
    );

    await listEvents("planam-test-session", "personal");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/v2/events"),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Telegram-Init-Data": "planam-test-session" }),
      }),
    );
    fetchMock.mockRestore();
  });

  it("sends event creation with an idempotency key", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ event_id: "event-1" }), { status: 200 }),
    );

    await createEvent("planam-test-session", "personal", {
      title: "Ужин",
      event_type: "dinner",
      starts_at: "2026-09-27T18:00:00.000Z",
      collaboration_mode: "RESTRICTIONS_COLLECTION",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/v2/events"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Idempotency-Key": expect.any(String) }),
      }),
    );
    fetchMock.mockRestore();
  });
});
