"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { RecipeCookFinishSheet } from "@/components/recipes-2026/RecipeCookFinishSheet";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import { useToast } from "@/components/ui/ToastProvider";
import { fetchRecipe, markRecipeCooked } from "@/lib/recipes/api";
import { recipeDetailHeading } from "@/lib/recipes/card-title";
import {
  readRecipeMealContext,
  recipeDetailPathWithContext,
} from "@/lib/recipes/recipe-meal-context";
import {
  formatTimerLabel,
  parseStepMinutes,
} from "@/lib/recipes/recipe-step-timer";
import type { RecipeDetail } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";

type RecipeCookingModeProps = {
  recipeId: number;
};

function StepTimer({ minutes }: { minutes: number }) {
  const [remaining, setRemaining] = useState<number | null>(null);

  useEffect(() => {
    if (remaining == null) {
      return;
    }
    if (remaining <= 0) {
      return;
    }
    const id = window.setInterval(() => {
      setRemaining((v) => (v != null && v > 0 ? v - 1 : 0));
    }, 1000);
    return () => window.clearInterval(id);
  }, [remaining]);

  if (remaining == null) {
    return (
      <button
        type="button"
        onClick={() => setRemaining(minutes * 60)}
        className="rounded-pill border border-orange-200 bg-orange-50 px-3 py-1.5 pa26-micro font-semibold text-orange-800 dark:border-orange-900/40 dark:bg-orange-950/30 dark:text-orange-200"
        data-testid="recipe-step-timer-start"
      >
        Запустить таймер · {formatTimerLabel(minutes)}
      </button>
    );
  }

  const mins = Math.floor(remaining / 60);
  const secs = remaining % 60;
  const done = remaining <= 0;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span
        className={cn(
          "rounded-pill px-3 py-1.5 pa26-micro font-semibold tabular-nums",
          done
            ? "bg-sage-100 text-sage-800 dark:bg-sage-900/30"
            : "bg-orange-100 text-orange-800 dark:bg-orange-950/40",
        )}
        data-testid="recipe-step-timer-display"
      >
        {done ? "Готово" : `${mins}:${secs.toString().padStart(2, "0")}`}
      </span>
      {!done ? (
        <button
          type="button"
          onClick={() => setRemaining(null)}
          className="pa26-micro font-semibold text-pa-muted"
        >
          Сбросить
        </button>
      ) : null}
    </div>
  );
}

