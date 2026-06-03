import { Suspense } from "react";

import { SubscriptionHub2026 } from "@/components/monetization-2026/SubscriptionHub2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function AccountSubscriptionPage() {
  requirePlanamUi2026OrRedirect("/account/subscription");

  return (
    <Suspense fallback={null}>
      <SubscriptionHub2026 />
    </Suspense>
  );
}
