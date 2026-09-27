import { describe, expect, it } from "vitest";

import {
  displayScopeLabel,
  hasEntitlement,
  recoverScope,
  selectHousehold,
  type HouseholdOption,
} from "@/lib/v2/household-scope";

const households: HouseholdOption[] = [
  { household_id: "h1", name: "Дом", status: "active", role: "owner" },
  { household_id: "h2", name: "Дача", status: "active", role: "member" },
];

describe("Wave 1 household scope", () => {
  it("supports personal mode and recovers stale selections", () => {
    expect(selectHousehold([], "missing")).toBeNull();
    expect(recoverScope([], { householdId: "missing", personId: "p1" })).toEqual({
      householdId: null,
      personId: "p1",
    });
    expect(displayScopeLabel([], { householdId: null, personId: null })).toBe("Личный режим");
  });

  it("selects only an authorized household and falls back deterministically", () => {
    expect(selectHousehold(households, "h2")?.name).toBe("Дача");
    expect(recoverScope(households, { householdId: "foreign", personId: null })).toEqual({
      householdId: "h1",
      personId: null,
    });
  });

  it("uses server-provided effective entitlements", () => {
    expect(hasEntitlement([{ capability: "core.household.manage", allowed: true, limit: null, used: 0, remaining: null, source: "policy" }], "core.household.manage")).toBe(true);
    expect(hasEntitlement([{ capability: "core.household.manage", allowed: false, limit: 0, used: 0, remaining: 0, source: "policy" }], "core.household.manage")).toBe(false);
  });
});
