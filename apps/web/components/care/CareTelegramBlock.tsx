"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  fetchCareSettings,
  sendTestCareNotification,
  updateCareSettings,
} from "@/lib/care/api";
import type {
  CareLevel,
  CareNotificationType,
  CareSettings,
  CareSettingsUpdate,
} from "@/lib/care/types";

const TOGGLE_ITEMS: { key: keyof CareSettings; label: string; type?: CareNotificationType }[] = [
  { key: "water_enabled", label: "Вода", type: "water" },
  { key: "protein_enabled", label: "Белок", type: "protein" },
  { key: "menu_enabled", label: "Меню", type: "menu" },
  { key: "shopping_enabled", label: "Покупки", type: "shopping" },
  { key: "pantry_enabled", label: "Запасы", type: "pantry" },
  { key: "progress_enabled", label: "Прогресс", type: "progress" },
  { key: "family_enabled", label: "Семья", type: "family" },
  { key: "pro_enabled", label: "PRO", type: "pro" },
];

const CARE_LEVELS: { value: CareLevel; label: string; hint: string }[] = [
  {
    value: "minimal",
    label: "Минимальный",
    hint: "Только важное: меню, покупки, запасы",
  },
  {
    value: "standard",
    label: "Стандартный",
    hint: "Обычные мягкие напоминания",
  },
  {
    value: "active",
    label: "Активный",
    hint: "Больше подсказок, если вы готовы",
  },
];

type CareTelegramBlockProps = {
  compact?: boolean;
  showSettingsLink?: boolean;
};

export function CareTelegramBlock({
  compact = false,
  showSettingsLink = true,
}: CareTelegramBlockProps) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [settings, setSettings] = useState<CareSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchCareSettings(initData, mode);
      setSettings(data);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function patch(partial: Parameters<typeof updateCareSettings>[2]) {
    if (!initData || !settings) return;
    const previous = settings;
    setSettings((current) => (current ? { ...current, ...partial } : current));
    setSaving(true);
    setFeedback(null);
    try {
      const updated = await updateCareSettings(initData, mode, partial);
      setSettings(updated);
    } catch (err) {
      setSettings(previous);
      setFeedback(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    if (!initData) return;
    setTesting(true);
    setFeedback(null);
    try {
      const res = await sendTestCareNotification(initData, mode, "water");
      setFeedback(res.message);
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "Не удалось отправить");
    } finally {
      setTesting(false);
    }
  }

  if (loading) {
    return (
      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-sm text-stone-500">Загрузка настроек заботы…</p>
      </section>
    );
  }

  if (!settings) {
    return (
      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-sm text-stone-500">
          Настройки заботы доступны в Telegram Mini App
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-sm font-bold text-stone-900">Забота в Telegram</h2>
          <p className="mt-0.5 text-xs text-stone-500">
            ПланАм будет мягко напоминать о важном
          </p>
        </div>
        {showSettingsLink && !compact ? (
          <Link
            href="/settings/care"
            className="shrink-0 text-xs font-semibold text-emerald-700"
          >
            Подробнее
          </Link>
        ) : null}
      </div>

      <div className="mt-3">
        <p className="text-xs font-semibold text-stone-500">Уровень заботы</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {CARE_LEVELS.map((level) => (
            <button
              key={level.value}
              type="button"
              disabled={saving}
              onClick={() => void patch({ care_level: level.value })}
              className={`rounded-full border px-3 py-2 text-left text-sm transition ${
                settings.care_level === level.value
                  ? "border-emerald-600 bg-emerald-50 font-semibold text-emerald-900"
                  : "border-stone-200 text-stone-700"
              }`}
            >
              {level.label}
            </button>
          ))}
        </div>
        <p className="mt-1.5 text-[11px] text-stone-500">
          {CARE_LEVELS.find((l) => l.value === settings.care_level)?.hint}
        </p>
      </div>

      <ul className="mt-3 space-y-2">
        {TOGGLE_ITEMS.map((item) => {
          const isPro = item.key === "pro_enabled";
          const locked = isPro && !settings.has_pro_plan;
          const checked = Boolean(settings[item.key]);

          if (locked) {
            return (
              <li
                key={item.key}
                className="rounded-xl border border-stone-200 bg-stone-50/90 px-3 py-2.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-stone-600">
                    {item.label}
                  </span>
                  <span className="text-[10px] font-bold uppercase text-stone-400">
                    PRO
                  </span>
                </div>
                <p className="mt-1 text-xs text-stone-500">
                  Доступно в ПланАм PRO
                </p>
                <Link
                  href="/subscription"
                  className="mt-2 inline-block text-xs font-semibold text-emerald-700"
                >
                  Узнать о PRO
                </Link>
              </li>
            );
          }

          const disabledByMinimal =
            settings.care_level === "minimal" &&
            !["menu_enabled", "shopping_enabled", "pantry_enabled"].includes(
              item.key,
            );

          return (
            <li
              key={item.key}
              className={`flex items-center justify-between rounded-xl px-3 py-2.5 ${
                disabledByMinimal ? "bg-stone-50/50 opacity-60" : "bg-stone-50"
              }`}
            >
              <span className="text-sm font-medium text-stone-800">
                {item.label}
              </span>
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={saving || disabledByMinimal}
                  onChange={() =>
                    void patch({ [item.key]: !checked } as CareSettingsUpdate)
                  }
                  className="peer sr-only"
                />
                <span className="h-6 w-10 rounded-full bg-stone-200 transition peer-checked:bg-emerald-500 peer-disabled:opacity-50" />
                <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition peer-checked:translate-x-4" />
              </label>
            </li>
          );
        })}
      </ul>

      {feedback ? (
        <p
          className={`mt-3 rounded-lg px-3 py-2 text-sm ${
            feedback.includes("отправлен")
              ? "bg-emerald-50 text-emerald-900"
              : "bg-amber-50 text-amber-900"
          }`}
        >
          {feedback}
        </p>
      ) : null}

      <button
        type="button"
        disabled={testing || !initData}
        onClick={() => void handleTest()}
        className="mt-3 w-full min-h-[44px] rounded-xl border border-emerald-200 bg-emerald-50 py-2.5 text-sm font-semibold text-emerald-800 disabled:opacity-50"
      >
        {testing ? "Отправляем…" : "Отправить тестовое уведомление"}
      </button>
    </section>
  );
}
