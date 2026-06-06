import { Suspense } from "react";

import { Shopping2026 } from "@/components/dom-2026/Shopping2026";
import { ShoppingListView } from "@/components/shopping/ShoppingListView";
import { ShoppingSectionLayout } from "@/components/shopping/ShoppingSectionLayout";
import { SkeletonList } from "@/components/ui/Skeleton";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function ShoppingPage() {
  if (isPlanamUi2026Enabled()) {
    requirePlanamUi2026OrRedirect("/shopping");
    return <Shopping2026 />;
  }
  return (
    <Suspense
      fallback={
        <ShoppingSectionLayout subtitle="Список покупок семьи">
          <SkeletonList count={3} />
        </ShoppingSectionLayout>
      }
    >
      <ShoppingListView />
    </Suspense>
  );
}
