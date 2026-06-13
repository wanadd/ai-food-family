import type { RecipeSummary } from "@/lib/recipes/types";

/** Short card heading — prefer display_title for catalog grids. */
export function recipeCardHeading(recipe: Pick<RecipeSummary, "display_title" | "title">): string {
  const display = recipe.display_title?.trim();
  if (display) return display;
  return recipe.title?.trim() || "";
}

/** Full detail heading — always the canonical recipe title. */
export function recipeDetailHeading(recipe: Pick<RecipeSummary, "title">): string {
  return recipe.title?.trim() || "";
}
