"use client";

import Link from "next/link";

import { CareSettingsPanel } from "@/components/care/CareSettingsPanel";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { NotificationSettingsForm } from "@/components/notifications/NotificationSettingsForm";
import { useTelegram } from "@/components/TelegramProvider";

export default function NotificationsPage() {
  const { initData } = useTelegram();

  if (!initData) {
    return (
      <ScreenLayout
        title="Уведомления"
        back={{ label: "Профиль", href: "/profile" }}
      >
        <p className="text-sm text-graphite-600">
          Уведомления настраиваются в Telegram Mini App после авторизации.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-sage-700"
        >
          На главную
        </Link>
      </ScreenLayout>
    );
  }

  return (
    <ScreenLayout
      title="Уведомления"
      subtitle="Заботливые подсказки от ПланАм в Telegram"
      back={{ label: "Профиль", href: "/profile" }}
      contentClassName="space-y-6"
    >
      <p className="text-sm text-graphite-600">
        ПланАм может мягко напоминать о важном — без давления и в удобное время.
      </p>

      <CareSettingsPanel />

      <NotificationSettingsForm />
    </ScreenLayout>
  );
}
