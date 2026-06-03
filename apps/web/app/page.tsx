import { Suspense } from "react";

import { PlanAmHome } from "@/components/home/PlanAmHome";
import { Home2026 } from "@/components/home-2026/Home2026";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function Home() {
  if (isPlanamUi2026Enabled()) {
    return (
      <Suspense fallback={null}>
        <Home2026 />
      </Suspense>
    );
  }

  return <PlanAmHome />;
}
