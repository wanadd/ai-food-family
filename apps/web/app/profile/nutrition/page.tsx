import { Suspense } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { NutritionProfileForm } from "@/components/nutrition-profile/NutritionProfileForm";
import { SkeletonList } from "@/components/ui/Skeleton";
import { redirectLegacyToPlanam2026 } from "@/lib/planam/planam-2026-page";

export default function NutritionProfilePage() {
  redirectLegacyToPlanam2026("/account/nutrition");
  return (
    <Suspense
      fallback={
        <ScreenLayout
          title="Нутрициологический профиль"
          contentClassName="space-y-3 pb-24"
        >
          <SkeletonList count={4} />
        </ScreenLayout>
      }
    >
      <NutritionProfileForm />
    </Suspense>
  );
}
