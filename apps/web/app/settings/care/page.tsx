import { CareSettingsPanel } from "@/components/care/CareSettingsPanel";
import { ScreenLayout } from "@/components/layout/ScreenLayout";

export default function CareSettingsPage() {
  return (
    <ScreenLayout
      title="Забота ПланАм"
      subtitle="Мягкие напоминания в Telegram"
      back={{ label: "Настройки", href: "/settings" }}
    >
      <p className="mb-4 text-sm leading-relaxed text-stone-600">
        Сообщения приходят в чат с ботом ПланАм. Настройки сохраняются автоматически.
      </p>
      <CareSettingsPanel />
    </ScreenLayout>
  );
}
