"use client";

import { useEffect, useState } from "react";

import { MealFallbackPlate2026 } from "@/components/home-2026/MealFallbackPlate2026";
import { cn } from "@/lib/planam/cn";

const DEFAULT_STEPS = [
  { title: "PLANAM собирает меню", caption: "Учитываем цели, запасы дома и предпочтения семьи" },
  { title: "Подбираем блюда", caption: "Стараемся сделать рацион вкусным и удобным" },
  { title: "Собираем список покупок", caption: "Убираем то, что уже есть дома" },
  { title: "Проверяем баланс", caption: "Смотрим калории, белок и разнообразие" },
] as const;

type AiProcessLoading2026Props = {
  active?: boolean;
  steps?: readonly { title: string; caption: string }[];
  className?: string;
};

export function AiProcessLoading2026({
  active = true,
  steps = DEFAULT_STEPS,
  className,
}: AiProcessLoading2026Props) {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setStepIndex(0);
      return;
    }
    const timer = window.setInterval(() => {
      setStepIndex((i) => (i + 1) % steps.length);
    }, 3200);
    return () => window.clearInterval(timer);
  }, [active, steps.length]);

  if (!active) {
    return null;
  }

  const step = steps[stepIndex] ?? steps[0];

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
          {steps.map((_, i) => (
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
          <p className="pa26-card-title text-sage-800 dark:text-sage-300">{step.title}</p>
          <p className="pa26-caption mt-1 text-pa-muted">{step.caption}</p>
        </div>
      </div>
    </div>
  );
}
