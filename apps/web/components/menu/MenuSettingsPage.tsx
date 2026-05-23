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
      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-sm font-bold text-stone-900">Персон по умолчанию</p>
        <p className="mt-1 text-sm text-stone-600">
          Автоматически: {defaultPersons}{" "}
          {defaultPersons === 1 ? "человек" : "человека"}
        </p>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={useOverride}
            onChange={(e) => setUseOverride(e.target.checked)}
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
            className="mt-2 w-full rounded-xl border border-stone-200 px-3 py-2 text-sm"
          />
        ) : null}
      </section>

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-sm font-bold text-stone-900">Режим плана</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {PLAN_MODE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setPlanMode(option.value)}
              className={`rounded-full border px-3 py-2 text-sm ${
                planMode === option.value
                  ? "border-emerald-600 bg-emerald-50 font-semibold text-emerald-900"
                  : "border-stone-200 text-stone-700"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </section>

      <p className="text-xs text-stone-500">
        ПланАм не навязывает блюда — вы всегда можете выбрать рецепты из каталога
        или заменить блюда вручную.
      </p>

      <StickyBottomBar>
        <button
          type="button"
          onClick={handleSave}
          className="w-full rounded-2xl bg-emerald-600 py-3.5 text-base font-semibold text-white"
        >
          Сохранить
        </button>
        <Link
          href="/menu/generate"
          className="mt-2 block text-center text-sm font-semibold text-emerald-700"
        >
          Составить меню →
        </Link>
      </StickyBottomBar>
    </ScreenLayout>
  );
}
