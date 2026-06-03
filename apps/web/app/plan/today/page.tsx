import { RoutePlaceholder2026 } from "@/components/planam-2026/screens/RoutePlaceholder2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function PlanTodayPage() {
  requirePlanamUi2026OrRedirect("/plan/today");

  return (
    <RoutePlaceholder2026
      title="Сегодня"
      description="Immersive-лента блюд на день (Hero cards)."
      sprintNote="Legacy: /menu/current. Реализация — после Home 2026."
    />
  );
}
