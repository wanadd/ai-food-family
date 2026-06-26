import { RecipeCookingMode } from "@/components/recipes-2026/RecipeCookingMode";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

type PageProps = {
  params: { id: string };
};

export default function PlanRecipeCookPage({ params }: PageProps) {
  requirePlanamUi2026OrRedirect("/plan/recipes");

  const recipeId = Number(params.id);
  if (!Number.isFinite(recipeId) || recipeId <= 0) {
    return null;
  }

  return <RecipeCookingMode recipeId={recipeId} />;
}
