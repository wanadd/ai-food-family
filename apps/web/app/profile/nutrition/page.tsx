import { Suspense } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { NutritionProfileForm } from "@/components/nutrition-profile/NutritionProfileForm";
import { SkeletonList } from "@/components/ui/Skeleton";

export default function NutritionProfilePage() {
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
