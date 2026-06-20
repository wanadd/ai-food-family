import { Suspense } from "react";

import { MenuTodayV2 } from "@/components/planam-v2/menu/MenuTodayV2";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanTodayPage() {
  requirePlanamUi2026OrRedirect("/plan/today");

  return (
    <Suspense fallback={null}>
      <MenuTodayV2 />
    </Suspense>
  );
}
