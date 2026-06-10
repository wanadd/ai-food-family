import { Suspense } from "react";

import { PlanAmHome } from "@/components/home/PlanAmHome";
import { HomeV2 } from "@/components/planam-v2/home/HomeV2";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function Home() {
  if (isPlanamUi2026Enabled()) {
    return (
      <Suspense fallback={null}>
        <HomeV2 />
      </Suspense>
    );
  }

  return <PlanAmHome />;
}
