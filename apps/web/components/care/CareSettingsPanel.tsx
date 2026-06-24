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
}[] = [
  {
    value: "minimal",
    label: "Только важное",
    description: "Покупки, меню и запасы",
  },
  {
    value: "standard",
    label: "Баланс",
    description: "Вода, питание и полезные привычки",
  },
  {
    value: "active",
    label: "PRO",
    description: "Тренировки, КБЖУ и персональные советы",
  },
];

const PRIMARY_TOGGLES: {
  key: keyof CareSettings;
  label: string;
}[] = [
  { key: "shopping_enabled", label: "Покупки" },
  { key: "menu_enabled", label: "Готовка" },
  { key: "water_enabled", label: "Вода" },
  { key: "protein_enabled", label: "Питание" },
  { key: "pantry_enabled", label: "Запасы" },
];

const EXTRA_TOGGLES: {
  key: keyof CareSettings;
  label: string;
}[] = [
  { key: "family_enabled", label: "Семья" },
  { key: "progress_enabled", label: "Прогресс" },
  { key: "pro_enabled", label: "Тренировки" },
];

function CareToggleRow({
  item,
  settings,
  saving,
  onPatch,
}: {
  item: { key: keyof CareSettings; label: string };
  settings: CareSettings;
  saving: boolean;
  onPatch: (partial: CareSettingsUpdate) => void;
}) {
  const isPro = item.key === "pro_enabled";
  const locked = isPro && !settings.has_pro_plan;
  const checked = Boolean(settings[item.key]);
  const disabledByMinimal =
    settings.care_level === "minimal" &&
    !["menu_enabled", "shopping_enabled", "pantry_enabled"].includes(item.key);

  return (
    <li
      className={`flex items-center justify-between rounded-control px-3 py-2.5 ${
        disabledByMinimal || locked
          ? "bg-cream-deep/50 opacity-70 dark:bg-pa-elevated/40"
          : "bg-cream-deep/40 dark:bg-pa-elevated/40"
      }`}
    >
      <span className="text-sm font-medium text-pa-foreground">
        {item.label}
        {locked ? (
          <span className="ml-2 text-[10px] font-bold text-pa-muted">PRO</span>
        ) : null}
      </span>
      <label className="relative inline-flex cursor-pointer items-center">
        <input
          type="checkbox"
          checked={checked}
          disabled={saving || locked || disabledByMinimal}
          onChange={() => onPatch({ [item.key]: !checked } as CareSettingsUpdate)}
          className="peer sr-only"
        />
        <span className="h-6 w-10 rounded-full bg-cream-deep transition peer-checked:bg-sage-500 peer-disabled:opacity-50" />
        <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-cream-surface shadow transition peer-checked:translate-x-4" />
      </label>
    </li>
  );
}

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
    return <p className="text-sm text-pa-muted">Загрузка…</p>;
  }

  if (!settings) {
    return (
      <p className="text-sm text-pa-muted">
        Настройки доступны в Telegram Mini App
      </p>
    );
  }

  const quietRange =
    settings.quiet_hours_start && settings.quiet_hours_end
      ? `${settings.quiet_hours_start} — ${settings.quiet_hours_end}`
      : null;

  return (
    <div className="space-y-4">
      {feedback ? (
        <p className="text-xs font-medium text-sage-800">{feedback}</p>
      ) : null}

      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <h2 className="text-sm font-bold text-pa-foreground">Режим заботы</h2>
        <p className="mt-0.5 text-xs text-pa-muted">
          Сколько напоминаний присылать в Telegram
        </p>
        <div className="mt-3 space-y-2">
          {CARE_MODES.map((modeOption) => (
            <button
              key={modeOption.value}
              type="button"
              disabled={saving}
              onClick={() => void patch({ care_level: modeOption.value })}
              className={`w-full rounded-control border px-4 py-3 text-left transition ${
                settings.care_level === modeOption.value
                  ? "border-sage-500 bg-sage-50"
                  : "border-pa-border bg-pa-surface"
              }`}
            >
              <p className="font-semibold text-pa-foreground">{modeOption.label}</p>
              <p className="mt-0.5 text-xs text-pa-muted">{modeOption.description}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <h2 className="text-sm font-bold text-pa-foreground">Что напоминать</h2>
        <ul className="mt-3 space-y-2">
          {PRIMARY_TOGGLES.map((item) => (
            <CareToggleRow
              key={item.key}
              item={item}
              settings={settings}
              saving={saving}
              onPatch={(partial) => void patch(partial)}
            />
          ))}
        </ul>

        <details className="group mt-3">
          <summary className="cursor-pointer list-none text-xs font-semibold text-pa-muted">
            Ещё напоминания
          </summary>
          <ul className="mt-2 space-y-2">
            {EXTRA_TOGGLES.map((item) => (
              <CareToggleRow
                key={item.key}
                item={item}
                settings={settings}
                saving={saving}
                onPatch={(partial) => void patch(partial)}
              />
            ))}
          </ul>
        </details>
      </section>

      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <h2 className="text-sm font-bold text-pa-foreground">Тихие часы</h2>
        <p className="mt-0.5 text-xs text-pa-muted">
          {quietRange ?? "ПланАм может писать в любое время"}
        </p>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs font-medium text-pa-muted">С</span>
            <input
              type="time"
              value={settings.quiet_hours_start ?? ""}
              disabled={saving}
              onChange={(e) =>
                void patch({ quiet_hours_start: e.target.value || null })
              }
              className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 text-base text-pa-foreground focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-pa-muted">До</span>
            <input
              type="time"
              value={settings.quiet_hours_end ?? ""}
              disabled={saving}
              onChange={(e) =>
                void patch({ quiet_hours_end: e.target.value || null })
              }
              className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 text-base text-pa-foreground focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
            />
          </label>
        </div>
        {!quietRange ? (
          <button
            type="button"
            disabled={saving}
            onClick={() =>
              void patch({
                quiet_hours_start: "22:00",
                quiet_hours_end: "08:00",
              })
            }
            className="mt-3 inline-flex items-center justify-center rounded-control border border-pa-border bg-pa-surface px-3 py-2 text-xs font-semibold text-pa-foreground"
          >
            Поставить 22:00 — 08:00
          </button>
        ) : null}
      </section>

      <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
        <h2 className="text-sm font-bold text-pa-foreground">Проверка</h2>
        <p className="mt-0.5 text-xs text-pa-muted">
          Отправим тестовое сообщение в Telegram
        </p>
        <button
          type="button"
          disabled={testing}
          onClick={() => void handleTest()}
          className="mt-3 w-full min-h-[48px] rounded-control border border-sage-200 bg-sage-50 py-3 text-sm font-semibold text-sage-800"
        >
          {testing ? "Отправляем…" : "Тестовое уведомление"}
        </button>
      </section>
    </div>
  );
}
