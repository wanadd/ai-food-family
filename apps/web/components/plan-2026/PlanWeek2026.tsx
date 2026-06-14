"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchSelectedMenu } from "@/lib/menu/api";
import { getMenuDays, defaultDayIndex } from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { menuMealHeading } from "@/lib/menu/meal-heading";
import { pluralRuWithCount } from "@/lib/i18n/plural-ru";
import { mealLabel } from "@/lib/recipes/labels";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";
import { formatPlanDayLabel } from "@/lib/plan/plan-today";

export function PlanWeek2026() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const selected = await fetchSelectedMenu(initData, mode);
      setMenu(selected?.menu ?? null);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (!modeLoading) {
      void load();
    }
  }, [load, modeLoading]);

  if (loading) {
    return (
      <div className="space-y-3 px-4 pb-8 pt-4">
        <Skeleton2026 variant="rect" className="h-20" />
        <Skeleton2026 variant="rect" className="h-20" />
      </div>
    );
  }

  if (!menu) {
    return (
      <div className="px-4 py-8">
        <EmptyState2026
          title="Плана нет"
          description="Создайте меню на неделю."
          actionLabel="Создать меню"
          onAction={() => router.push(PLAN_PATHS.generate)}
        />
      </div>
    );
  }

  const days = getMenuDays(menu);
  const todayIdx = defaultDayIndex(menu);

  return (
    <div className="space-y-4 px-4 pb-8 pt-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="pa26-page-title">Обзор</h1>
        <Link href={PLAN_PATHS.generate}>
          <Button2026 variant="secondary">Пересобрать</Button2026>
        </Link>
      </div>

      <div className="space-y-3">
        {days.map((day) => {
          const isToday = day.day_index === todayIdx;
          return (
            <Link
              key={day.day_index}
              href={`${PLAN_PATHS.today}?day=${day.day_index}`}
              className="block rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft transition active:scale-[0.98] dark:shadow-none"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="pa26-card-title">
                  {formatPlanDayLabel(menu, day.day_index)}
                  {isToday ? (
                    <span className="ml-2 rounded-pill bg-sage-50 px-2 py-0.5 pa26-micro text-sage-700 dark:bg-sage-700/30 dark:text-sage-300">
                      сегодня
                    </span>
                  ) : null}
                </p>
                <span className="pa26-caption text-pa-muted">
                  {pluralRuWithCount(day.meals.length, "блюдо", "блюда", "блюд")} →
                </span>
              </div>
              <ul className="mt-3 space-y-2">
                {day.meals.slice(0, 4).map((meal, i) => {
                  const heading = menuMealHeading(meal);
                  const mealType = mealLabel(meal.meal_type);
                  const kcal =
                    meal.calories_estimate != null
                      ? `${Math.round(meal.calories_estimate)} ккал`
                      : null;
                  return (
                    <li
                      key={`${meal.meal_type}-${meal.recipe_id ?? i}`}
                      className="flex items-center gap-2"
                    >
                      <div className="h-10 w-10 shrink-0 overflow-hidden rounded-control">
                        <RecipeImage2026
                          imageUrl={meal.image_url ?? meal.thumbnail_url ?? meal.hero_image_url}
                          alt={heading}
                          variant="thumb"
                          mealType={meal.meal_type}
                          className="size-10"
                        />
                      </div>
                      <p className="min-w-0 flex-1 pa26-caption leading-snug text-pa-ink">
                        {mealType ? (
                          <span className="text-pa-muted">{mealType} · </span>
                        ) : null}
                        {heading}
                        {kcal ? (
                          <span className="text-pa-muted"> · {kcal}</span>
                        ) : null}
                      </p>
                    </li>
                  );
                })}
              </ul>
              {day.meals.length > 4 ? (
                <p className="mt-2 pa26-micro text-pa-muted">
                  ещё{" "}
                  {pluralRuWithCount(day.meals.length - 4, "блюдо", "блюда", "блюд")}
                </p>
              ) : null}
            </Link>
          );
        })}
      </div>

      <Link href={PLAN_PATHS.today} className="block">
        <Button2026 variant="primary" className="w-full">
          Открыть сегодня
        </Button2026>
      </Link>
    </div>
  );
}
