import { RecipeCatalog2026 } from "@/components/recipes-2026/RecipeCatalog2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanRecipesPage() {
  requirePlanamUi2026OrRedirect("/plan/recipes");

  return <RecipeCatalog2026 />;
}
