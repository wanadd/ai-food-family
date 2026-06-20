import { redirect } from "next/navigation";
import { Suspense } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { ProgressDashboard } from "@/components/progress/ProgressDashboard";
import { SkeletonList } from "@/components/ui/Skeleton";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function ProgressPage() {
  if (isPlanamUi2026Enabled()) {
    redirect("/wellness");
  }
  return (
    <Suspense
      fallback={
        <ScreenLayout title="Прогресс" contentClassName="space-y-3 pb-24">
          <SkeletonList count={3} />
        </ScreenLayout>
      }
    >
      <ProgressDashboard />
    </Suspense>
  );
}
