import { Suspense } from "react";

import { PaymentStub2026 } from "@/components/monetization-2026/PaymentStub2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function SubscriptionCheckoutPage() {
  requirePlanamUi2026OrRedirect("/account/subscription/checkout");

  return (
    <Suspense fallback={null}>
      <PaymentStub2026 />
    </Suspense>
  );
}
