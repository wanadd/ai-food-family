import { redirect } from "next/navigation";

import { Shopping2026 } from "@/components/dom-2026/Shopping2026";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function HomeShoppingPage() {
  if (isPlanamUi2026Enabled()) {
    redirect("/shopping");
  }
  requirePlanamUi2026OrRedirect("/home/shopping");
  return <Shopping2026 />;
}
