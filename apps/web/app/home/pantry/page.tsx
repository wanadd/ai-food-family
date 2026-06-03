import { Pantry2026 } from "@/components/dom-2026/Pantry2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function HomePantryPage() {
  requirePlanamUi2026OrRedirect("/home/pantry");

  return <Pantry2026 />;
}