export function RecipeCookingMode({ recipeId }: RecipeCookingModeProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { showToast } = useToast();

  const mealContext = useMemo(
    () => readRecipeMealContext(searchParams),
    [searchParams],
  );
  const detailHref = recipeDetailPathWithContext(recipeId, searchParams);

  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [finishOpen, setFinishOpen] = useState(false);
  const [cookingBusy, setCookingBusy] = useState(false);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecipe(initData, recipeId);
      setRecipe(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Рецепт не найден");
    } finally {
      setLoading(false);
    }
  }, [initData, recipeId]);

  useEffect(() => {
    void load();
  }, [load]);

  const steps = Array.isArray(recipe?.steps) ? recipe!.steps : [];
  const totalSteps = steps.length;
  const isLastStep = totalSteps > 0 && stepIndex === totalSteps - 1;
  const currentStep = steps[stepIndex] ?? "";
  const stepMinutes = parseStepMinutes(currentStep);
  const heading = recipe ? recipeDetailHeading(recipe) : "";

  const hasMenuContext = Boolean(
    mealContext.plannedDate || mealContext.menuSelectionId != null,
  );

  async function handlePrepared() {
    if (!recipe) return;
    setCookingBusy(true);
    try {
      if (initData) {
        await markRecipeCooked(initData, mode, recipe.id, {
          servings: recipe.servings ?? 1,
        });
      }
      setFinishOpen(true);
    } catch {
      setFinishOpen(true);
      showToast("Приготовлено. Выберите, что сделать с блюдом.");
    } finally {
      setCookingBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="px-4 py-8">
        <Skeleton2026 variant="text" className="max-w-[70%]" />
        <Skeleton2026 variant="rect" className="mt-4 h-40" />
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="px-4 py-12">
        <EmptyState2026
          title="Не удалось открыть режим готовки"
          description={error ?? "Вернитесь к рецепту."}
          actionLabel="К рецепту"
          onAction={() => router.push(detailHref)}
        />
      </div>
    );
  }

  if (totalSteps === 0) {
    return (
      <div className="flex min-h-[70vh] flex-col px-4 pb-8 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <Link
          href={detailHref}
          className="pa26-micro font-semibold text-sage-700 dark:text-sage-300"
        >
          ← К рецепту
        </Link>
        <h1 className="pa26-page-title mt-3">{heading}</h1>
        <p className="mt-4 pa26-body text-pa-muted">
          Пошаговые инструкции пока не добавлены. Можно отметить блюдо готовым.
        </p>
        <Button2026
          variant="primary"
          size="wide"
          className="mt-6"
          loading={cookingBusy}
          data-testid="recipe-cook-finish"
          onClick={() => void handlePrepared()}
        >
          Приготовлено
        </Button2026>
        <RecipeCookFinishSheet
          open={finishOpen}
          onClose={() => {
            setFinishOpen(false);
            router.push(detailHref);
          }}
          recipeId={recipe.id}
          recipeTitle={heading}
          servings={recipe.servings ?? 1}
          mealContext={mealContext}
          hasMenuContext={hasMenuContext}
        />
      </div>
    );
  }

  return (
    <div
      className="flex min-h-[100dvh] flex-col bg-pa-canvas pb-[max(1rem,env(safe-area-inset-bottom))]"
      data-testid="recipe-cooking-mode"
    >
      <header className="border-b border-pa-border bg-pa-surface px-4 py-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <Link
          href={detailHref}
          className="pa26-micro font-semibold text-sage-700 dark:text-sage-300"
          data-testid="recipe-cook-back"
        >
          ← К рецепту
        </Link>
        <h1 className="pa26-card-title mt-2 line-clamp-2">{heading}</h1>
        <p
          className="pa26-micro mt-1 font-semibold text-orange-700 dark:text-orange-300"
          data-testid="recipe-cook-progress"
        >
          Шаг {stepIndex + 1} из {totalSteps}
        </p>
        <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-pa-border/60">
          <div
            className="h-full rounded-pill bg-orange-500 transition-all"
            style={{ width: `${((stepIndex + 1) / totalSteps) * 100}%` }}
          />
        </div>
      </header>

      <main className="flex flex-1 flex-col px-4 py-6">
        <p className="pa26-hero leading-snug text-pa-foreground">{currentStep}</p>
        {stepMinutes != null ? (
          <div className="mt-4">
            <StepTimer minutes={stepMinutes} />
          </div>
        ) : null}
      </main>

      <footer className="border-t border-pa-border bg-pa-surface px-4 py-3">
        <div className="flex gap-2">
          <Button2026
            variant="secondary"
            className="flex-1"
            disabled={stepIndex === 0}
            onClick={() => setStepIndex((i) => Math.max(0, i - 1))}
            data-testid="recipe-cook-prev"
          >
            Назад
          </Button2026>
          {isLastStep ? (
            <Button2026
              variant="primary"
              className="flex-1"
              loading={cookingBusy}
              data-testid="recipe-cook-finish"
              onClick={() => void handlePrepared()}
            >
              Приготовлено
            </Button2026>
          ) : (
            <Button2026
              variant="primary"
              className="flex-1"
              onClick={() =>
                setStepIndex((i) => Math.min(totalSteps - 1, i + 1))
              }
              data-testid="recipe-cook-next"
            >
              Дальше
            </Button2026>
          )}
        </div>
      </footer>

      <RecipeCookFinishSheet
        open={finishOpen}
        onClose={() => {
          setFinishOpen(false);
          router.push(detailHref);
        }}
        onDone={() => {
          setTimeout(() => router.push(detailHref), 1200);
        }}
        recipeId={recipe.id}
        recipeTitle={heading}
        servings={recipe.servings ?? 1}
        mealContext={mealContext}
        hasMenuContext={hasMenuContext}
      />
    </div>
  );
}
