import { PlanGenerate2026 } from "@/components/plan-2026/PlanGenerate2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanGeneratePage() {
  requirePlanamUi2026OrRedirect("/plan/generate");

  return <PlanGenerate2026 />;
}
