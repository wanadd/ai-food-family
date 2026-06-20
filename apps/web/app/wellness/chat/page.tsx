import { WellnessChat2026 } from "@/components/wellness-2026/WellnessChat2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function WellnessChatPage() {
  requirePlanamUi2026OrRedirect("/wellness/chat");

  return <WellnessChat2026 />;
}
