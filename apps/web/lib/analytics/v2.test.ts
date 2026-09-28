import { describe, expect, it } from "vitest";

import { sanitizeAnalyticsPayload } from "./v2";

describe("v2 analytics privacy boundary", () => {
  it("drops sensitive and provider identity fields", () => {
    expect(sanitizeAnalyticsPayload({
      surface: "events",
      count: 2,
      allergy: "peanut",
      invitation_token: "secret",
      telegram_id: 123,
      prompt: "private",
    })).toEqual({ surface: "events", count: 2 });
  });

  it("keeps bounded scalar dimensions only", () => {
    expect(sanitizeAnalyticsPayload({ ok: true, value: null, nested: { raw: true } }))
      .toEqual({ ok: true, value: null });
  });
});
