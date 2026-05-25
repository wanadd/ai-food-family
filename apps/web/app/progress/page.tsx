import { Suspense } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { ProgressDashboard } from "@/components/progress/ProgressDashboard";
import { SkeletonList } from "@/components/ui/Skeleton";

export default function ProgressPage() {
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
