"use client";

import Link from "next/link";

import type { MenuGoalId, PlanModeId } from "@/lib/menu/planner-options";
import {
  CHECKLIST_ADD_LINKS,
  CHECKLIST_ITEMS,
  MENU_BUDGET_OPTIONS,
  MENU_DAY_OPTIONS,
  MENU_GOAL_OPTIONS,
  PLAN_MODE_OPTIONS,
} from "@/lib/menu/planner-options";
import type { ChecklistItemStatus } from "@/lib/menu/planner-summary";
import { wizardLogicalStep } from "@/lib/menu/wizard-steps";
import { MenuPlannerSection } from "@/components/menu/MenuPlannerSection";

type Props = {
  screenIndex: number;
  goal: MenuGoalId | null;
  goalError?: string | null;
  onGoalChange: (g: MenuGoalId) => void;
  personsCount: number;
  onPersonsChange: (n: number) => void;
  days: number;
  onDaysChange: (d: number) => void;
  budget: string;
  onBudgetChange: (b: string) => void;
  planMode: PlanModeId;
  onPlanModeChange: (m: PlanModeId) => void;
  checklistStatuses: Record<string, ChecklistItemStatus>;
  familyName?: string;
  isFamily: boolean;
};

function statusLabel(status: ChecklistItemStatus): string {
  if (status === "included") return "Учтено";
  if (status === "missing") return "Не заполнено";
  return "Добавить";
}

function statusClass(status: ChecklistItemStatus): string {
  if (status === "included") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (status === "missing") {
    return "bg-amber-100 text-amber-900";
  }
  return "bg-stone-100 text-emerald-800";
}

export function MenuWizardSteps({
  screenIndex,
  goal,
  goalError,
  onGoalChange,
  personsCount,
  onPersonsChange,
  days,
  onDaysChange,
  budget,
  onBudgetChange,
  planMode,
  onPlanModeChange,
  checklistStatuses,
  familyName,
  isFamily,
}: Props) {
  const step = wizardLogicalStep(screenIndex, isFamily);

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
        {goalError ? (
          <p className="mt-3 text-sm font-medium text-red-700" role="alert">
            {goalError}
          </p>
        ) : null}
        <p className="mt-3 text-xs text-stone-500">
          {goal
            ? "Нажмите «Продолжить» внизу экрана"
            : "Выберите цель, затем нажмите «Продолжить»"}
        </p>
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
      <MenuPlannerSection title={`Шаг ${isFamily ? 3 : 2} · На сколько дней`}>
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
      <MenuPlannerSection title={`Шаг ${isFamily ? 4 : 3} · Бюджет`}>
        <div className="grid gap-2">
          {MENU_BUDGET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onBudgetChange(opt.value)}
              className={`rounded-xl border px-4 py-3 text-left text-sm font-medium ${
                budget === opt.value
                  ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                  : "border-stone-200 bg-white text-stone-800"
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
    <MenuPlannerSection title={`Шаг ${isFamily ? 5 : 4} · Что учтёт ПланАм`}>
      <ul className="space-y-2">
        {CHECKLIST_ITEMS.filter((item) => isFamily || item.id !== "persons").map(
          (item) => {
            const status = checklistStatuses[item.id] ?? "missing";
            const href = CHECKLIST_ADD_LINKS[item.id];
            return (
              <li
                key={item.id}
                className="flex items-center justify-between gap-2 text-sm text-stone-700"
              >
                <span>{item.label}</span>
                {status === "add" && href ? (
                  <Link
                    href={href}
                    className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusClass(status)}`}
                  >
                    {statusLabel(status)}
                  </Link>
                ) : (
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusClass(status)}`}
                  >
                    {statusLabel(status)}
                  </span>
                )}
              </li>
            );
          },
        )}
      </ul>
      {!isFamily ? (
        <p className="mt-2 text-xs text-stone-500">Персон: 1 (личный режим)</p>
      ) : null}
      <p className="mt-3 text-xs text-stone-500">
        Период: {days} {days === 1 ? "день" : days < 5 ? "дня" : "дней"}
      </p>
    </MenuPlannerSection>
  );
}
