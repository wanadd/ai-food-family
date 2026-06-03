import { RoutePlaceholder2026 } from "@/components/planam-2026/screens/RoutePlaceholder2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function HomeShoppingPage() {
  requirePlanamUi2026OrRedirect("/home/shopping");

  return (
    <RoutePlaceholder2026
      title="Список покупок"
      description="Full-bleed checklist, прогресс «куплено»."
      sprintNote="Legacy: /shopping. Контент — Sprint 6."
    />
  );
}
