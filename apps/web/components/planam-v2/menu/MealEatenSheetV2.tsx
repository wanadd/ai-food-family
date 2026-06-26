"use client";

/**
 * PLANAM V2 — «приготовил ≠ съел».
 * Bottom sheet после готовки / из meal actions: Съел сейчас, Съем позже,
 * Ел другое, Пропустил. КБЖУ на backend считаются только для EATEN-статусов
 * (ate_*); cooked / skipped записываются, но в КБЖУ не попадают.
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
} from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { mealTypesForHour } from "@/lib/home/planam-hero-2026";
import { createMealCheckin } from "@/lib/meal-checkins/api";
import { MEAL_TYPE_LABELS } from "@/lib/meal-checkins/constants";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import { cn } from "@/lib/planam/cn";

type Step = "actions" | "other" | "done";

type Outcome = "ate_home" | "cooked" | "skipped" | "ate_other";

export type MealEatenSheetV2Props = {
  open: boolean;
  onClose: () => void;
  /** Вызывается после успешной записи (для перезагрузки данных экрана). */
  onSaved?: () => void;
  /** breakfast | lunch | dinner | snack. Если не задан — пользователь выберет. */
  mealType?: string | null;
  mealName?: string | null;
  recipeId?: number | null;
  plannedDate?: string | null;
  /** "actions" — полный выбор после готовки; "other" — сразу форма «Ел другое». */
  initialStep?: "actions" | "other";
  /** Сразу записать исход (с wellness quick actions). */
  autoOutcome?: Outcome | null;
  title?: string;
};

const PORTION_OPTIONS = [
  { id: "small", label: "мало" },
  { id: "normal", label: "обычно" },
  { id: "large", label: "много" },
] as const;

const DONE_TEXT: Record<Outcome, string> = {
  ate_home: "Записали! КБЖУ учтены в сегодняшнем дне.",
  cooked: "Отметили как приготовленное. КБЖУ учтём, когда поедите.",
  skipped: "Приём пищи пропущен — в КБЖУ не учитываем.",
  ate_other: "Записали! Учтём в дневнике питания.",
};

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"] as const;

const FOOD_QUICK_CHIPS = [
  "суп",
  "салат",
  "мясо",
  "каша",
  "бутерброд",
  "напиток",
] as const;

