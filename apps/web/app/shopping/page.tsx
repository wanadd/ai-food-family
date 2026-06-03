import { redirect } from "next/navigation";
import { Suspense } from "react";

import { ShoppingListView } from "@/components/shopping/ShoppingListView";
import { ShoppingSectionLayout } from "@/components/shopping/ShoppingSectionLayout";
import { SkeletonList } from "@/components/ui/Skeleton";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function ShoppingPage() {
  if (isPlanamUi2026Enabled()) {
    redirect("/home/shopping");
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
