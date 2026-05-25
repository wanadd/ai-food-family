import { Suspense } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { ShoppingListView } from "@/components/shopping/ShoppingListView";
import { SkeletonList } from "@/components/ui/Skeleton";

export default function ShoppingPage() {
  return (
    <Suspense
      fallback={
        <ScreenLayout title="Покупки" contentClassName="space-y-3 pb-24">
          <SkeletonList count={3} />
        </ScreenLayout>
      }
    >
      <ShoppingListView />
    </Suspense>
  );
}
