import { GenerateMenuV2 } from "@/components/planam-v2/menu/GenerateMenuV2";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanGeneratePage() {
  requirePlanamUi2026OrRedirect("/plan/generate");

  return <GenerateMenuV2 />;
}
