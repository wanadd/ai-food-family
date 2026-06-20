import { PlanWeek2026 } from "@/components/plan-2026/PlanWeek2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanPage() {
  requirePlanamUi2026OrRedirect("/plan");

  return <PlanWeek2026 />;
}
