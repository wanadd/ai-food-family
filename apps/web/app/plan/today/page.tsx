import { Suspense } from "react";

import { PlanToday2026 } from "@/components/plan-2026/PlanToday2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanTodayPage() {
  requirePlanamUi2026OrRedirect("/plan/today");

  return (
    <Suspense fallback={null}>
      <PlanToday2026 />
    </Suspense>
  );
}