export function MealEatenSheetV2({
  open,
  onClose,
  onSaved,
  mealType = null,
  mealName = null,
  recipeId = null,
  plannedDate = null,
  initialStep = "actions",
  autoOutcome = null,
  title,
}: MealEatenSheetV2Props) {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();

  const [step, setStep] = useState<Step>(initialStep);
  const [selectedMealType, setSelectedMealType] = useState<string>(
    mealType ?? mealTypesForHour(new Date().getHours())[0],
  );
  const [otherText, setOtherText] = useState("");
  const [portion, setPortion] = useState<string>("normal");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [doneText, setDoneText] = useState("");
  const autoSubmittedRef = useRef(false);

  useEffect(() => {
    if (open) {
      setStep(initialStep);
      setSelectedMealType(
        mealType ?? mealTypesForHour(new Date().getHours())[0],
      );
      setOtherText("");
      setPortion("normal");
      setError(null);
      setBusy(false);
      autoSubmittedRef.current = false;
    }
  }, [open, initialStep, mealType]);

  const submit = useCallback(
    async (outcome: Outcome, description?: string | null) => {
      if (!initData) {
        return;
      }
      setBusy(true);
      setError(null);
      try {
        await createMealCheckin(initData, mode, {
          meal_type: selectedMealType,
          actual_status: outcome,
          planned_date: plannedDate ?? undefined,
          actual_description: description ?? mealName ?? undefined,
          recipe_id:
            outcome === "ate_other" ? undefined : (recipeId ?? undefined),
        });
        invalidateCache("menu-overview");
        setDoneText(DONE_TEXT[outcome]);
        setStep("done");
        onSaved?.();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Не удалось сохранить");
      } finally {
        setBusy(false);
      }
    },
    [
      initData,
      mode,
      selectedMealType,
      plannedDate,
      mealName,
      recipeId,
      onSaved,
    ],
  );

  useEffect(() => {
    if (!open || !autoOutcome || autoOutcome === "ate_other") {
      return;
    }
    if (autoSubmittedRef.current) {
      return;
    }
    autoSubmittedRef.current = true;
    void submit(autoOutcome);
  }, [open, autoOutcome, submit]);

  const sheetTitle =
    title ??
    (step === "other"
      ? "Ел другое"
      : step === "done"
        ? "Записано"
        : "Блюдо приготовлено 🎉");

  return (
    <V2BottomSheet open={open} title={sheetTitle} onClose={onClose}>
      {step === "actions" ? (
        <div className="space-y-3 pb-2">
          {mealName ? (
            <p className="pa26-body text-pa-muted">{mealName}</p>
          ) : null}
          {!mealType ? (
            <div>
              <p className="pa26-micro mb-1.5 text-pa-muted">Какой это приём пищи?</p>
              <div className="flex flex-wrap gap-2">
                {MEAL_TYPES.map((t) => (
                  <V2Chip
                    key={t}
                    label={MEAL_TYPE_LABELS[t]}
                    active={selectedMealType === t}
                    onClick={() => setSelectedMealType(t)}
                  />
                ))}
              </div>
            </div>
          ) : null}
          <p className="pa26-body font-semibold">Что дальше?</p>
          <div className="space-y-2">
            <OutcomeButton
              label="Съел сейчас"
              caption="КБЖУ учтём сразу"
              disabled={busy}
              onClick={() => void submit("ate_home")}
            />
            <OutcomeButton
              label="Съем позже"
              caption="Отметим как приготовленное, КБЖУ — потом"
              disabled={busy}
              onClick={() => void submit("cooked")}
            />
            <OutcomeButton
              label="Ел другое"
              caption="Запишем, что вы ели вместо блюда"
              disabled={busy}
              onClick={() => setStep("other")}
            />
            <OutcomeButton
              label="Пропустил приём пищи"
              caption="Не учитываем в КБЖУ"
              disabled={busy}
              onClick={() => void submit("skipped")}
            />
          </div>
          {error ? <p className="pa26-caption text-pa-error">{error}</p> : null}
          <button
            type="button"
            className="pa26-caption w-full py-1 text-center font-semibold text-sage-700 dark:text-sage-300"
            onClick={() => {
              onClose();
              router.push(PLANAM_ROUTES.planToday);
            }}
          >
            Вернуться в меню
          </button>
        </div>
      ) : null}

      {step === "other" ? (
        <div className="space-y-4 pb-2">
          {!mealType ? (
            <div className="flex flex-wrap gap-2">
              {MEAL_TYPES.map((t) => (
                <V2Chip
                  key={t}
                  label={MEAL_TYPE_LABELS[t]}
                  active={selectedMealType === t}
                  onClick={() => setSelectedMealType(t)}
                />
              ))}
            </div>
          ) : null}
          <div>
            <label
              htmlFor="meal-other-input"
              className="pa26-caption mb-1.5 block font-semibold"
            >
              Что вы ели?
            </label>
            <input
              id="meal-other-input"
              type="text"
              value={otherText}
              onChange={(e) => setOtherText(e.target.value)}
              placeholder="Например: салат и кофе"
              className="w-full rounded-control border border-pa-border bg-pa-surface px-3.5 py-3 pa26-body text-pa-foreground outline-none placeholder:text-pa-muted focus:border-sage-500"
            />
            <div className="mt-2 flex flex-wrap gap-2">
              {FOOD_QUICK_CHIPS.map((chip) => (
                <V2Chip
                  key={chip}
                  label={chip}
                  active={otherText.toLowerCase() === chip}
                  onClick={() => setOtherText(chip)}
                />
              ))}
            </div>
          </div>
          <div>
            <p className="pa26-caption mb-1.5 font-semibold">Количество</p>
            <div className="flex gap-2">
              {PORTION_OPTIONS.map((p) => (
                <V2Chip
                  key={p.id}
                  label={p.label}
                  active={portion === p.id}
                  onClick={() => setPortion(p.id)}
                />
              ))}
            </div>
          </div>
          {error ? <p className="pa26-caption text-pa-error">{error}</p> : null}
          <V2Button
            variant="primary"
            size="wide"
            loading={busy}
            disabled={!otherText.trim()}
            onClick={() => {
              const portionLabel =
                PORTION_OPTIONS.find((p) => p.id === portion)?.label ?? "обычно";
              void submit("ate_other", `${otherText.trim()} (${portionLabel})`);
            }}
          >
            Учесть
          </V2Button>
          {initialStep === "actions" ? (
            <button
              type="button"
              className="pa26-caption w-full py-1 text-center font-semibold text-sage-700 dark:text-sage-300"
              onClick={() => setStep("actions")}
            >
              ← Назад
            </button>
          ) : null}
        </div>
      ) : null}

      {step === "done" ? (
        <div className="space-y-4 pb-2">
          <p className="pa26-body text-pa-muted">{doneText}</p>
          <V2Button variant="primary" size="wide" onClick={onClose}>
            Готово
          </V2Button>
        </div>
      ) : null}
    </V2BottomSheet>
  );
}

function OutcomeButton({
  label,
  caption,
  onClick,
  disabled = false,
}: {
  label: string;
  caption?: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "flex w-full min-h-[52px] flex-col justify-center rounded-card border border-pa-border bg-pa-surface px-4 py-2.5 text-left transition",
        "hover:bg-sage-50 disabled:opacity-60 dark:hover:bg-pa-elevated/40",
      )}
    >
      <span className="pa26-card-title">{label}</span>
      {caption ? (
        <span className="pa26-micro mt-0.5 text-pa-muted">{caption}</span>
      ) : null}
    </button>
  );
}
