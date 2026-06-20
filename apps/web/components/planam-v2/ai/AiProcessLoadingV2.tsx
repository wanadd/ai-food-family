"use client";

import { useEffect, useState } from "react";

import { MealFallbackPlate2026 } from "@/components/home-2026/MealFallbackPlate2026";
import { cn } from "@/lib/planam/cn";

export type AiProcessVariant = "menu" | "shopping" | "pantry" | "wellness";

type AiStep = { title: string; caption: string };

const VARIANT_STEPS: Record<AiProcessVariant, readonly AiStep[]> = {
  menu: [
    { title: "PLANAM собирает меню", caption: "Учитываем цели, запасы дома и предпочтения семьи" },
    { title: "Подбираем блюда", caption: "Ищем вкусные и удобные варианты" },
    { title: "Собираем покупки", caption: "Убираем то, что уже есть дома" },
    { title: "Проверяем баланс", caption: "Смотрим калории, белок и разнообразие" },
  ],
  shopping: [
    { title: "Собираем список покупок", caption: "Убираем продукты, которые уже есть дома" },
    { title: "Группируем по категориям", caption: "Чтобы в магазине было удобно" },
  ],
  pantry: [
    { title: "PLANAM смотрит запасы", caption: "Ищем блюда из того, что уже есть дома" },
    { title: "Подбираем рецепты", caption: "Сначала — продукты, которые скоро испортятся" },
  ],
  wellness: [
    { title: "Анализируем рацион", caption: "Смотрим калории, белок и воду за сегодня" },
    { title: "Готовим рекомендации", caption: "Подбираем, что улучшить мягко и без жёстких правил" },
  ],
};

export type AiProcessLoadingV2Props = {
  active?: boolean;
  variant?: AiProcessVariant;
  title?: string;
  subtitle?: string;
  steps?: readonly AiStep[];
  className?: string;
};

export function AiProcessLoadingV2({
  active = true,
  variant = "menu",
  title,
  subtitle,
  steps,
  className,
}: AiProcessLoadingV2Props) {
  const resolvedSteps = steps ?? VARIANT_STEPS[variant];
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setStepIndex(0);
      return;
    }
    const timer = window.setInterval(() => {
      setStepIndex((i) => (i + 1) % resolvedSteps.length);
    }, 3000);
    return () => window.clearInterval(timer);
  }, [active, resolvedSteps.length]);

  if (!active) {
    return null;
  }

  const step = resolvedSteps[stepIndex] ?? resolvedSteps[0];

  return (
    <div
      className={cn(
        "overflow-hidden rounded-card border border-pa-border bg-pa-surface",
        className,
      )}
      aria-live="polite"
      aria-busy="true"
    >
      <div className="relative h-28 overflow-hidden">
        <MealFallbackPlate2026 mealType="lunch" className="absolute inset-0 opacity-90" />
        <div className="absolute inset-0 bg-gradient-to-t from-pa-surface via-pa-surface/20 to-transparent" />
      </div>
      <div className="space-y-3 px-4 pb-4 pt-2">
        <div className="flex gap-1">
          {resolvedSteps.map((_, i) => (
            <span
              key={i}
              className={cn(
                "h-1 flex-1 rounded-full transition-colors",
                i <= stepIndex ? "bg-sage-500 dark:bg-sage-400" : "bg-pa-border",
              )}
            />
          ))}
        </div>
        <div>
          <p className="pa26-card-title text-sage-800 dark:text-sage-300">
            {title ?? step.title}
          </p>
          <p className="pa26-caption mt-1 text-pa-muted">
            {subtitle ?? step.caption}
          </p>
        </div>
      </div>
    </div>
  );
}
