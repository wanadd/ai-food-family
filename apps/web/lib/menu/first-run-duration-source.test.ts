import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));

describe("first-run menu duration source", () => {
  it("onboarding offers selectable durations and passes selected planDays", () => {
    const source = readFileSync(
      `${repoRoot}/components/onboarding-2026/Onboarding2026Flow.tsx`,
      "utf8",
    );
    expect(source).toContain("MENU_DURATION_OPTIONS");
    expect(source).toContain("setPlanDays(days)");
    expect(source).toContain("planDays,");
    expect(source).toContain("Выберите длительность меню: 1, 3, 5 или 7 дней.");
    expect(source).not.toContain("planDays: 5");
  });

  it("manual generator uses the same allowed duration options", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/menu/GenerateMenuV2.tsx`,
      "utf8",
    );
    expect(source).toContain("MENU_DURATION_OPTIONS");
    expect(source).toContain("DEFAULT_MENU_DURATION_DAYS");
    expect(source).toContain("setPlanDays(d)");
    expect(source).toContain("Собрать меню на {formatMenuDuration(planDays)}");
  });

  it("copy does not hardcode seven days before selection", () => {
    const files = [
      "components/onboarding-2026/OnboardingGenerateStep2026.tsx",
      "components/onboarding-2026/OnboardingWowReveal2026.tsx",
      "components/planam-v2/menu/GenerateMenuV2.tsx",
      "components/planam-v2/shopping/ShoppingV2.tsx",
    ];
    for (const file of files) {
      const source = readFileSync(`${repoRoot}/${file}`, "utf8");
      expect(source).not.toContain("первое меню на 7 дней");
      expect(source).not.toContain("Покупки для меню на 7 дней");
    }
  });
});
