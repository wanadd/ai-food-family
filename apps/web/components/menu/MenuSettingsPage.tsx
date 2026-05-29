"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { StickyBottomBar } from "@/components/layout/StickyBottomBar";
import { useTelegram } from "@/components/TelegramProvider";
import { PLAN_MODE_OPTIONS, type PlanModeId } from "@/lib/menu/planner-options";
import {
  loadPersonsOverride,
  loadPlanMode,
  clearPersonsOverride,
  savePersonsOverride,
  savePlanMode,
} from "@/lib/menu/planner-storage";

export function MenuSettingsPage() {
  const { mode, context } = useAppMode();
  const defaultPersons =
    mode === "family" && context?.family
      ? context.family.members_count ?? context.family.members.length
      : 1;

  const [planMode, setPlanMode] = useState<PlanModeId>("healthy");
  const [personsOverride, setPersonsOverride] = useState<number | null>(null);
  const [useOverride, setUseOverride] = useState(false);

  useEffect(() => {
    const stored = loadPlanMode() as PlanModeId | null;
    if (stored && PLAN_MODE_OPTIONS.some((o) => o.value === stored)) {
      setPlanMode(stored);
    }
    const persons = loadPersonsOverride();
    if (persons !== null) {
      setPersonsOverride(persons);
      setUseOverride(true);
    }
  }, []);

  function handleSave() {
    savePlanMode(planMode);
    if (useOverride && personsOverride !== null) {
      savePersonsOverride(personsOverride);
    } else {
      clearPersonsOverride();
    }
  }

  return (
    <ScreenLayout
      title="Настройки меню"
      subtitle="Режим генерации и порции"
      back={{ label: "Меню", href: "/menu" }}
      contentClassName="space-y-3"
    >
      <section className="pa-card p-4">
        <p className="text-sm font-bold text-graphite-900">Персон по умолчанию</p>
        <p className="mt-1 text-sm text-graphite-600">
          Автоматически: {defaultPersons}{" "}
          {defaultPersons === 1 ? "человек" : "человека"}
        </p>
        <label className="mt-3 flex items-center gap-2 text-sm text-graphite-800">
          <input
            type="checkbox"
            checked={useOverride}
            onChange={(e) => setUseOverride(e.target.checked)}
            className="rounded border-cream-border text-sage-600 focus:ring-sage-400"
          />
          Временно задать другое число при генерации
        </label>
        {useOverride ? (
          <input
            type="number"
            min={1}
            max={20}
            value={personsOverride ?? defaultPersons}
            onChange={(e) =>
              setPersonsOverride(parseInt(e.target.value, 10) || defaultPersons)
            }
            className="mt-2 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2 text-sm text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          />
        ) : null}
      </section>

      <section className="pa-card p-4">
        <p className="text-sm font-bold text-graphite-900">Режим плана</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {PLAN_MODE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setPlanMode(option.value)}
              className={`pa-chip ${
                planMode === option.value
                  ? "border-sage-500 bg-sage-50 font-semibold text-sage-900"
                  : "border-cream-border text-graphite-700"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </section>

      <p className="text-xs text-graphite-500">
        ПланАм не навязывает блюда — вы всегда можете выбрать рецепты из каталога
        или заменить блюда вручную.
      </p>

      <StickyBottomBar>
        <button
          type="button"
          onClick={handleSave}
          className="pa-btn-primary w-full py-3.5 text-base"
        >
          Сохранить
        </button>
        <Link
          href="/menu/generate"
          className="mt-2 block text-center text-sm font-semibold text-sage-700"
        >
          Составить меню →
        </Link>
      </StickyBottomBar>
    </ScreenLayout>
  );
}
