import { RoutePlaceholder2026 } from "@/components/planam-2026/screens/RoutePlaceholder2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function HomePantryPage() {
  requirePlanamUi2026OrRedirect("/home/pantry");

  return (
    <RoutePlaceholder2026
      title="Запасы"
      description="Сроки годности и остатки дома."
      sprintNote="Legacy: /shopping/pantry. Контент — Sprint 6."
    />
  );
}
