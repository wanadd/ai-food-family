import { Suspense } from "react";

import { ShoppingListView } from "@/components/shopping/ShoppingListView";
import { ShoppingSectionLayout } from "@/components/shopping/ShoppingSectionLayout";
import { SkeletonList } from "@/components/ui/Skeleton";

export default function ShoppingPage() {
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
