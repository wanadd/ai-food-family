import { Suspense } from "react";

import { ProgressDashboard } from "@/components/progress/ProgressDashboard";
import { PageLoading } from "@/components/ui/PageLoading";

export default function ProgressPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-stone-50">
          <PageLoading message="Загрузка…" />
        </div>
      }
    >
      <ProgressDashboard />
    </Suspense>
  );
}
