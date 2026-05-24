"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useTelegram } from "@/components/TelegramProvider";

import {
  buildIcsFile,
  downloadIcs,
  nextOccurrence,
} from "@/lib/notifications/calendar";
import {
  fetchNotificationSettings,
  updateNotificationSettings,
} from "@/lib/notifications/api";
import { getDeviceTimezone } from "@/lib/notifications/timezone";
import type { NotificationSettings } from "@/lib/notifications/types";

type ReminderCardProps = {
  emoji: string;
  title: string;
  description: string;
  category: string;
  enabled: boolean;
  time: string;
  daysLabel: string;
  onEnabledChange: (value: boolean) => void;
  onTimeChange: (value: string) => void;
  onAddToCalendar: () => void;
  disabled: boolean;
};

function ReminderCard({
  emoji,
  title,
  description,
  category,
  enabled,
  time,
  daysLabel,
  onEnabledChange,
  onTimeChange,
  onAddToCalendar,
  disabled,
}: ReminderCardProps) {
  return (
    <section
      className={`rounded-2xl border p-5 transition ${
        enabled
          ? "border-emerald-200 bg-emerald-50/30"
          : "border-stone-100 bg-white"
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl" aria-hidden>
          {emoji}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-stone-900">{title}</h3>
            <label className="relative inline-flex cursor-pointer items-center">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={enabled}
                disabled={disabled}
                onChange={(e) => onEnabledChange(e.target.checked)}
              />
              <span className="h-7 w-12 rounded-full bg-stone-200 transition peer-checked:bg-emerald-600 peer-disabled:opacity-50" />
              <span className="absolute left-0.5 top-0.5 h-6 w-6 rounded-full bg-white shadow transition peer-checked:translate-x-5" />
            </label>
          </div>
          <p className="mt-1 text-sm text-stone-500">{description}</p>
          <p className="mt-1 text-xs text-stone-400">
            {category} · {daysLabel}
          </p>
          {enabled ? (
            <>
              <label className="mt-4 block">
                <span className="text-xs font-medium text-stone-600">Время</span>
                <input
                  type="time"
                  value={time}
                  disabled={disabled}
                  onChange={(e) => onTimeChange(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-stone-200 px-3 py-2.5 text-base"
                />
              </label>
              <button
                type="button"
                disabled={disabled}
                onClick={onAddToCalendar}
                className="mt-3 w-full rounded-xl border border-stone-200 bg-white py-2.5 text-sm font-semibold text-stone-800"
              >
                Добавить в календарь
              </button>
            </>
          ) : null}
        </div>
      </div>
    </section>
  );
}

export function NotificationSettingsForm() {
  const { initData } = useTelegram();
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
      if (!data) {
        setSettings(null);
        return;
      }
      const deviceTz = getDeviceTimezone();
      if (data.timezone !== deviceTz) {
        const synced = await updateNotificationSettings(telegramInitData, {
          timezone: deviceTz,
        });
        setSettings(synced);
      } else {
        setSettings(data);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить настройки",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initData) {
      void loadSettings(initData);
    } else {
      setLoading(false);
    }
  }, [initData, loadSettings]);

  async function persist(patch: Parameters<typeof updateNotificationSettings>[1]) {
    if (!initData || !settings) {
      return;
    }
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const data = await updateNotificationSettings(initData, {
        ...patch,
        timezone: getDeviceTimezone(),
      });
      setSettings(data);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
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

  const deviceTz = getDeviceTimezone();

  return (
    <ScreenLayout
      title="Уведомления"
      subtitle={`Время с устройства (${deviceTz})`}
      back={{ label: "Профиль", href: "/profile" }}
      contentClassName="space-y-5"
    >
      {error ? (
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {saved ? (
        <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          ✓ Сохранено
        </p>
      ) : null}

      <section className="rounded-2xl border border-stone-100 bg-white p-4">
        <p className="text-sm font-semibold text-stone-900">Настроить неделю</p>
        <p className="mt-1 text-xs text-stone-500">
          ПланАм присылает напоминания в Telegram. Также можно добавить событие в
          календарь устройства.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={saving}
            onClick={() =>
              void persist({
                buy_reminder_enabled: true,
                buy_reminder_time: "18:00",
                cook_dinner_enabled: true,
                cook_dinner_time: "17:30",
              })
            }
            className="rounded-lg border border-stone-200 px-3 py-2 text-xs font-semibold"
          >
            Покупки Пн/Ср/Пт 18:00
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() =>
              void persist({
                cook_breakfast_enabled: true,
                cook_lunch_enabled: true,
                cook_dinner_enabled: true,
                cook_breakfast_time: "08:00",
                cook_lunch_time: "13:00",
                cook_dinner_time: "18:00",
              })
            }
            className="rounded-lg border border-stone-200 px-3 py-2 text-xs font-semibold"
          >
            Готовка каждый день
          </button>
        </div>
        <p className="mt-2 text-[11px] text-stone-400">
          Дни недели для Telegram-рассылки настраиваются на сервере; в календарь
          можно экспортировать ближайшее событие по кнопке ниже.
        </p>
      </section>

      <ReminderCard
        emoji="🛒"
        title="Напомнить купить"
        category="Покупки"
        description="Список покупок — что ещё не отмечено купленным"
        daysLabel="каждый день (Telegram)"
        enabled={settings.buy_reminder_enabled}
        time={settings.buy_reminder_time}
        disabled={saving}
        onEnabledChange={(value) => persist({ buy_reminder_enabled: value })}
        onTimeChange={(value) => persist({ buy_reminder_time: value })}
        onAddToCalendar={() => {
          const ics = buildIcsFile([
            {
              title: "ПланАм: покупки",
              description: "Проверьте список покупок в приложении",
              start: nextOccurrence(settings.buy_reminder_time, 1),
            },
          ]);
          downloadIcs("planam-shopping.ics", ics);
        }}
      />

      <ReminderCard
        emoji="🌅"
        title="Завтрак"
        category="Готовка"
        description="Напоминание приготовить завтрак из выбранного меню"
        daysLabel="каждый день"
        enabled={settings.cook_breakfast_enabled}
        time={settings.cook_breakfast_time}
        disabled={saving}
        onEnabledChange={(value) => persist({ cook_breakfast_enabled: value })}
        onTimeChange={(value) => persist({ cook_breakfast_time: value })}
        onAddToCalendar={() => {
          downloadIcs(
            "planam-breakfast.ics",
            buildIcsFile([
              {
                title: "ПланАм: завтрак",
                start: nextOccurrence(settings.cook_breakfast_time, new Date().getDay()),
              },
            ]),
          );
        }}
      />

      <ReminderCard
        emoji="🍲"
        title="Обед"
        category="Готовка"
        description="Напоминание приготовить обед"
        daysLabel="каждый день"
        enabled={settings.cook_lunch_enabled}
        time={settings.cook_lunch_time}
        disabled={saving}
        onEnabledChange={(value) => persist({ cook_lunch_enabled: value })}
        onTimeChange={(value) => persist({ cook_lunch_time: value })}
        onAddToCalendar={() => {
          downloadIcs(
            "planam-lunch.ics",
            buildIcsFile([
              {
                title: "ПланАм: обед",
                start: nextOccurrence(settings.cook_lunch_time, new Date().getDay()),
              },
            ]),
          );
        }}
      />

      <ReminderCard
        emoji="🌙"
        title="Ужин"
        category="Готовка"
        description="Напоминание приготовить ужин"
        daysLabel="каждый день"
        enabled={settings.cook_dinner_enabled}
        time={settings.cook_dinner_time}
        disabled={saving}
        onEnabledChange={(value) => persist({ cook_dinner_enabled: value })}
        onTimeChange={(value) => persist({ cook_dinner_time: value })}
        onAddToCalendar={() => {
          downloadIcs(
            "planam-dinner.ics",
            buildIcsFile([
              {
                title: "ПланАм: ужин",
                start: nextOccurrence(settings.cook_dinner_time, new Date().getDay()),
              },
            ]),
          );
        }}
      />

      <p className="text-center text-xs text-stone-400">
        {saving
          ? "Сохранение…"
          : "Убедитесь, что бот может писать вам в личные сообщения"}
      </p>
    </ScreenLayout>
  );
}
