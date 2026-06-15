"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
} from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import { menuMealHeading } from "@/lib/menu/meal-heading";
import {
  adjustCookingBatchRemaining,
  createCookingBatch,
  discardCookingBatch,
  fetchActiveCookingBatch,
  finishCookingBatch,
  formatPreparedLeftoverAmount,
  mapExistingBatchToSheetDefaults,
  mapNewDishToSheetDefaults,
  previewPreparedRemaining,
  recordCookingBatchUsage,
  type CookingBatch,
} from "@/lib/plan/leftovers-api";
import type { PlanTodayMeal } from "@/lib/plan/plan-today";

const USE_PRESETS = [1, 2, 3] as const;

type PreparedLeftoversSheetV2Props = {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
  meal: PlanTodayMeal | null;
  familyId: number | null;
  menuSelectionId: number | null;
  dayIndex: number;
  plannedDate: string | null;
  canManage?: boolean;
};

export function PreparedLeftoversSheetV2({
  open,
  onClose,
  onSaved,
  meal,
  familyId,
  menuSelectionId,
  dayIndex,
  plannedDate,
  canManage = true,
}: PreparedLeftoversSheetV2Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [batch, setBatch] = useState<CookingBatch | null>(null);
  const [totalServings, setTotalServings] = useState(1);
  const [servingUnit, setServingUnit] = useState("порция");
  const [usedServings, setUsedServings] = useState<number | null>(null);
  const [customUsed, setCustomUsed] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const heading = meal ? menuMealHeading(meal.meal) : "";

  const remaining = useMemo(
    () =>
      previewPreparedRemaining(
        batch,
        totalServings,
        usedServings,
        customUsed,
      ),
    [batch, totalServings, usedServings, customUsed],
  );

  const loadExistingBatch = useCallback(async () => {
    if (!initData || !meal) {
      return;
    }
    setLoading(true);
    setError(null);
    setBatch(null);
    setUsedServings(null);
    setCustomUsed("");
    try {
      const existing = await fetchActiveCookingBatch(initData, mode, {
        recipe_id: meal.meal.recipe_id ?? null,
        menu_selection_id: menuSelectionId,
        day_index: dayIndex,
        meal_type: meal.meal.meal_type,
        planned_date: plannedDate,
      });
      if (existing) {
        const mapped = mapExistingBatchToSheetDefaults(existing);
        setBatch(mapped.batch);
        setTotalServings(mapped.totalServings);
        setServingUnit(mapped.servingUnit);
      } else {
        const mapped = mapNewDishToSheetDefaults(meal.meal.servings);
        setBatch(mapped.batch);
        setTotalServings(mapped.totalServings);
        setServingUnit(mapped.servingUnit);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить остатки",
      );
      const mapped = mapNewDishToSheetDefaults(meal.meal.servings);
      setBatch(mapped.batch);
      setTotalServings(mapped.totalServings);
      setServingUnit(mapped.servingUnit);
    } finally {
      setLoading(false);
    }
  }, [initData, meal, mode, menuSelectionId, dayIndex, plannedDate]);

  useEffect(() => {
    if (open && meal) {
      void loadExistingBatch();
    }
  }, [open, meal, loadExistingBatch]);

  async function ensureBatch(): Promise<CookingBatch> {
    if (!initData || !meal) {
      throw new Error("Нет данных");
    }
    if (batch) {
      return batch;
    }
    const created = await createCookingBatch(initData, mode, {
      family_id: familyId,
      recipe_id: meal.meal.recipe_id ?? null,
      recipe_title: heading,
      menu_selection_id: menuSelectionId,
      day_index: dayIndex,
      planned_date: plannedDate,
      meal_type: meal.meal.meal_type,
      total_servings: totalServings,
      serving_unit: servingUnit,
    });
    setBatch(created);
    return created;
  }

  async function handleSave() {
    if (!initData || !meal || !canManage || loading) {
      return;
    }
    const used =
      usedServings ??
      (customUsed ? Number(customUsed.replace(",", ".")) : null);
    if (used == null || !Number.isFinite(used) || used < 0) {
      setError("Укажите, сколько порций ушло");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      let current = await ensureBatch();
      if (used > 0) {
        current = await recordCookingBatchUsage(initData, mode, current.id, {
          servings_used: used,
        });
      } else {
        current = await adjustCookingBatchRemaining(initData, mode, current.id, {
          remaining_servings: totalServings,
        });
      }
      setBatch(current);
      setTotalServings(current.total_servings);
      setServingUnit(current.serving_unit);
      setUsedServings(null);
      setCustomUsed("");
      onSaved?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  }

  async function handleFinish() {
    if (!initData || !canManage || loading) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const current = await ensureBatch();
      const finished = await finishCookingBatch(initData, mode, current.id);
      setBatch(finished);
      onSaved?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  }

  async function handleDiscard() {
    if (!initData || !canManage || loading) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const current = await ensureBatch();
      const discarded = await discardCookingBatch(initData, mode, current.id);
      setBatch(discarded);
      onSaved?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  }

  const footer = (
    <div className="space-y-2">
      {error ? (
        <p className="pa26-micro text-center text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : null}
      {!canManage ? (
        <p className="pa26-micro text-center text-pa-muted">
          Только админ семьи может менять общие остатки
        </p>
      ) : (
        <>
          <V2Button
            variant="primary"
            className="w-full"
            disabled={busy || loading}
            onClick={() => void handleSave()}
          >
            {busy ? "Сохраняем…" : "Сохранить остатки"}
          </V2Button>
          <div className="flex gap-2">
            <V2Button
              variant="secondary"
              className="flex-1"
              disabled={busy || loading}
              onClick={() => void handleFinish()}
            >
              Всё съели
            </V2Button>
            <V2Button
              variant="secondary"
              className="flex-1"
              disabled={busy || loading}
              onClick={() => void handleDiscard()}
            >
              Выбросили
            </V2Button>
          </div>
        </>
      )}
    </div>
  );

  return (
    <V2BottomSheet
      open={open}
      title="Остатки блюда"
      onClose={onClose}
      footer={footer}
    >
      {meal ? (
        <div className="space-y-4">
          <p className="pa26-card-title">{heading}</p>

          {loading ? (
            <p className="pa26-caption text-pa-muted">Загружаем остатки…</p>
          ) : (
            <>
              <div>
                <p className="pa26-micro mb-2 font-semibold text-pa-foreground">
                  Приготовлено
                </p>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    disabled={!canManage || busy || Boolean(batch)}
                    className="flex size-9 items-center justify-center rounded-full border border-pa-border text-lg"
                    onClick={() => setTotalServings((v) => Math.max(1, v - 1))}
                  >
                    −
                  </button>
                  <span className="pa26-body min-w-[4rem] text-center">
                    {totalServings} {servingUnit === "порция" ? "порций" : servingUnit}
                  </span>
                  <button
                    type="button"
                    disabled={!canManage || busy || Boolean(batch)}
                    className="flex size-9 items-center justify-center rounded-full border border-pa-border text-lg"
                    onClick={() => setTotalServings((v) => v + 1)}
                  >
                    +
                  </button>
                </div>
              </div>

              <div>
                <p className="pa26-micro mb-2 font-semibold text-pa-foreground">
                  Ушло
                </p>
                <div className="flex flex-wrap gap-2">
                  {USE_PRESETS.map((n) => (
                    <V2Chip
                      key={n}
                      label={String(n)}
                      active={usedServings === n}
                      disabled={!canManage || busy}
                      onClick={() => {
                        setUsedServings(n);
                        setCustomUsed("");
                      }}
                    />
                  ))}
                  <V2Chip
                    label="Другое"
                    active={usedServings === null && customUsed !== ""}
                    disabled={!canManage || busy}
                    onClick={() => setUsedServings(null)}
                  />
                </div>
                {usedServings === null ? (
                  <input
                    type="text"
                    inputMode="decimal"
                    value={customUsed}
                    disabled={!canManage || busy}
                    onChange={(e) => setCustomUsed(e.target.value)}
                    placeholder="Количество"
                    className="mt-2 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2 pa26-body"
                  />
                ) : null}
              </div>

              <div className="rounded-card border border-pa-border bg-pa-surface p-3">
                <p className="pa26-micro text-pa-muted">Осталось</p>
                <p className="pa26-body font-semibold">
                  {formatPreparedLeftoverAmount(
                    remaining,
                    batch?.total_servings ?? totalServings,
                    servingUnit,
                  )}
                </p>
              </div>
            </>
          )}
        </div>
      ) : null}
    </V2BottomSheet>
  );
}
