import { RoutePlaceholder2026 } from "@/components/planam-2026/screens/RoutePlaceholder2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanPage() {
  requirePlanamUi2026OrRedirect("/plan");

  return (
    <RoutePlaceholder2026
      title="План на неделю"
      description="Календарь меню и быстрый доступ к генерации."
      sprintNote="Контент из /menu — миграция в Sprint 4–5."
    />
  );
}
