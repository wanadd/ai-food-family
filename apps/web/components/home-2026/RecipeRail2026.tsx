"use client";

import { useRouter } from "next/navigation";

import { HeroCard2026 } from "@/components/planam-2026/cards/HeroCard2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import {
  formatMealMeta,
  type Home2026TodayMeal,
} from "@/lib/home/home-2026-data";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

type RecipeRail2026Props = {
  meals: Home2026TodayMeal[];
  loading?: boolean;
  hasMenu: boolean;
  isNewUser?: boolean;
  onCreateMenu?: () => void;
};

export function RecipeRail2026({
  meals,
  loading = false,
  hasMenu,
  isNewUser = false,
  onCreateMenu,
}: RecipeRail2026Props) {
  const router = useRouter();
  const use2026 = isPlanamUi2026Enabled();

  if (loading) {
    return (
      <section className="pt-6" aria-busy="true">
        <p className="pa26-section-title mb-3 px-4">Сегодня</p>
        <div className="flex gap-3 overflow-hidden px-4 pb-2">
          {[1, 2, 3].map((i) => (
            <Skeleton2026
              key={i}
              variant="rect"
              aspectRatio="4/3"
              className="h-[200px] w-[72%] max-w-[320px] shrink-0 rounded-card"
            />
          ))}
        </div>
      </section>
    );
  }

  if (!hasMenu || meals.length === 0) {
    return (
      <section className="px-4 pt-6">
        <EmptyState2026
          icon={<span aria-hidden>🍽</span>}
          title={isNewUser ? "Ваш план начинается здесь" : "Пока нет блюд на сегодня"}
          description={
            isNewUser
              ? "Создайте первое меню — и лента наполнится блюдами с фото из вашего плана."
              : "Сгенерируйте меню на неделю, чтобы увидеть блюда дня в ленте."
          }
          actionLabel="Создать меню"
          onAction={onCreateMenu ?? (() => router.push("/menu/generate"))}
        />
      </section>
    );
  }

  return (
    <section className="pt-6" aria-label="Блюда на сегодня">
      <p className="pa26-section-title mb-3 px-4">Сегодня</p>
      <div className="flex gap-3 overflow-x-auto px-4 pb-2 scroll-smooth snap-x snap-mandatory">
        {meals.map((meal) => (
          <HeroCard2026
            key={`${meal.meal_type}-${meal.recipe_id ?? meal.name}`}
            className="snap-start"
            title={meal.name}
            caption={formatMealMeta(meal)}
            imageUrl={meal.image_url}
            imageAlt={meal.name}
            aspect="4:3"
            onClick={() =>
              router.push(
                meal.recipe_id
                  ? `/recipes/${meal.recipe_id}`
                  : use2026
                    ? "/plan/today"
                    : "/menu/current",
              )
            }
          />
        ))}
      </div>
    </section>
  );
}
