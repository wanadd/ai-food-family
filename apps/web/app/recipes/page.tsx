import { redirect } from "next/navigation";

import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

// Каталог рецептов: UI 2026 → /plan/recipes, legacy → /menu/recipes.
export default function RecipesPage() {
  redirect(isPlanamUi2026Enabled() ? "/plan/recipes" : "/menu/recipes");
}
