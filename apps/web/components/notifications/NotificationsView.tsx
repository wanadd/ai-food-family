"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { CareSettingsPanel } from "@/components/care/CareSettingsPanel";
import { NotificationOnboardingPanel } from "@/components/notifications/NotificationOnboardingPanel";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { NotificationSettingsForm } from "@/components/notifications/NotificationSettingsForm";
import { useTelegram } from "@/components/TelegramProvider";
import { usePlanam2026Embedded } from "@/lib/planam/embedded-2026";
import { fetchNotificationSettings } from "@/lib/notifications/api";
import type { NotificationSettings } from "@/lib/notifications/types";

function NotificationsFrame({ children }: { children: ReactNode }) {
  const embedded = usePlanam2026Embedded("/account/notifications");

  if (embedded) {
    return (
      <div className="mx-auto max-w-lg space-y-4 px-4 pb-6 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <h1 className="pa26-page-title">Уведомления</h1>
        <p className="text-sm leading-relaxed text-pa-muted">
          Включайте только нужные напоминания в Telegram.
        </p>
        {children}
      </div>
    );
  }

  return (
    <ScreenLayout
      title="Уведомления"
      subtitle="Включайте только нужные напоминания в Telegram"
      back={{ label: "Профиль", href: "/account" }}
      contentClassName="space-y-4"
    >
      {children}
    </ScreenLayout>
  );
}

export function NotificationsView() {
  const { initData } = useTelegram();
  const embedded = usePlanam2026Embedded("/account/notifications");
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [loading, setLoading] = useState(true);

  const reloadSettings = useCallback(async () => {
    if (!initData) return;
    const row = await fetchNotificationSettings(initData);
    setSettings(row);
  }, [initData]);

  useEffect(() => {
    if (!initData) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const row = await fetchNotificationSettings(initData);
        if (!cancelled) setSettings(row);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [initData]);

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
      {loading ? (
        <p className="text-sm text-pa-muted">Загрузка настроек…</p>
      ) : settings && !settings.notifications_onboarded ? (
        <NotificationOnboardingPanel onSaved={() => void reloadSettings()} />
      ) : (
        <>
          {settings?.care_mode === "off" ? (
            <p className="rounded-card border border-pa-border bg-pa-surface p-4 text-sm text-pa-muted">
              Уведомления выключены. Включите категории ниже, когда будете готовы;
              это не обязательный шаг первого запуска.
            </p>
          ) : null}
          <CareSettingsPanel />

          <details className="group rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <summary className="cursor-pointer list-none">
          <span className="flex items-center justify-between">
            <span className="text-sm font-bold text-pa-foreground">
              Расписание готовки и покупок
            </span>
            <span className="text-xs text-pa-muted group-open:rotate-180 transition">
              ▼
            </span>
          </span>
          <span className="mt-0.5 block text-xs text-pa-muted">
            Точное время напоминаний по приёмам пищи
          </span>
        </summary>
        <div className="mt-4">
          <NotificationSettingsForm />
        </div>
      </details>
        </>
      )}
    </NotificationsFrame>
  );
}
