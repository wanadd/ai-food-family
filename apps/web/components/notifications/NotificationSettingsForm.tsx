"use client";

import { useCallback, useEffect, useState } from "react";

import { useTelegram } from "@/components/TelegramProvider";

import {
  cacheKey,
  getCached,
  setCached,
} from "@/lib/cache/session-cache";
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
      className={`rounded-card border p-5 shadow-soft transition dark:shadow-none ${
        enabled
          ? "border-sage-200 bg-sage-50/30 dark:border-sage-700/40 dark:bg-sage-900/20"
          : "border-pa-border bg-pa-surface"
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl" aria-hidden>
          {emoji}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-pa-foreground">{title}</h3>
            <label className="relative inline-flex cursor-pointer items-center">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={enabled}
                disabled={disabled}
                onChange={(e) => onEnabledChange(e.target.checked)}
              />
              <span className="h-7 w-12 rounded-full bg-cream-deep transition peer-checked:bg-sage-600 peer-disabled:opacity-50 dark:bg-pa-elevated" />
              <span className="absolute left-0.5 top-0.5 h-6 w-6 rounded-full bg-pa-surface shadow-soft transition peer-checked:translate-x-5" />
            </label>
          </div>
          <p className="mt-1 text-sm text-pa-muted">{description}</p>
          <p className="mt-1 text-xs text-pa-muted">
            {category} · {daysLabel}
          </p>
          {enabled ? (
            <>
              <label className="mt-4 block">
                <span className="text-xs font-medium text-pa-muted">Время</span>
                <input
                  type="time"
                  value={time}
                  disabled={disabled}
                  onChange={(e) => onTimeChange(e.target.value)}
                  className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 text-base text-pa-foreground focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
                />
              </label>
              <button
                type="button"
                disabled={disabled}
                onClick={onAddToCalendar}
                className="mt-3 w-full rounded-control border border-pa-border bg-pa-surface py-2.5 text-sm font-semibold text-pa-foreground"
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
  const cached = initData
    ? getCached<NotificationSettings>(cacheKey.notificationSettings())
    : null;
  const [settings, setSettings] = useState<NotificationSettings | null>(cached);
  const [loading, setLoading] = useState(cached == null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const loadSettings = useCallback(async (telegramInitData: string) => {
    const primed = getCached<NotificationSettings>(
      cacheKey.notificationSettings(),
    );
    if (primed) {
      setSettings(primed);
      setLoading(false);
    } else {
      setLoading(true);
    }
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
        setCached(cacheKey.notificationSettings(), synced);
        setSettings(synced);
      } else {
        setCached(cacheKey.notificationSettings(), data);
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
      setCached(cacheKey.notificationSettings(), data);
      setSettings(data);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  if (!initData) {
    return null;
  }

  if (loading || !settings) {
    return (
      <p className="py-10 text-center text-sm text-pa-muted">
        Загрузка расписания…
      </p>
    );
  }

  const deviceTz = getDeviceTimezone();

  return (
    <div className="space-y-5">
      {error ? (
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {saved ? (
        <p className="rounded-control border border-sage-200 bg-sage-50 px-4 py-3 text-sm text-sage-800">
          ✓ Сохранено
        </p>
      ) : null}

      <details className="group rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <summary className="cursor-pointer list-none">
          <span className="flex items-center justify-between">
            <span className="text-sm font-bold text-pa-foreground">
              Готовка и покупки по расписанию
            </span>
            <span className="text-xs text-pa-muted group-open:rotate-180 transition">
              ▼
            </span>
          </span>
          <span className="mt-0.5 block text-xs text-pa-muted">
            Время — с вашего устройства ({deviceTz})
          </span>
        </summary>
        <p className="mt-3 text-xs text-pa-muted">
          Если удобно, добавьте событие в календарь телефона.
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
            className="rounded-pill bg-cream-deep px-3 py-2 text-xs font-semibold text-pa-foreground dark:bg-pa-elevated"
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
            className="rounded-pill bg-cream-deep px-3 py-2 text-xs font-semibold text-pa-foreground dark:bg-pa-elevated"
          >
            Готовка каждый день
          </button>
        </div>
        <p className="mt-2 text-[11px] text-pa-muted">
          Дни недели для Telegram-рассылки настраиваются на сервере; в календарь
          можно экспортировать ближайшее событие по кнопке ниже.
        </p>

        <div className="mt-4 space-y-3">

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

        </div>
      </details>

      <p className="text-center text-xs text-pa-muted">
        {saving
          ? "Сохраняем…"
          : "Чтобы напоминания приходили, разрешите боту писать вам в Telegram."}
      </p>
    </div>
  );
}
