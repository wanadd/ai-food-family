"use client";

import { HeroCard2026 } from "@/components/planam-2026/cards/HeroCard2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { TrialWelcomeCard2026 } from "@/components/onboarding-2026/TrialWelcomeCard2026";
import type { Home2026TodayMeal } from "@/lib/home/home-2026-data";
import { formatMealMeta } from "@/lib/home/home-2026-data";

type OnboardingWowReveal2026Props = {
  meals: Home2026TodayMeal[];
  menuTitle: string | null;
  amaBalance: number | null;
  onStartDay: () => void;
};

export function OnboardingWowReveal2026({
  meals,
  menuTitle,
  amaBalance,
  onStartDay,
}: OnboardingWowReveal2026Props) {
  const displayMeals = meals.slice(0, 5);

  return (
    <div className="space-y-5">
      <div className="text-center">
        <p className="pa26-hero">Ваш план готов</p>
        {menuTitle ? (
          <p className="pa26-body mt-2 text-pa-muted">{menuTitle}</p>
        ) : (
          <p className="pa26-body mt-2 text-pa-muted">
            Персональные блюда на ближайшие дни — с фото и списком покупок.
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

      <Button2026 variant="primary" size="wide" onClick={onStartDay}>
        Начать день
      </Button2026>
    </div>
  );
}
