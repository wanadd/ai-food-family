"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { PreparedLeftoversInlineV2 } from "@/components/planam-v2/menu/PreparedLeftoversInlineV2";
import { useTelegram } from "@/components/TelegramProvider";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
} from "@/components/planam-v2/ui/V2Primitives";
import { cacheKey, invalidate as invalidateCache } from "@/lib/cache/session-cache";
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
  buildPersonalConsumptionPayload,
  consumptionSaveFooterHint,
  getMealConsumptionSaveBlockReason,
  mealConsumptionSaveBlockMessage,
  canSaveMealConsumption,
  resolveEffectiveConsumptionDrafts,
  MEAL_CONSUMPTION_MEMBER_PROMPT,
  MEAL_CONSUMPTION_PORTION_OPTIONS,
  MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
  MEAL_CONSUMPTION_PERMISSION_ERROR,
  MEAL_CONSUMPTION_SAVE_ERROR,
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
import {
  buildDefaultLeftoversDraft,
  hasTouchedLeftoversDrafts,
  mapBatchesByMealKey,
  persistLeftoversDraft,
  shouldShowLeftoversSection,
  type LeftoversDraft,
} from "@/lib/plan/meal-leftovers-unified";
import { fetchPreparedLeftovers, type CookingBatch } from "@/lib/plan/leftovers-api";
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
  currentUserId?: number | null;
  canManagePreparedLeftovers?: boolean;
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
  currentUserId: currentUserIdProp = null,
  canManagePreparedLeftovers = true,
}: MealConsumptionSheetV2Props) {
  const { initData, user } = useTelegram();
  const { mode, context } = useAppMode();
  const [targetId, setTargetId] = useState<ConsumptionTargetId>("self");
  const [drafts, setDrafts] = useState<Record<string, ConsumptionDraft>>({});
  const [leftoversDrafts, setLeftoversDrafts] = useState<
    Record<string, LeftoversDraft>
  >({});
  const [batchesByKey, setBatchesByKey] = useState<
    Record<string, CookingBatch | null>
  >({});
  const [logs, setLogs] = useState<
    Awaited<ReturnType<typeof fetchMealConsumptionLogs>>
  >([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [loadingLeftovers, setLoadingLeftovers] = useState(false);
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
        servings: item.meal.servings ?? null,
      })),
    [meals],
  );

  const currentUserId =
    currentUserIdProp ??
    user?.id ??
    familyMembers.find((m) => m.is_you)?.user_id ??
    null;

  const consumptionTargets = useMemo(
    () => resolveConsumptionTargets(targetId, familyMembers, currentUserId),
    [targetId, familyMembers, currentUserId],
  );

  const effectiveDrafts = useMemo(
    () => resolveEffectiveConsumptionDrafts(mealInputs, drafts),
    [mealInputs, drafts],
  );

  const consumptionSaveBlockReason = getMealConsumptionSaveBlockReason({
    mode,
    mealInputs,
    drafts: effectiveDrafts,
    targets: consumptionTargets,
    saving,
    hasInitData: Boolean(initData),
  });

  const canSaveConsumption = canSaveMealConsumption({
    mode,
    mealInputs,
    drafts: effectiveDrafts,
    targets: consumptionTargets,
    saving,
    hasInitData: Boolean(initData),
  });

  const hasLeftoversToSave = hasTouchedLeftoversDrafts(leftoversDrafts);
  const canSave =
    (canSaveConsumption || hasLeftoversToSave) &&
    Boolean(initData) &&
    !saving &&
    !loadingLogs;

  const saveBlockMessage = mealConsumptionSaveBlockMessage(
    canSave ? null : consumptionSaveBlockReason,
  );

  const footerHint = consumptionSaveFooterHint(
    familyId,
    isFamilyAdmin,
    targetId,
  );

  const loadLeftovers = useCallback(async () => {
    if (!initData || !open) {
      setBatchesByKey({});
      return;
    }
    setLoadingLeftovers(true);
    try {
      const batches = await fetchPreparedLeftovers(initData, mode);
      const mealKeys = mealInputs.map((m) => ({
        key: mealConsumptionKey(m.meal_type, m.mealIndex),
        meal_type: m.meal_type,
        recipe_id: m.recipe_id,
      }));
      const mapped = mapBatchesByMealKey(
        batches,
        mealKeys,
        menuSelectionId,
        dayIndex,
        plannedDate,
      );
      setBatchesByKey(mapped);
      const nextDrafts: Record<string, LeftoversDraft> = {};
      for (const meal of mealInputs) {
        const key = mealConsumptionKey(meal.meal_type, meal.mealIndex);
        nextDrafts[key] = buildDefaultLeftoversDraft(
          mapped[key] ?? null,
          meal.servings,
        );
      }
      setLeftoversDrafts(nextDrafts);
    } catch {
      setBatchesByKey({});
    } finally {
      setLoadingLeftovers(false);
    }
  }, [initData, open, mode, mealInputs, menuSelectionId, dayIndex, plannedDate]);

  const loadLogs = useCallback(async () => {
    if (!initData || !open) {
      setLogs([]);
      return;
    }
    setLoadingLogs(true);
    setError(null);
    try {
      const target = resolveConsumptionTargets(
        targetId,
        familyMembers,
        currentUserId,
      )[0];
      const rows = await fetchMealConsumptionLogs(initData, mode, {
        family_id: familyId,
        family_member_id:
          target?.family_member_id != null ? target.family_member_id : null,
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
    targetId,
    currentUserId,
    familyMembers,
  ]);

  useEffect(() => {
    if (!open) {
      return;
    }
    void loadLogs();
    void loadLeftovers();
  }, [open, loadLogs, loadLeftovers, targetId]);

  useEffect(() => {
    if (!open) {
      return;
    }
    setTargetId(memberTargets[0]?.id ?? "self");
  }, [open, memberTargets]);

  useEffect(() => {
    if (!open) {
      setDrafts({});
      return;
    }
    if (mealInputs.length > 0) {
      setDrafts(buildDefaultConsumptionDrafts(mealInputs));
    }
  }, [open, mealInputs]);

  useEffect(() => {
    if (!open || logs.length === 0 || consumptionTargets.length !== 1) {
      return;
    }
    const target = consumptionTargets[0];
    setDrafts(applyConsumptionLogsToDrafts(mealInputs, logs, target));
  }, [open, logs, mealInputs, consumptionTargets]);

  function updateDraft(key: string, patch: Partial<ConsumptionDraft>) {
    setDrafts((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...patch },
    }));
  }

  function updateLeftoversDraft(key: string, patch: Partial<LeftoversDraft>) {
    setLeftoversDrafts((prev) => ({
      ...prev,
      [key]: { ...(prev[key] ?? buildDefaultLeftoversDraft(null)), ...patch },
    }));
  }

  async function handleSave() {
    if (!initData || !canSave) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      if (canSaveConsumption) {
        const targets = resolveConsumptionTargets(
          targetId,
          familyMembers,
          currentUserId,
        );
        if (targets.length === 0) {
          setError(MEAL_CONSUMPTION_PERMISSION_ERROR);
          return;
        }
        const entries = buildConsumptionSaveEntries(
          mealInputs,
          effectiveDrafts,
          targets,
        );
        if (entries.length > 0) {
          const result = await saveMealConsumptionLogs(
            initData,
            mode,
            buildPersonalConsumptionPayload(
              {
                familyId,
                menuSelectionId,
                dayIndex,
                plannedDate,
              },
              entries,
            ),
          );
          if (!result?.saved) {
            setError(MEAL_CONSUMPTION_SAVE_ERROR);
            return;
          }
        }
      }

      if (hasLeftoversToSave) {
        for (const meal of mealInputs) {
          const key = mealConsumptionKey(meal.meal_type, meal.mealIndex);
          const leftoversDraft = leftoversDrafts[key];
          if (!leftoversDraft?.touched || meal.recipe_id == null) {
            continue;
          }
          if (
            !shouldShowLeftoversSection({
              recipeId: meal.recipe_id,
              included: effectiveDrafts[key]?.included ?? false,
              status: effectiveDrafts[key]?.status ?? "eaten",
              existingBatch: batchesByKey[key] ?? null,
            })
          ) {
            continue;
          }
          await persistLeftoversDraft(
            initData,
            mode,
            {
              familyId,
              menuSelectionId,
              dayIndex,
              plannedDate,
              recipeId: meal.recipe_id,
              recipeTitle: meal.recipe_title,
              mealType: meal.meal_type,
              recipeServings: meal.servings,
            },
            leftoversDraft,
            batchesByKey[key] ?? null,
          );
        }
        invalidateCache(cacheKey.pantry(mode));
        invalidateCache(cacheKey.menuOverview(mode));
      }

      await loadLogs();
      await loadLeftovers();
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
      {!canSave && saveBlockMessage && !hasLeftoversToSave ? (
        <p className="pa26-micro text-center text-pa-muted">{saveBlockMessage}</p>
      ) : null}
      {(loadingLogs || loadingLeftovers) && canSave ? (
        <p className="pa26-micro text-center text-pa-muted">Загружаем отметки…</p>
      ) : null}
      <p className="pa26-micro text-center text-pa-muted">{footerHint}</p>
      <V2Button
        variant="primary"
        className="w-full"
        disabled={!canSave || loadingLogs || loadingLeftovers}
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

        {loadingLogs || loadingLeftovers ? (
          <p className="pa26-caption text-pa-muted">Загружаем отметки…</p>
        ) : null}

        {meals.length === 0 ? (
          <p className="pa26-body text-pa-muted">На этот день блюд в плане нет.</p>
        ) : (
          <ul className="space-y-3">
            {meals.map((item) => {
              const key = mealConsumptionKey(item.meal.meal_type, item.mealIndex);
              const draft = effectiveDrafts[key] ?? {
                included: true,
                portion: 1 as const,
                status: "eaten" as const,
              };
              const leftoversDraft =
                leftoversDrafts[key] ??
                buildDefaultLeftoversDraft(
                  batchesByKey[key] ?? null,
                  item.meal.servings,
                );
              const existingBatch = batchesByKey[key] ?? null;
              const showLeftovers = shouldShowLeftoversSection({
                recipeId: item.meal.recipe_id ?? null,
                included: draft.included,
                status: draft.status,
                existingBatch,
                leftoversExpanded: draft.leftoversExpanded,
              });
              const canExpandLeftovers =
                Boolean(item.meal.recipe_id) &&
                draft.included &&
                draft.status === "eaten" &&
                !existingBatch &&
                !draft.leftoversExpanded;
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
                      {draft.status === "ate_out" ? (
                        <input
                          type="text"
                          value={draft.externalFoodNote ?? ""}
                          onChange={(e) =>
                            updateDraft(key, {
                              externalFoodNote: e.target.value,
                            })
                          }
                          placeholder="Что ели? (без AI, вручную)"
                          className="w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2 pa26-body"
                        />
                      ) : null}
                      {canExpandLeftovers ? (
                        <V2Chip
                          label="Уточнить остатки"
                          active={false}
                          onClick={() =>
                            updateDraft(key, { leftoversExpanded: true })
                          }
                        />
                      ) : null}
                      {showLeftovers ? (
                        <PreparedLeftoversInlineV2
                          batch={existingBatch}
                          draft={leftoversDraft}
                          canManage={canManagePreparedLeftovers}
                          disabled={saving || loadingLeftovers}
                          onChange={(patch) => updateLeftoversDraft(key, patch)}
                        />
                      ) : null}
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
