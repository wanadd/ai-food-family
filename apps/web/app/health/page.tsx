import { redirect } from "next/navigation";

import { NutritionistDashboard } from "@/components/nutritionist/NutritionistDashboard";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

export default function HealthPage() {
  if (isPlanamUi2026Enabled()) {
    redirect("/wellness");
  }
  return <NutritionistDashboard />;
}
