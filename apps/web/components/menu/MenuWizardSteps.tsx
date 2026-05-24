"use client";

import type { MenuGoalId, PlanModeId } from "@/lib/menu/planner-options";
import {
  CHECKLIST_ITEMS,
  MENU_BUDGET_OPTIONS,
  MENU_DAY_OPTIONS,
  MENU_GOAL_OPTIONS,
  PLAN_MODE_OPTIONS,
} from "@/lib/menu/planner-options";
import { MenuPlannerSection } from "@/components/menu/MenuPlannerSection";

type Props = {
  step: number;
  goal: MenuGoalId;
  onGoalChange: (g: MenuGoalId) => void;
  personsCount: number;
  onPersonsChange: (n: number) => void;
  days: number;
  onDaysChange: (d: number) => void;
  budget: string;
  onBudgetChange: (b: string) => void;
  planMode: PlanModeId;
  onPlanModeChange: (m: PlanModeId) => void;
  checklist: Record<string, boolean>;
  familyName?: string;
  isFamily: boolean;
};

export function MenuWizardSteps({
  step,
  goal,
  onGoalChange,
  personsCount,
  onPersonsChange,
  days,
  onDaysChange,
  budget,
  onBudgetChange,
  planMode,
  onPlanModeChange,
  checklist,
  familyName,
  isFamily,
}: Props) {
  if (step === 0) {
    return (
      <MenuPlannerSection title="Шаг 1 · Цель">
        <div className="grid gap-2">
          {MENU_GOAL_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onGoalChange(opt.value)}
              className={`rounded-xl border px-4 py-3 text-left text-sm font-medium ${
                goal === opt.value
                  ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                  : "border-stone-200 bg-white text-stone-800"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </MenuPlannerSection>
    );
  }

  if (step === 1) {
    return (
      <MenuPlannerSection title="Шаг 2 · Количество человек">
        {isFamily && familyName ? (
          <p className="mb-2 text-sm text-stone-600">Семья: {familyName}</p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => onPersonsChange(n)}
              className={`min-h-[44px] min-w-[44px] rounded-xl border text-sm font-semibold ${
                personsCount === n
                  ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                  : "border-stone-200 bg-white"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </MenuPlannerSection>
    );
  }

  if (step === 2) {
    return (
      <MenuPlannerSection title="Шаг 3 · На сколько дней">
        <div className="grid grid-cols-3 gap-2">
          {MENU_DAY_OPTIONS.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => onDaysChange(d)}
              className={`min-h-[44px] rounded-xl border text-sm font-semibold ${
                days === d
                  ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                  : "border-stone-200 bg-white"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </MenuPlannerSection>
    );
  }

  if (step === 3) {
    return (
      <MenuPlannerSection title="Шаг 4 · Бюджет">
        <div className="grid gap-2">
          {MENU_BUDGET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onBudgetChange(opt.value)}
              className={`rounded-xl border px-4 py-3 text-left text-sm font-medium ${
                budget === opt.value
                  ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                  : "border-stone-200 bg-white"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <p className="mt-3 text-xs text-stone-500">Режим плана:</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {PLAN_MODE_OPTIONS.slice(0, 4).map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onPlanModeChange(opt.value)}
              className={`rounded-full border px-3 py-1.5 text-xs ${
                planMode === opt.value
                  ? "border-emerald-600 bg-emerald-50 font-semibold"
                  : "border-stone-200"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </MenuPlannerSection>
    );
  }

  return (
    <MenuPlannerSection title="Шаг 5 · Что учтёт ПланАм">
      <ul className="space-y-2">
        {CHECKLIST_ITEMS.map((item) => (
          <li key={item.id} className="flex items-center gap-2 text-sm text-stone-700">
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs ${
                checklist[item.id]
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-stone-100 text-stone-400"
              }`}
            >
              {checklist[item.id] ? "✓" : "·"}
            </span>
            {item.label}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-stone-500">
        Период: {days} {days === 1 ? "день" : days < 5 ? "дня" : "дней"}
      </p>
    </MenuPlannerSection>
  );
}
