"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { CareSettingsPanel } from "@/components/care/CareSettingsPanel";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { NotificationSettingsForm } from "@/components/notifications/NotificationSettingsForm";
import { useTelegram } from "@/components/TelegramProvider";
import { usePlanam2026Embedded } from "@/lib/planam/embedded-2026";

const NOTIFICATION_SECTIONS = [
  {
    title: "Готовка",
    body: "Напомнить начать готовить и отметить результат.",
  },
  {
    title: "Покупки",
    body: "Вернуть к списку продуктов перед походом в магазин.",
  },
  {
    title: "Здоровье",
    body: "Вода, питание и мягкие рекомендации без давления.",
  },
  {
    title: "Тихие часы",
    body: "Период, когда PLANAM не присылает сообщения.",
  },
];

function NotificationsFrame({ children }: { children: ReactNode }) {
  const embedded = usePlanam2026Embedded("/account/notifications");

  if (embedded) {
    return (
      <div className="mx-auto max-w-lg space-y-5 px-4 pb-6 pt-[max(0.75rem,env(safe-area-inset-top))]">
        {children}
      </div>
    );
  }

  return (
    <ScreenLayout
      title="Уведомления"
      subtitle="Заботливые подсказки от ПланАм в Telegram"
      back={{ label: "Профиль", href: "/account" }}
      contentClassName="space-y-6"
    >
      {children}
    </ScreenLayout>
  );
}

export function NotificationsView() {
  const { initData } = useTelegram();
  const embedded = usePlanam2026Embedded("/account/notifications");

  if (!initData) {
    if (embedded) {
      return (
        <div className="mx-auto max-w-lg px-4 pb-6">
          <p className="text-sm text-pa-muted">
            Уведомления настраиваются в Telegram Mini App после авторизации.
          </p>
          <Link
            href="/"
            className="mt-6 inline-block text-sm font-semibold text-sage-700"
          >
            На главную
          </Link>
        </div>
      );
    }

    return (
      <ScreenLayout
        title="Уведомления"
        back={{ label: "Профиль", href: "/account" }}
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
    <NotificationsFrame>
      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <p className="text-sm leading-relaxed text-pa-muted">
          Мягкие подсказки о готовке, покупках и здоровье в удобное время.
        </p>
      </section>

      <section className="grid gap-2">
        {NOTIFICATION_SECTIONS.map((item) => (
          <article
            key={item.title}
            className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none"
          >
            <p className="text-sm font-semibold text-pa-foreground">{item.title}</p>
            <p className="mt-1 text-xs leading-relaxed text-pa-muted">{item.body}</p>
          </article>
        ))}
      </section>

      <CareSettingsPanel />

      <NotificationSettingsForm />
    </NotificationsFrame>
  );
}
