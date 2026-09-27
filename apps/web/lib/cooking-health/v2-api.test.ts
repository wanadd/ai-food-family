import { describe, expect, it, vi } from "vitest";
import { apiFetch } from "@/lib/api-client";
import { completeCookingV2, readHealthDeviationsV2, recordMealCheckinV2, startCookingV2 } from "./v2-api";

vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }));

describe("W6 API contract", () => {
  it("uses exactly the four frozen routes", async () => {
    vi.mocked(apiFetch).mockResolvedValue({});
    await startCookingV2("", "personal", "h1", {}, "s1");
    await completeCookingV2("", "personal", "s1", {}, "s2");
    await recordMealCheckinV2("", "personal", "p1", { external_description: "snack" }, "s3");
    await readHealthDeviationsV2("", "personal", "p1");
    expect(vi.mocked(apiFetch).mock.calls.map((call) => call[2])).toEqual([
      "/v2/households/h1/cooking-sessions",
      "/v2/cooking-sessions/s1/complete",
      "/v2/people/p1/meal-checkins",
      "/v2/people/p1/health/deviations",
    ]);
  });
});
