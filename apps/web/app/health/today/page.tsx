import { redirect } from "next/navigation";

import { HealthTodayView } from "@/components/nutritionist/HealthTodayView";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function HealthTodayPage() {
  if (isPlanamUi2026Enabled()) {
    redirect("/wellness");
  }
  return <HealthTodayView />;
}
