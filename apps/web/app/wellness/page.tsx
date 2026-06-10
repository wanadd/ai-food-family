import { WellnessV2 } from "@/components/planam-v2/wellness/WellnessV2";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function WellnessPage() {
  requirePlanamUi2026OrRedirect("/wellness");

  return <WellnessV2 />;
}
