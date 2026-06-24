import { Suspense } from "react";

import { ShoppingV2 } from "@/components/planam-v2/shopping/ShoppingV2";
import { Shopping2026 } from "@/components/dom-2026/Shopping2026";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function HomeShoppingPage() {
  if (isPlanamUi2026Enabled()) {
    return (
      <Suspense fallback={null}>
        <ShoppingV2 />
      </Suspense>
    );
  }
  return <Shopping2026 />;
}
