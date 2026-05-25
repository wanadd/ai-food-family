"use client";

import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  setCached,
} from "@/lib/cache/session-cache";
import {
  fetchCareSettings,
  sendTestCareNotification,
  updateCareSettings,
} from "@/lib/care/api";
import type {
  CareLevel,
  CareSettings,
  CareSettingsUpdate,
} from "@/lib/care/types";

const CARE_MODES: {
  value: CareLevel;
  label: string;
  description: string;
  frequency: string;
  examples: string[];
}[] = [
  {
    value: "minimal",
    label: "Только важное",
    description: "Покупки · Меню · Запасы",
    frequency: "1–3 уведомления в день",
    examples: [
      "«Не забудьте синхронизировать список покупок»",
      "«Меню на завтра готово — откройте план»",
      "«В запасах заканчивается молоко»",
    ],
  },
  {
    value: "standard",
    label: "Баланс",
    description: "Вода · Белок · Прогресс · Полезные привычки",
    frequency: "3–6 уведомлений в день",
    examples: [
      "«Выпейте стакан воды — осталось 500 мл до нормы»",
      "«Добавьте белок к ужину»",
      "«Отметьте вес — так точнее прогноз цели»",
    ],
  },
  {
    value: "active",
    label: "Персональный коуч PRO",
    description: "Питание · Тренировки · Прогресс · Персональные советы",
    frequency: "до 10 уведомлений в день",
    examples: [
      "«После тренировки — перекус с белком»",
      "«По плану сегодня лёгкий ужин»",
      "«Прогресс к цели: −0,3 кг за неделю»",
    ],
  },
];

const TOGGLE_ITEMS: {
  key: keyof CareSettings;
  label: string;
}[] = [
  { key: "water_enabled", label: "Вода" },
  { key: "protein_enabled", label: "Белок" },
  { key: "menu_enabled", label: "Меню" },
  { key: "shopping_enabled", label: "Покупки" },
  { key: "pantry_enabled", label: "Запасы" },
  { key: "family_enabled", label: "Семья" },
  { key: "progress_enabled", label: "Прогресс" },
  { key: "pro_enabled", label: "Тренировки" },
];

export function CareSettingsPanel() {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const cached = initData
    ? getCached<CareSettings>(cacheKey.careSettings(mode))
    : null;
  const [settings, setSettings] = useState<CareSettings | null>(cached);
  const [loading, setLoading] = useState(cached == null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    const primed = getCached<CareSettings>(cacheKey.careSettings(mode));
    if (primed) {
      setSettings(primed);
      setLoading(false);
    } else {
      setLoading(true);
    }
    try {
      const data = await fetchCareSettings(initData, mode);
      setCached(cacheKey.careSettings(mode), data);
      setSettings(data);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function patch(partial: CareSettingsUpdate) {
    if (!initData || !settings) return;
    const previous = settings;
    setSettings((current) => (current ? { ...current, ...partial } : current));
    setSaving(true);
    setFeedback(null);
    try {
      const updated = await updateCareSettings(initData, mode, partial);
      setCached(cacheKey.careSettings(mode), updated);
      setSettings(updated);
      setFeedback("✓ Сохранено");
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
    return <p className="text-sm text-stone-500">Загрузка…</p>;
  }

  if (!settings) {
    return (
      <p className="text-sm text-stone-500">
        Настройки доступны в Telegram Mini App
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-bold text-stone-900">Режим заботы</h2>
        <div className="mt-3 space-y-2">
          {CARE_MODES.map((modeOption) => (
            <button
              key={modeOption.value}
              type="button"
              disabled={saving}
              onClick={() => void patch({ care_level: modeOption.value })}
              className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                settings.care_level === modeOption.value
                  ? "border-emerald-600 bg-emerald-50"
                  : "border-stone-200 bg-white"
              }`}
            >
              <p className="font-semibold text-stone-900">{modeOption.label}</p>
              <p className="mt-0.5 text-xs text-stone-600">{modeOption.description}</p>
              <p className="mt-1 text-[11px] font-medium text-emerald-700">
                {modeOption.frequency}
              </p>
              <ul className="mt-2 space-y-1 border-t border-stone-100 pt-2">
                {modeOption.examples.map((ex) => (
                  <li key={ex} className="text-[11px] leading-snug text-stone-500">
                    {ex}
                  </li>
                ))}
              </ul>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-bold text-stone-900">Что напоминать</h2>
        <p className="mt-1 text-xs text-stone-500">
          Если что-то не нужно — отключите. Можно вернуть в любой момент.
        </p>
        <ul className="mt-3 space-y-2">
          {TOGGLE_ITEMS.map((item) => {
            const isPro = item.key === "pro_enabled";
            const locked = isPro && !settings.has_pro_plan;
            const checked = Boolean(settings[item.key]);
            const disabledByMinimal =
              settings.care_level === "minimal" &&
              !["menu_enabled", "shopping_enabled", "pantry_enabled"].includes(
                item.key,
              );

            return (
              <li
                key={item.key}
                className={`flex items-center justify-between rounded-xl px-3 py-2.5 ${
                  disabledByMinimal || locked
                    ? "bg-stone-50/60 opacity-70"
                    : "bg-stone-50"
                }`}
              >
                <span className="text-sm font-medium text-stone-800">
                  {item.label}
                  {locked ? (
                    <span className="ml-2 text-[10px] font-bold text-stone-400">
                      PRO
                    </span>
                  ) : null}
                </span>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={saving || locked || disabledByMinimal}
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
      </section>

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-bold text-stone-900">Тихие часы</h2>
        <p className="mt-1 text-xs text-stone-500">
          В это время ПланАм ничего не присылает. Если оставить пустым — сообщения
          могут приходить в любое время.
        </p>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs font-medium text-stone-600">С</span>
            <input
              type="time"
              value={settings.quiet_hours_start ?? ""}
              disabled={saving}
              onChange={(e) =>
                void patch({ quiet_hours_start: e.target.value || null })
              }
              className="mt-1 w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-base"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-stone-600">До</span>
            <input
              type="time"
              value={settings.quiet_hours_end ?? ""}
              disabled={saving}
              onChange={(e) =>
                void patch({ quiet_hours_end: e.target.value || null })
              }
              className="mt-1 w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-base"
            />
          </label>
        </div>
        {settings.quiet_hours_start && settings.quiet_hours_end ? (
          <p className="mt-2 text-[11px] text-stone-500">
            С {settings.quiet_hours_start} до {settings.quiet_hours_end} ПланАм
            будет молчать.
          </p>
        ) : (
          <button
            type="button"
            disabled={saving}
            onClick={() =>
              void patch({
                quiet_hours_start: "22:00",
                quiet_hours_end: "08:00",
              })
            }
            className="mt-3 inline-flex items-center justify-center rounded-lg border border-stone-200 bg-white px-3 py-2 text-xs font-semibold text-stone-700"
          >
            Поставить 22:00–08:00
          </button>
        )}
      </section>

      {feedback ? (
        <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {feedback}
        </p>
      ) : null}

      <button
        type="button"
        disabled={testing}
        onClick={() => void handleTest()}
        className="w-full min-h-[48px] rounded-xl border border-emerald-200 bg-emerald-50 py-3 text-sm font-semibold text-emerald-800"
      >
        {testing ? "Отправляем…" : "Тестовое уведомление в Telegram"}
      </button>
    </div>
  );
}
