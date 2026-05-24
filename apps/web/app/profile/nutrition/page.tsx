import { Suspense } from "react";

import { NutritionProfileForm } from "@/components/nutrition-profile/NutritionProfileForm";
import { PageLoading } from "@/components/ui/PageLoading";

export default function NutritionProfilePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-stone-50">
          <PageLoading message="Загрузка…" />
        </div>
      }
    >
      <NutritionProfileForm />
    </Suspense>
  );
}
