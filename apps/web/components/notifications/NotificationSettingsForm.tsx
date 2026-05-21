"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  fetchNotificationSettings,
  updateNotificationSettings,
} from "@/lib/notifications/api";
import { TIMEZONE_OPTIONS } from "@/lib/notifications/options";
import type { NotificationSettings } from "@/lib/notifications/types";
import { getTelegramInitData } from "@/lib/telegram-webapp";

type ReminderCardProps = {
  emoji: string;
  title: string;
  description: string;
  enabled: boolean;
  time: string;
  onEnabledChange: (value: boolean) => void;
  onTimeChange: (value: string) => void;
  disabled: boolean;
};

function ReminderCard({
  emoji,
  title,
  description,
  enabled,
  time,
  onEnabledChange,
  onTimeChange,
  disabled,
}: ReminderCardProps) {
  return (
    <section
      className={`rounded-2xl border p-5 transition ${
        enabled
          ? "border-emerald-200 bg-white shadow-sm"
          : "border-stone-200 bg-stone-50/80"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex gap-3">
          <span className="text-2xl" aria-hidden>
            {emoji}
          </span>
          <div>
            <h3 className="font-semibold text-stone-900">{title}</h3>
            <p className="mt-1 text-sm text-stone-500">{description}</p>
          </div>
        </div>
        <label className="relative inline-flex cursor-pointer items-center">
          <input
            type="checkbox"
            checked={enabled}
            disabled={disabled}
            onChange={(event) => onEnabledChange(event.target.checked)}
            className="peer sr-only"
          />
          <span className="h-7 w-12 rounded-full bg-stone-200 transition peer-checked:bg-emerald-500 peer-disabled:opacity-50" />
          <span className="absolute left-0.5 top-0.5 h-6 w-6 rounded-full bg-white shadow transition peer-checked:translate-x-5" />
        </label>
      </div>

      <label
        className={`mt-4 block ${enabled ? "" : "pointer-events-none opacity-40"}`}
      >
        <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Время напоминания
        </span>
        <input
          type="time"
          value={time}
          disabled={disabled || !enabled}
          onChange={(event) => onTimeChange(event.target.value)}
          className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3 text-sm font-medium text-stone-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
        />
      </label>
    </section>
  );
}

export function NotificationSettingsForm() {
  const [initData, setInitData] = useState("");
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const loadSettings = useCallback(async (telegramInitData: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNotificationSettings(telegramInitData);
      setSettings(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить настройки",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const data = getTelegramInitData();
    setInitData(data);
    if (data) {
      loadSettings(data);
    } else {
      setLoading(false);
    }
  }, [loadSettings]);

  async function persist(patch: Parameters<typeof updateNotificationSettings>[1]) {
    if (!initData) {
      return;
    }
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const data = await updateNotificationSettings(initData, patch);
      setSettings(data);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось сохранить настройки",
      );
    } finally {
      setSaving(false);
    }
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">
          Уведомления настраиваются в Telegram Mini App после авторизации.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-emerald-700"
        >
          На главную
        </Link>
      </div>
    );
  }

  if (loading || !settings) {
    return (
      <p className="py-20 text-center text-sm text-stone-500">
        Загрузка настроек…
      </p>
    );
  }

  return (
    <div className="min-h-screen bg-[#fafaf9]">
      <header className="border-b border-stone-200/80 bg-white/80 px-5 py-6 backdrop-blur">
        <Link href="/" className="text-xs font-semibold text-emerald-700">
          ← Назад
        </Link>
        <h1 className="mt-3 text-2xl font-bold text-stone-900">Уведомления</h1>
        <p className="mt-1 text-sm text-stone-500">
          Напоминания приходят в Telegram в выбранное время
        </p>
      </header>

      <main className="mx-auto max-w-lg space-y-5 px-5 py-8">
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        {saved ? (
          <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            Настройки сохранены
          </p>
        ) : null}

        <section className="rounded-2xl border border-stone-200 bg-white p-5">
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">
              Часовой пояс
            </span>
            <select
              value={settings.timezone}
              disabled={saving}
              onChange={(event) => persist({ timezone: event.target.value })}
              className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3 text-sm font-medium text-stone-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
            >
              {TIMEZONE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </section>

        <ReminderCard
          emoji="🛒"
          title="Напомнить купить"
          description="Список покупок из выбранного меню — что ещё не отмечено"
          enabled={settings.buy_reminder_enabled}
          time={settings.buy_reminder_time}
          disabled={saving}
          onEnabledChange={(value) =>
            persist({ buy_reminder_enabled: value })
          }
          onTimeChange={(value) => persist({ buy_reminder_time: value })}
        />

        <ReminderCard
          emoji="👨‍🍳"
          title="Напомнить приготовить"
          description="Блюда на сегодня из выбранного семейного меню"
          enabled={settings.cook_reminder_enabled}
          time={settings.cook_reminder_time}
          disabled={saving}
          onEnabledChange={(value) =>
            persist({ cook_reminder_enabled: value })
          }
          onTimeChange={(value) => persist({ cook_reminder_time: value })}
        />

        <p className="text-center text-xs text-stone-400">
          {saving
            ? "Сохранение…"
            : "Убедитесь, что бот может писать вам в личные сообщения"}
        </p>
      </main>
    </div>
  );
}
