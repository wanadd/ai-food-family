import { describe, expect, it } from "vitest";

import { foodSafetyPresentation } from "./food-safety";

describe("food safety presentation", () => {
  it("preserves UNKNOWN instead of making it reassuring", () => {
    const view = foodSafetyPresentation({
      decision: "UNKNOWN",
      person_id: "person-2",
      food_identity_id: 4,
      reason_codes: ["missing_evidence"],
      evidence_claim_ids: [],
    });
    expect(view.state).toBe("UNKNOWN");
    expect(view.personId).toBe("person-2");
    expect(view.label).toContain("Недостаточно");
  });

  it("keeps a server BLOCK visible with its person attribution", () => {
    const view = foodSafetyPresentation({
      decision: "BLOCK",
      person_id: "child-1",
      food_identity_id: null,
      reason_codes: ["allergen"],
      evidence_claim_ids: ["claim-1"],
    });
    expect(view.state).toBe("BLOCK");
    expect(view.personId).toBe("child-1");
  });
});
