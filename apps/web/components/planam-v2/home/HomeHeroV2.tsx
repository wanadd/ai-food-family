"use client";

/**
 * PLANAM V2 — Home hero (P0 hotfix).
 * Meal-вариант: подпись «Сегодня на …», название (≤2 строк, без кавычек),
 * чистое фото ~1/3 экрана без тяжёлого градиента, мета, CTA «Готовить»
 * и secondary «Ел другое» / «Пропустил». «Заменить» с hero убрана.
 * Остальные варианты hero рендерит существующий PlanAmHero2026.
 */

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MealFallbackPlate2026 } from "@/components/home-2026/MealFallbackPlate2026";
import { PlanAmHero2026 } from "@/components/home-2026/PlanAmHero2026";
import { V2Button } from "@/components/planam-v2/ui/V2Primitives";
import { useToast } from "@/components/ui/ToastProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import { cleanMealTitle, type PlanAmHeroState } from "@/lib/home/planam-hero-2026";
import { formatMealMeta } from "@/lib/home/home-2026-data";
import { createMealCheckin } from "@/lib/meal-checkins/api";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";

const MEAL_INTRO: Record<string, string> = {
  breakfast: "Сегодня на завтрак",
  lunch: "Сегодня на обед",
  dinner: "Сегодня на ужин",
  snack: "Сегодня на перекус",
};

export type HomeHeroV2Props = {
  loading?: boolean;
  state: PlanAmHeroState;
  /** Перезагрузка overview после checkin (Ел другое / Пропустил). */
  onChanged?: () => void;
};

export function HomeHeroV2({ loading = false, state, onChanged }: HomeHeroV2Props) {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { showToast } = useToast();
  const [skipBusy, setSkipBusy] = useState(false);

  if (loading) {
    return (
      <section className="px-4 pt-1" aria-busy="true">
        <Skeleton2026 variant="rect" className="min-h-[260px] w-full rounded-card" />
      </section>
    );
  }

  if (state.variant !== "meal" || !state.meal) {
    return <PlanAmHero2026 state={state} />;
  }

  const meal = state.meal;
  const title = cleanMealTitle(meal.name);
  const intro = MEAL_INTRO[meal.meal_type] ?? "Сегодня в меню";
  const metaParts: string[] = [];
  if (meal.prep_time_minutes != null && meal.prep_time_minutes > 0) {
    metaParts.push(`${meal.prep_time_minutes} мин`);
  }
  if (meal.calories != null && meal.calories > 0) {
    metaParts.push(`${Math.round(meal.calories)} ккал`);
  }
  const meta = metaParts.join(" · ") || formatMealMeta(meal);

  async function handleSkip() {
    if (!initData || skipBusy) {
      return;
    }
    setSkipBusy(true);
    try {
      await createMealCheckin(initData, mode, {
        meal_type: meal.meal_type,
        actual_status: "skipped",
        actual_description: meal.name,
        recipe_id: meal.recipe_id ?? undefined,
      });
      invalidateCache("menu-overview");
      showToast("Приём пищи пропущен — КБЖУ не учитываем");
      onChanged?.();
    } catch {
      showToast("Не удалось сохранить. Попробуйте ещё раз.");
    } finally {
      setSkipBusy(false);
    }
  }

  function openMealAction() {
    router.push(`/plan/today?meal=${encodeURIComponent(meal.meal_type)}&action=1`);
  }

  return (
    <section className="px-4 pt-1" aria-label="Главное действие">
      <div className="overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none">
        <div className="px-4 pb-1 pt-3.5">
          <p className="pa26-micro font-semibold uppercase tracking-wide text-sage-700 dark:text-sage-300">
            {intro}
          </p>
          <h2 className="pa26-hero mt-1 line-clamp-2 text-pa-foreground">{title}</h2>
        </div>

        <div className="relative mx-4 mt-2 h-[30vh] max-h-[260px] min-h-[170px] overflow-hidden rounded-control">
          {meal.image_url ? (
            <Image
              src={meal.image_url}
              alt={title}
              fill
              className="object-cover"
              sizes="100vw"
              unoptimized
              priority
            />
          ) : (
            <MealFallbackPlate2026
              mealType={meal.meal_type}
              className="absolute inset-0"
            />
          )}
          {/* Лёгкий градиент только снизу — для читаемости края, фото не перекрываем. */}
          <div
            className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-black/20 to-transparent"
            aria-hidden
          />
        </div>

        <div className="px-4 pb-4 pt-2.5">
          {meta ? <p className="pa26-caption text-pa-muted">{meta}</p> : null}
          <div className="mt-2.5 space-y-2">
            <V2Button
              variant="primary"
              size="wide"
              onClick={openMealAction}
            >
              Открыть действия
            </V2Button>
            <div className="flex gap-2">
              <V2Button
                variant="secondary"
                className="flex-1"
                onClick={openMealAction}
              >
                Ел другое
              </V2Button>
              <V2Button
                variant="secondary"
                className="flex-1"
                loading={skipBusy}
                onClick={() => void handleSkip()}
              >
                Пропустил
              </V2Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
