import { redirect } from "next/navigation";

import { RecipeDetailLegacy } from "@/app/recipes/[id]/RecipeDetailLegacy";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

type RecipeDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function RecipeDetailPage({ params }: RecipeDetailPageProps) {
  const { id } = await params;

  if (isPlanamUi2026Enabled()) {
    redirect(`/plan/recipes/${id}`);
  }

  return <RecipeDetailLegacy />;
}
