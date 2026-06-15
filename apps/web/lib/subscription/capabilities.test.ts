import { describe, expect, it } from "vitest";

import { hasCapability, profileLimitForTariff } from "./capabilities";

describe("subscription capabilities", () => {
  it("start trial has profile limit 1", () => {
    expect(profileLimitForTariff("start_trial")).toBe(1);
  });

  it("family pro has sport mode", () => {
    expect(hasCapability("family_pro", "health_sport_mode")).toBe(true);
  });
});
