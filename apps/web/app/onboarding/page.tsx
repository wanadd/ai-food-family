import { redirect } from "next/navigation";

import { Onboarding2026Flow } from "@/components/onboarding-2026/Onboarding2026Flow";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function OnboardingPage() {
  if (isPlanamUi2026Enabled()) {
    return <Onboarding2026Flow />;
  }

  redirect("/profile/nutrition");
}
