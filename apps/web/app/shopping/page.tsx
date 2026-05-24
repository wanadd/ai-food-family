import { Suspense } from "react";

import { ShoppingListView } from "@/components/shopping/ShoppingListView";
import { PageLoading } from "@/components/ui/PageLoading";

export default function ShoppingPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-stone-50">
          <PageLoading message="Загрузка покупок…" />
        </div>
      }
    >
      <ShoppingListView />
    </Suspense>
  );
}
