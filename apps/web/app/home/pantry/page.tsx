import { PantryV2 } from "@/components/planam-v2/home-domain/PantryV2";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function HomePantryPage() {
  requirePlanamUi2026OrRedirect("/home/pantry");

  return <PantryV2 />;
}
