import { Suspense } from "react";

import { NutritionProfileForm } from "@/components/nutrition-profile/NutritionProfileForm";
import { SkeletonList } from "@/components/ui/Skeleton";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function AccountNutritionPage() {
  requirePlanamUi2026OrRedirect("/account/nutrition");

  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-lg space-y-3 px-4 pb-6">
          <SkeletonList count={4} />
        </div>
      }
    >
      <NutritionProfileForm />
    </Suspense>
  );
}
