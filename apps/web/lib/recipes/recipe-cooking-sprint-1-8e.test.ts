import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { getBackFallback2026 } from "@/lib/navigation/back-navigation-2026";
import {
  isBottomNavHidden2026,
  isRecipeCookingModePath,
} from "@/lib/navigation/nav-config-2026";
import { resolveMigrationTarget } from "@/lib/navigation/route-migration-2026";
import { recipeCookPath } from "@/lib/recipes/recipe-meal-context";
import { parseStepMinutes } from "@/lib/recipes/recipe-step-timer";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));

describe("recipe cooking sprint 1.8e", () => {
  it("renders recipe detail with cook CTA and checklist", () => {
    const source = readFileSync(
      `${repoRoot}/components/recipes-2026/RecipeDetail2026.tsx`,
      "utf8",
    );
    expect(source).toContain('data-testid="recipe-start-cook"');
    expect(source).toContain("Начать готовить");
    expect(source).toContain("RecipeIngredientsChecklist");
    expect(source).toContain("Открыть режим готовки");
    expect(source).not.toContain("markRecipeCooked");
  });

  it("cooking mode renders step progress and finish CTA", () => {
    const source = readFileSync(
      `${repoRoot}/components/recipes-2026/RecipeCookingMode.tsx`,
      "utf8",
    );
    expect(source).toContain('data-testid="recipe-cooking-mode"');
    expect(source).toContain('data-testid="recipe-cook-progress"');
    expect(source).toContain('data-testid="recipe-cook-finish"');
    expect(source).toContain('data-testid="recipe-cook-next"');
    expect(source).toContain('data-testid="recipe-cook-prev"');
  });

  it("finish sheet separates eaten from later", () => {
    const source = readFileSync(
      `${repoRoot}/components/recipes-2026/RecipeCookFinishSheet.tsx`,
      "utf8",
    );
    expect(source).toContain('data-testid="recipe-finish-eaten"');
    expect(source).toContain('data-testid="recipe-finish-later"');
    expect(source).toContain('data-testid="recipe-finish-pantry"');
    expect(source).toContain("Приготовленное не считается съеденным");
    expect(source).toContain('actual_status: "ate_home"');
    expect(source).toContain('actual_status: "cooked"');
  });

  it("parses step timer minutes from Russian text", () => {
    expect(parseStepMinutes("Тушить 15 минут на слабом огне")).toBe(15);
    expect(parseStepMinutes("Без таймера")).toBeNull();
  });

  it("builds cook path preserving returnTo", () => {
    const params = new URLSearchParams("returnTo=%2Fplan%2Ftoday&mealType=lunch");
    expect(recipeCookPath(256, params)).toBe(
      "/plan/recipes/256/cook?returnTo=%2Fplan%2Ftoday&mealType=lunch",
    );
  });

  it("hides bottom nav on cooking mode route", () => {
    expect(isRecipeCookingModePath("/plan/recipes/256/cook")).toBe(true);
    expect(isBottomNavHidden2026("/plan/recipes/256/cook")).toBe(true);
    expect(isBottomNavHidden2026("/plan/recipes")).toBe(false);
  });

  it("cooking mode back returns to recipe detail", () => {
    expect(getBackFallback2026("/plan/recipes/256/cook")).toBe("/plan/recipes/256");
  });

  it("preserves legacy recipe redirect", () => {
    expect(resolveMigrationTarget("/recipes/256")).toBe("/plan/recipes/256");
  });

  it("has cook route page", () => {
    const page = readFileSync(
      `${repoRoot}/app/plan/recipes/[id]/cook/page.tsx`,
      "utf8",
    );
    expect(page).toContain("RecipeCookingMode");
  });
});
