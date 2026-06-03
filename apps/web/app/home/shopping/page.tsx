import { Shopping2026 } from "@/components/dom-2026/Shopping2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function HomeShoppingPage() {
  requirePlanamUi2026OrRedirect("/home/shopping");

  return <Shopping2026 />;
}
