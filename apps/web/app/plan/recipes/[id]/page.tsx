import { RecipeDetail2026 } from "@/components/recipes-2026/RecipeDetail2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

type PageProps = {
  params: { id: string };
};

export default function PlanRecipeDetailPage({ params }: PageProps) {
  requirePlanamUi2026OrRedirect("/plan/recipes");

  const recipeId = Number(params.id);
  if (!Number.isFinite(recipeId) || recipeId <= 0) {
    return null;
  }

  return <RecipeDetail2026 recipeId={recipeId} />;
}
