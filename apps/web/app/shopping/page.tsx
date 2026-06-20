import { Suspense } from "react";

import { ShoppingV2 } from "@/components/planam-v2/shopping/ShoppingV2";
import { ShoppingListView } from "@/components/shopping/ShoppingListView";
import { ShoppingSectionLayout } from "@/components/shopping/ShoppingSectionLayout";
import { SkeletonList } from "@/components/ui/Skeleton";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function ShoppingPage() {
  if (isPlanamUi2026Enabled()) {
    requirePlanamUi2026OrRedirect("/shopping");
    return <ShoppingV2 />;
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
