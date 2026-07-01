"use client";

import { HeroCard2026 } from "@/components/planam-2026/cards/HeroCard2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { TrialWelcomeCard2026 } from "@/components/onboarding-2026/TrialWelcomeCard2026";
import { formatMenuDuration } from "@/lib/menu/duration-options";
import type { Home2026TodayMeal } from "@/lib/home/home-2026-data";
import { formatMealMeta } from "@/lib/home/home-2026-data";

type OnboardingWowReveal2026Props = {
  meals: Home2026TodayMeal[];
  menuTitle: string | null;
  amaBalance: number | null;
  planDays: number;
  onOpenMenu: () => void;
  onOpenShopping: () => void;
  onNotificationsLater: () => void;
};

export function OnboardingWowReveal2026({
  meals,
  menuTitle,
  amaBalance,
  planDays,
  onOpenMenu,
  onOpenShopping,
  onNotificationsLater,
}: OnboardingWowReveal2026Props) {
  const displayMeals = meals.slice(0, 5);
  const duration = formatMenuDuration(planDays);

  return (
    <div className="space-y-5">
      <div className="text-center">
        <p className="pa26-hero">Меню готово</p>
        {menuTitle ? (
          <p className="pa26-body mt-2 text-pa-muted">
            {menuTitle} · план на {duration} сохранён.
          </p>
        ) : (
          <p className="pa26-body mt-2 text-pa-muted">
            План на {duration} сохранён. Список покупок уже подготовлен.
          </p>
        )}
      </div>

      <div className="flex gap-3 overflow-x-auto pb-1 scroll-smooth snap-x snap-mandatory">
        {displayMeals.map((meal) => (
          <HeroCard2026
            key={`${meal.meal_type}-${meal.name}`}
            className="snap-start"
            title={meal.name}
            caption={formatMealMeta(meal)}
            imageUrl={meal.image_url}
            aspect="4:3"
          />
        ))}
      </div>

      {displayMeals.length === 0 ? (
        <p className="pa26-caption text-center text-pa-muted">
          Блюда появятся в ленте на главной — откройте Дом.
        </p>
      ) : null}

      <TrialWelcomeCard2026 amaBalance={amaBalance} />

      <Button2026 variant="primary" size="wide" onClick={onOpenMenu}>
        Открыть меню
      </Button2026>
      <Button2026 variant="secondary" size="wide" onClick={onOpenShopping}>
        Посмотреть покупки
      </Button2026>
      <Button2026 variant="ghost" size="wide" onClick={onNotificationsLater}>
        Уведомления позже
      </Button2026>
    </div>
  );
}
