import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

/** Canonical PLANAM 2026 plan routes. */
export const PLAN_PATHS = {
  week: "/plan",
  today: "/plan/today",
  generate: "/plan/generate",
  recipes: "/plan/recipes",
  recipe: (id: number) => `/plan/recipes/${id}`,
} as const;

const LEGACY_PLAN: Record<string, string> = {
  "/menu": "/menu",
  "/menu/current": "/menu/current",
  "/menu/generate": "/menu/generate",
  "/menu/recipes": "/menu/recipes",
};

const TO_2026: Record<string, string> = {
  "/menu": PLAN_PATHS.week,
  "/menu/current": PLAN_PATHS.today,
  "/menu/generate": PLAN_PATHS.generate,
  "/menu/recipes": PLAN_PATHS.recipes,
};

/** Resolve menu/plan links for Home, rail, and deep links. */
export function resolvePlanPath(
  path: string,
  use2026: boolean = isPlanamUi2026Enabled(),
): string {
  if (!use2026) {
    return LEGACY_PLAN[path] ?? path;
  }
  if (path.startsWith("/recipes/")) {
    const id = path.replace("/recipes/", "");
    return PLAN_PATHS.recipe(Number(id));
  }
  return TO_2026[path] ?? path;
}

export function recipeDetailPath(
  recipeId: number,
  use2026: boolean = isPlanamUi2026Enabled(),
): string {
  return use2026 ? PLAN_PATHS.recipe(recipeId) : `/recipes/${recipeId}`;
}
