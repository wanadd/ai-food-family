"use client";

import { useCallback, useState } from "react";

import { useTelegram } from "@/components/TelegramProvider";
import {
  fetchNotificationSettings,
  saveNotificationOnboarding,
} from "@/lib/notifications/api";
import type {
  CareModeOption,
  NotificationOnboardingPayload,
  NotificationTypeOption,
} from "@/lib/notifications/types";

const TYPE_OPTIONS: { id: NotificationTypeOption; label: string }[] = [
  { id: "menu", label: "Готовка и меню" },
  { id: "shopping", label: "Покупки" },
  { id: "pantry", label: "Запасы" },
  { id: "water", label: "Вода и здоровье" },
  { id: "family", label: "Семья" },
];

const MODE_OPTIONS: {
  id: CareModeOption;
  label: string;
  description: string;
}[] = [
  { id: "off", label: "Без уведомлений", description: "Тихий режим" },
  {
    id: "minimal",
    label: "Только важное",
    description: "1–2 напоминания в день",
  },
  {
    id: "normal",
    label: "1–2 раза в день",
    description: "Меню, покупки, запасы",
  },
  {
    id: "active",
    label: "Активная забота",
    description: "Больше подсказок и напоминаний",
  },
];

type Props = {
  onSaved: () => void;
};

export function NotificationOnboardingPanel({ onSaved }: Props) {
  const { initData } = useTelegram();
  const [careMode, setCareMode] = useState<CareModeOption>("off");
  const [types, setTypes] = useState<NotificationTypeOption[]>([]);
  const [quietStart, setQuietStart] = useState("22:00");
  const [quietEnd, setQuietEnd] = useState("09:00");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleType = (id: NotificationTypeOption) => {
    setTypes((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id],
    );
  };

  const buildPayload = useCallback(
    (mode: CareModeOption, selected: NotificationTypeOption[]): NotificationOnboardingPayload => ({
      care_mode: mode,
      enabled_notification_types: mode === "off" ? [] : selected,
      quiet_hours_start: quietStart,
      quiet_hours_end: quietEnd,
    }),
    [quietEnd, quietStart],
  );

  const persist = async (payload: NotificationOnboardingPayload) => {
    if (!initData) return;
    setSaving(true);
    setError(null);
    try {
      await saveNotificationOnboarding(initData, payload);
      await fetchNotificationSettings(initData);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  };

  const handleSave = () => {
    void persist(buildPayload(careMode, types));
  };

  const handleSkip = () => {
    void persist(buildPayload("off", []));
  };

  return (
    <section className="rounded-card border border-pa-border bg-pa-surface p-5 shadow-soft dark:shadow-none">
      <h2 className="text-base font-bold text-pa-foreground">Настроить уведомления</h2>
      <p className="mt-2 text-sm leading-relaxed text-pa-muted">
        PLANAM может напоминать о готовке, покупках, запасах и здоровье. Выберите,
        что действительно нужно. Можно оставить всё выключенным и вернуться позже.
      </p>

      <div className="mt-4 space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-pa-muted">
          Категории
        </p>
        {TYPE_OPTIONS.map((opt) => (
          <label
            key={opt.id}
            className="flex cursor-pointer items-center gap-3 rounded-lg border border-pa-border px-3 py-2"
          >
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-pa-border"
              checked={types.includes(opt.id)}
              disabled={saving || careMode === "off"}
              onChange={() => toggleType(opt.id)}
            />
            <span className="text-sm text-pa-foreground">{opt.label}</span>
          </label>
        ))}
      </div>

      <div className="mt-5 space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-pa-muted">
          Режим
        </p>
        {MODE_OPTIONS.map((opt) => (
          <label
            key={opt.id}
            className={`flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2 ${
              careMode === opt.id
                ? "border-sage-400 bg-sage-50/40 dark:border-sage-600 dark:bg-sage-900/20"
                : "border-pa-border"
            }`}
          >
            <input
              type="radio"
              name="care_mode"
              className="mt-1"
              checked={careMode === opt.id}
              disabled={saving}
              onChange={() => setCareMode(opt.id)}
            />
            <span>
              <span className="block text-sm font-medium text-pa-foreground">
                {opt.label}
              </span>
              <span className="text-xs text-pa-muted">{opt.description}</span>
            </span>
          </label>
        ))}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <label className="block">
          <span className="text-xs font-medium text-pa-muted">Тихие часы с</span>
          <input
            type="time"
            className="mt-1 w-full rounded-lg border border-pa-border bg-pa-surface px-2 py-2 text-sm"
            value={quietStart}
            disabled={saving}
            onChange={(e) => setQuietStart(e.target.value.slice(0, 5))}
          />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-pa-muted">до</span>
          <input
            type="time"
            className="mt-1 w-full rounded-lg border border-pa-border bg-pa-surface px-2 py-2 text-sm"
            value={quietEnd}
            disabled={saving}
            onChange={(e) => setQuietEnd(e.target.value.slice(0, 5))}
          />
        </label>
      </div>

      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

      <div className="mt-5 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          className="flex-1 rounded-xl bg-sage-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
          disabled={saving}
          onClick={handleSave}
        >
          {saving ? "Сохраняем…" : "Сохранить"}
        </button>
        <button
          type="button"
          className="flex-1 rounded-xl border border-pa-border px-4 py-3 text-sm font-semibold text-pa-foreground disabled:opacity-50"
          disabled={saving}
          onClick={handleSkip}
        >
          Пока без уведомлений
        </button>
      </div>
    </section>
  );
}
