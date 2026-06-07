"use client";

import { useEffect, useState } from "react";

import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchMenuDayNutrition, type DayNutrition } from "@/lib/menu/api";

type Props = {
  /** ISO date (YYYY-MM-DD) for the selected plan day. */
  plannedDate: string;
};

function confidenceHint(day: DayNutrition): string | null {
  switch (day.confidence) {
    case "estimated":
      return "примерно";
    case "low_confidence":
      return "часть рецептов требует уточнения";
    default:
      return null;
  }
}

function Macro({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="pa26-caption font-semibold text-pa-foreground">{value} г</p>
      <p className="pa26-micro mt-0.5 text-pa-muted">{label}</p>
    </div>
  );
}

export function DayNutritionCard2026({ plannedDate }: Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [day, setDay] = useState<DayNutrition | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    if (!initData || !plannedDate) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchMenuDayNutrition(initData, mode, plannedDate)
      .then((data) => {
        if (active) setDay(data);
      })
      .catch(() => {
        if (active) setDay(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [initData, mode, plannedDate]);

  if (loading || !day) {
    return null;
  }

  const isEmpty = day.coverage.total_items === 0;
  const approximate =
    day.confidence === "estimated" || day.confidence === "low_confidence";
  const hint = confidenceHint(day);
  const kcal = day.totals.kcal;
  const target = day.targets.kcal;

  return (
    <Card2026 padding="md" className="mt-3">
      <div className="flex items-baseline justify-between">
        <p className="pa26-caption font-semibold text-pa-foreground">
          Питание сегодня
        </p>
        {hint ? (
          <span className="pa26-micro text-pa-muted">{hint}</span>
        ) : null}
      </div>

      {isEmpty ? (
        <p className="pa26-body mt-2 text-pa-muted">
          Добавьте блюда в меню, и я посчитаю КБЖУ
        </p>
      ) : day.confidence === "unavailable" ? (
        <p className="pa26-body mt-2 text-pa-muted">
          КБЖУ пока нельзя посчитать — часть рецептов требует уточнения
        </p>
      ) : (
        <>
          <p className="pa26-hero mt-1 text-pa-foreground">
            {approximate ? "≈" : ""}
            {kcal}
            {target ? (
              <span className="pa26-body text-pa-muted"> / {target} ккал</span>
            ) : (
              <span className="pa26-body text-pa-muted"> ккал</span>
            )}
          </p>
          {target ? (
            <div className="mt-2 h-2 w-full overflow-hidden rounded-pill bg-pa-elevated">
              <div
                className="h-full rounded-pill bg-pa-brand"
                style={{
                  width: `${Math.min(100, Math.round((kcal / target) * 100))}%`,
                }}
              />
            </div>
          ) : null}
          <div className="mt-3 grid grid-cols-3 gap-2">
            <Macro label="Белки" value={day.totals.protein} />
            <Macro label="Жиры" value={day.totals.fat} />
            <Macro label="Углеводы" value={day.totals.carbs} />
          </div>
          {day.warnings.length > 0 ? (
            <p className="mt-3 pa26-micro text-pa-muted">{day.warnings[0]}</p>
          ) : null}
        </>
      )}
    </Card2026>
  );
}
