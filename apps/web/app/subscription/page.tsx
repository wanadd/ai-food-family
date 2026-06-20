import { redirect } from "next/navigation";

import { SubscriptionDashboard } from "@/components/subscription/SubscriptionDashboard";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { MONETIZATION_PATHS } from "@/lib/monetization/paths";

export default function SubscriptionPage() {
  if (isPlanamUi2026Enabled()) {
    redirect(MONETIZATION_PATHS.subscription);
  }
  return <SubscriptionDashboard />;
}
