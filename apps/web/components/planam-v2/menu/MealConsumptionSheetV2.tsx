"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
} from "@/components/planam-v2/ui/V2Primitives";
import { menuMealHeading } from "@/lib/menu/meal-heading";
import {
  fetchMealConsumptionLogs,
  mealConsumptionErrorMessage,
  saveMealConsumptionLogs,
} from "@/lib/plan/meal-consumption-api";
import {
  applyConsumptionLogsToDrafts,
  buildConsumptionMemberTargets,
  buildConsumptionSaveEntries,
  buildDefaultConsumptionDrafts,
  hasSaveableConsumptionDrafts,
  MEAL_CONSUMPTION_MEMBER_PROMPT,
  MEAL_CONSUMPTION_PORTION_OPTIONS,
  MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
  MEAL_CONSUMPTION_SAVING_LABEL,
  MEAL_CONSUMPTION_SHEET_SUBTITLE,
  MEAL_CONSUMPTION_SHEET_TITLE,
  MEAL_CONSUMPTION_STATUS_OPTIONS,
  mealConsumptionKey,
  resolveConsumptionTargets,
  shouldShowConsumptionMemberPicker,
  type ConsumptionDraft,
  type ConsumptionTargetId,
} from "@/lib/plan/meal-consumption-sheet";
import { mealTypeLabel } from "@/lib/plan/plan-today";
import type { PlanTodayMeal } from "@/lib/plan/plan-today";
import { cn } from "@/lib/planam/cn";

type MealConsumptionSheetV2Props = {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
  meals: PlanTodayMeal[];
  familyId: number | null;
  menuSelectionId: number | null;
  dayIndex: number;
  plannedDate: string | null;
};

function MealSelectionToggle({
  checked,
  onChange,
  mealLabel,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  mealLabel: string;
}) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      aria-label={`Включить в отметку: ${mealLabel}`}
      onClick={() => onChange(!checked)}
      className={cn(
        "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full border-2 transition",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400/60",
        checked
          ? "border-sage-500 bg-sage-500 text-white shadow-sm dark:border-sage-400 dark:bg-sage-400"
          : "border-sage-200 bg-sage-50/80 text-transparent dark:border-sage-700/50 dark:bg-sage-900/20",
      )}
    >
      <span aria-hidden className="text-xs font-bold leading-none">
        ✓
      </span>
    </button>
  );
}

