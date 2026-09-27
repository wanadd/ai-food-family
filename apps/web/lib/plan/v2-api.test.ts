import { describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import {
  createPlanningPlan,
  emptyPlanningSlot,
  generatePlanningRevision,
  replacePlanningSlot,
} from "./v2-api";

vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }));

describe("planning v2 API adapter", () => {
  it("uses canonical paths and idempotency keys for all commands", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ plan_id: "p1" });

    await createPlanningPlan("init", "personal", { owner_scope: "PERSON", person_id: "u1" }, "k1");
    await generatePlanningRevision("init", "personal", "p1", [], "k2", "r1");
    await replacePlanningSlot("init", "personal", "p1", "r1", "dinner", "rv2", "k3");
    await emptyPlanningSlot("init", "personal", "p1", "s1", "r2", "k4");

    expect(vi.mocked(apiFetch).mock.calls.map(([_, __, path]) => path)).toEqual([
      "/v2/plans",
      "/v2/plans/p1/generate",
      "/v2/plans/p1/revisions/r1/replace",
      "/v2/plans/p1/slots/s1/empty",
    ]);
    expect(vi.mocked(apiFetch).mock.calls.map(([_, __, ___, options]) => options?.headers)).toEqual([
      { "Idempotency-Key": "k1" },
      { "Idempotency-Key": "k2" },
      { "Idempotency-Key": "k3" },
      { "Idempotency-Key": "k4" },
    ]);
  });
});
