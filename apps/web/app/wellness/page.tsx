import { WellnessHome2026 } from "@/components/wellness-2026/WellnessHome2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function WellnessPage() {
  requirePlanamUi2026OrRedirect("/wellness");

  return <WellnessHome2026 />;
}
