import { RoutePlaceholder2026 } from "@/components/planam-2026/screens/RoutePlaceholder2026";
import { requirePlanamUi2026OrRedirect } from "@/lib/planam/planam-2026-page";

export default function WellnessPage() {
  requirePlanamUi2026OrRedirect("/wellness");

  return (
    <RoutePlaceholder2026
      title="Забота"
      description="Вода, чекины, советы и прогресс в одном scroll."
      sprintNote="Legacy: /health. Контент — Sprint 7."
    />
  );
}