export function MealConsumptionSheetV2({
  open,
  onClose,
  onSaved,
  meals,
  familyId,
  menuSelectionId,
  dayIndex,
  plannedDate,
}: MealConsumptionSheetV2Props) {
  const { initData } = useTelegram();
  const { mode, context } = useAppMode();
  const [targetId, setTargetId] = useState<ConsumptionTargetId>("self");
  const [drafts, setDrafts] = useState<Record<string, ConsumptionDraft>>({});
  const [logs, setLogs] = useState<
    Awaited<ReturnType<typeof fetchMealConsumptionLogs>>
  >([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const familyMembers = useMemo(() => {
    if (!context?.family?.members?.length) {
      return [];
    }
    return context.family.members;
  }, [context]);

  const isFamilyAdmin = context?.family?.your_role === "admin";
  const memberTargets = useMemo(
    () => buildConsumptionMemberTargets(familyMembers, isFamilyAdmin),
    [familyMembers, isFamilyAdmin],
  );
  const showMemberPicker = shouldShowConsumptionMemberPicker(
    familyMembers,
    isFamilyAdmin,
  );

  const mealInputs = useMemo(
    () =>
      meals.map((item) => ({
        meal_type: item.meal.meal_type,
        recipe_id: item.meal.recipe_id ?? null,
        recipe_title: menuMealHeading(item.meal),
        mealIndex: item.mealIndex,
      })),
    [meals],
  );

  const consumptionTargets = useMemo(
    () => resolveConsumptionTargets(targetId, familyMembers),
    [targetId, familyMembers],
  );

  const canSave =
    familyId != null &&
    hasSaveableConsumptionDrafts(drafts) &&
    !saving &&
    !loadingLogs;

  const loadLogs = useCallback(async () => {
    if (!initData || !open || familyId == null) {
      setLogs([]);
      return;
    }
    setLoadingLogs(true);
    setError(null);
    try {
      const rows = await fetchMealConsumptionLogs(initData, mode, {
        family_id: familyId,
        menu_selection_id: menuSelectionId,
        day_index: dayIndex,
        planned_date: plannedDate,
      });
      setLogs(rows);
    } catch {
      setLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  }, [
    initData,
    open,
    familyId,
    mode,
    menuSelectionId,
    dayIndex,
    plannedDate,
  ]);

  useEffect(() => {
    if (!open) {
      return;
    }
    void loadLogs();
  }, [open, loadLogs]);

  useEffect(() => {
    if (!open) {
      return;
    }
    setTargetId(memberTargets[0]?.id ?? "self");
  }, [open, memberTargets]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const target = consumptionTargets[0] ?? {
      user_id: null,
      family_member_id: null,
    };
    if (logs.length > 0 && consumptionTargets.length === 1) {
      setDrafts(applyConsumptionLogsToDrafts(mealInputs, logs, target));
    } else if (consumptionTargets.length === 1) {
      setDrafts(buildDefaultConsumptionDrafts(mealInputs));
    } else {
      setDrafts(buildDefaultConsumptionDrafts(mealInputs));
    }
  }, [open, logs, mealInputs, consumptionTargets, targetId]);

  function updateDraft(key: string, patch: Partial<ConsumptionDraft>) {
    setDrafts((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...patch },
    }));
  }

  async function handleSave() {
    if (!initData || familyId == null || !canSave) {
      return;
    }
    const targets = resolveConsumptionTargets(targetId, familyMembers);
    const entries = buildConsumptionSaveEntries(mealInputs, drafts, targets);
    if (entries.length === 0) {
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await saveMealConsumptionLogs(initData, mode, {
        family_id: familyId,
        menu_selection_id: menuSelectionId,
        day_index: dayIndex,
        planned_date: plannedDate,
        entries,
      });
      onSaved?.();
      onClose();
    } catch (err) {
      setError(mealConsumptionErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  const footer = (
    <div className="space-y-2">
      {error ? (
        <p className="pa26-micro text-center text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : null}
      {familyId == null ? (
        <p className="pa26-micro text-center text-pa-muted">
          Сохранение отметок доступно после настройки семьи
        </p>
      ) : null}
      <V2Button
        variant="primary"
        className="w-full"
        disabled={!canSave}
        onClick={() => void handleSave()}
      >
        {saving ? MEAL_CONSUMPTION_SAVING_LABEL : MEAL_CONSUMPTION_SAVE_BUTTON_LABEL}
      </V2Button>
    </div>
  );

  return (
    <V2BottomSheet
      open={open}
      title={MEAL_CONSUMPTION_SHEET_TITLE}
      onClose={onClose}
      footer={footer}
    >
      <div className="space-y-4">
        <p className="pa26-caption -mt-1 text-pa-muted">
          {MEAL_CONSUMPTION_SHEET_SUBTITLE}
        </p>

        {showMemberPicker ? (
          <div>
            <p className="pa26-micro mb-2 font-semibold text-pa-foreground">
              {MEAL_CONSUMPTION_MEMBER_PROMPT}
            </p>
            <div className="flex flex-wrap gap-2">
              {memberTargets.map((target) => (
                <V2Chip
                  key={String(target.id)}
                  label={target.label}
                  active={targetId === target.id}
                  onClick={() => setTargetId(target.id)}
                />
              ))}
            </div>
          </div>
        ) : null}

        {loadingLogs ? (
          <p className="pa26-caption text-pa-muted">Загружаем отметки…</p>
        ) : null}

        {meals.length === 0 ? (
          <p className="pa26-body text-pa-muted">На этот день блюд в плане нет.</p>
        ) : (
          <ul className="space-y-3">
            {meals.map((item) => {
              const key = mealConsumptionKey(item.meal.meal_type, item.mealIndex);
              const draft = drafts[key] ?? {
                included: true,
                portion: 1 as const,
                status: "eaten" as const,
              };
              const heading = menuMealHeading(item.meal);
              const type = mealTypeLabel(item.meal.meal_type);
              return (
                <li
                  key={key}
                  className={cn(
                    "rounded-card border border-pa-border bg-pa-surface p-3",
                    !draft.included && "opacity-60",
                  )}
                >
                  <div className="flex items-start gap-2">
                    <MealSelectionToggle
                      checked={draft.included}
                      mealLabel={heading}
                      onChange={(included) => updateDraft(key, { included })}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="pa26-micro text-pa-muted">{type}</p>
                      <p className="pa26-card-title leading-snug">{heading}</p>
                    </div>
                  </div>
                  {draft.included ? (
                    <div className="mt-3 space-y-2 pl-8">
                      <div>
                        <p className="pa26-micro mb-1 text-pa-muted">Порция</p>
                        <div className="flex flex-wrap gap-2">
                          {MEAL_CONSUMPTION_PORTION_OPTIONS.map((option) => (
                            <V2Chip
                              key={option.value}
                              label={option.label}
                              active={draft.portion === option.value}
                              disabled={draft.status === "ate_out"}
                              onClick={() =>
                                updateDraft(key, { portion: option.value })
                              }
                            />
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="pa26-micro mb-1 text-pa-muted">Статус</p>
                        <div className="flex flex-wrap gap-2">
                          {MEAL_CONSUMPTION_STATUS_OPTIONS.map((option) => (
                            <V2Chip
                              key={option.id}
                              label={option.label}
                              active={draft.status === option.id}
                              onClick={() =>
                                updateDraft(key, { status: option.id })
                              }
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </V2BottomSheet>
  );
}
