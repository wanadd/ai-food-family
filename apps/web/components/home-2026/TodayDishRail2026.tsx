"use client";

import { useRouter } from "next/navigation";

import { MealFallbackPlate2026 } from "@/components/home-2026/MealFallbackPlate2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import type { Home2026TodayMeal } from "@/lib/home/home-2026-data";
import { formatMealMeta } from "@/lib/home/home-2026-data";
import { PLANAM_ROUTES, recipeDetailPath } from "@/lib/planam/routes";
import { cn } from "@/lib/planam/cn";

type TodayDishRail2026Props = {
  meals: Home2026TodayMeal[];
  loading?: boolean;
};

function dishHref(meal: Home2026TodayMeal): string {
  if (meal.recipe_id != null) {
    return recipeDetailPath(meal.recipe_id);
  }
  return `${PLANAM_ROUTES.planToday}?meal=${encodeURIComponent(meal.meal_type)}`;
}

export function TodayDishRail2026({ meals, loading = false }: TodayDishRail2026Props) {
  const router = useRouter();

  if (loading) {
    return (
      <section className="px-4 pt-4" aria-busy="true" aria-label="Сегодня в меню">
        <Skeleton2026 variant="text" className="mb-2 max-w-[50%]" />
        <div className="flex gap-3 overflow-hidden">
          <Skeleton2026 variant="rect" className="h-44 w-[72%] shrink-0 rounded-card" />
          <Skeleton2026 variant="rect" className="h-44 w-[72%] shrink-0 rounded-card" />
        </div>
      </section>
    );
  }

  if (meals.length === 0) {
    return (
      <section className="px-4 pt-4" aria-label="Сегодня в меню">
        <RailHeader />
        <EmptyState2026
          title="Меню на сегодня ещё не собрано"
          description="Соберите план — и здесь появятся блюда на каждый приём пищи."
          actionLabel="Собрать меню"
          onAction={() => router.push(PLANAM_ROUTES.planGenerate)}
          className="py-6"
        />
      </section>
    );
  }

  return (
    <section className="px-4 pt-4" aria-label="Сегодня в меню">
      <RailHeader />
      <div
        className={cn(
          "-mx-4 flex gap-3 overflow-x-auto px-4 pb-1",
          "snap-x snap-mandatory scroll-smooth",
        )}
      >
        {meals.map((meal) => (
          <article
            key={meal.meal_type}
            className={cn(
              "flex w-[72%] shrink-0 snap-start flex-col overflow-hidden",
              "rounded-card border border-pa-border bg-pa-surface shadow-soft",
              "dark:shadow-none",
            )}
          >
            <div className="relative h-28 w-full overflow-hidden">
              {meal.image_url ? (
                <RecipeImage2026
                  imageUrl={meal.image_url}
                  alt={meal.name}
                  variant="thumb"
                  mealType={meal.meal_type}
                  className="h-full w-full"
                />
              ) : (
                <MealFallbackPlate2026
                  mealType={meal.meal_type}
                  className="h-full w-full"
                />
              )}
            </div>
            <div className="flex flex-1 flex-col p-3">
              <p className="pa26-micro font-semibold uppercase tracking-wide text-pa-muted">
                {meal.label}
              </p>
              <h3 className="pa26-card-title mt-0.5 line-clamp-2">{meal.name}</h3>
              <p className="pa26-caption mt-1 text-pa-muted">{formatMealMeta(meal)}</p>
              <Button2026
                variant="secondary"
                size="default"
                className="mt-3 w-full text-sm"
                onClick={() => router.push(dishHref(meal))}
              >
                Открыть
              </Button2026>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function RailHeader() {
  return (
    <header className="mb-3">
      <h2 className="pa26-section-title">Сегодня в меню</h2>
      <p className="pa26-caption mt-0.5 text-pa-muted">
        Можно заменить любое блюдо или открыть рецепт
      </p>
    </header>
  );
}
