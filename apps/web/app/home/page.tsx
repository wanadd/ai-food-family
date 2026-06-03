import { redirect } from "next/navigation";

import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

/** Алиас «Дом» → главный экран `/`. */
export default function HomeSectionPage() {
  requirePlanamUi2026OrRedirect("/home");
  redirect("/");
}
