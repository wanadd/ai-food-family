import { CareSettingsPanel } from "@/components/care/CareSettingsPanel";
import { ScreenLayout } from "@/components/layout/ScreenLayout";

export default function NutritionistCarePage() {
  return (
    <ScreenLayout
      title="Забота ПланАм"
      subtitle="Уведомления в Telegram"
      back={{ label: "Нутрициолог", href: "/nutritionist" }}
    >
      <CareSettingsPanel />
    </ScreenLayout>
  );
}
