"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { Sheet } from "@/components/ui/Sheet";
import { useTelegram } from "@/components/TelegramProvider";
import {
  createMealCheckin,
  fetchTodayMealCheckins,
  type MealCheckin,
} from "@/lib/meal-checkins/api";
import {
  MEAL_CHECKIN_OPTIONS,
  type MealCheckinStatus,
} from "@/lib/meal-checkins/constants";
import { MEAL_LABELS } from "@/lib/menu/labels";
import type { MenuMeal, MenuVariant } from "@/lib/menu/types";

const MAIN_MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"] as const;

type Props = {
  menu: MenuVariant;
  plannedDate: string;
  onReplaceMeal: (mealIndex: number) => void;
  onUpdated?: () => void;
};

export function MenuDayOverview({
  menu,
  plannedDate,
  onReplaceMeal,
  onUpdated,
}: Props) {
  const { initData } = useTelegram();
  const { mode, context } = useAppMode();
  const [checkins, setCheckins] = useState<MealCheckin[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [memberId, setMemberId] = useState<number | null>(null);
  const [detailMeal, setDetailMeal] = useState<{
    meal: MenuMeal;
    index: number;
  } | null>(null);

  const familyMembers = useMemo(() => {
    if (mode !== "family" || !context?.family?.members?.length) return [];
    return context.family.members;
  }, [mode, context]);

  useEffect(() => {
    if (familyMembers.length > 0) {
      setMemberId((prev) =>
        prev && familyMembers.some((m) => m.id === prev)
          ? prev
          : familyMembers[0].id,
      );
    } else {
      setMemberId(null);
    }
  }, [familyMembers]);

  const load = useCallback(async () => {
    if (!initData) return;
    setCheckins(await fetchTodayMealCheckins(initData, mode, plannedDate));
  }, [initData, mode, plannedDate]);

  useEffect(() => {
    void load();
  }, [load]);

  const statusByMeal = new Map<string, string>();
  for (const row of checkins) {
    const rowMember = row.family_member_id ?? null;
    const activeMember = memberId ?? null;
    if (rowMember !== activeMember) continue;
    statusByMeal.set(row.meal_type, row.actual_status);
  }

  async function markMeal(
    mealType: string,
    status: MealCheckinStatus,
    name: string,
    recipeId?: number | null,
  ) {
    if (!initData) return;
    const key = `${memberId ?? 0}:${mealType}`;
    setSaving(key);
    try {
      await createMealCheckin(initData, mode, {
        meal_type: mealType,
        actual_status: status,
        planned_date: plannedDate,
        family_member_id: memberId ?? undefined,
        actual_description: name,
        recipe_id: recipeId ?? undefined,
      });
      await load();
      onUpdated?.();
    } finally {
      setSaving(null);
    }
  }

  const meals = menu.meals
    .map((meal, index) => ({ meal, index }))
    .filter(({ meal }) =>
      MAIN_MEAL_TYPES.includes(meal.meal_type as (typeof MAIN_MEAL_TYPES)[number]),
    );

  if (meals.length === 0) return null;

  return (
    <>
      <section className="pa-card p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
          Сегодня в плане
        </p>

        {familyMembers.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {familyMembers.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMemberId(m.id)}
                className={`pa-chip px-2.5 py-1 text-[11px] ${
                  memberId === m.id
                    ? "border-sage-500 bg-sage-600 text-white"
                    : "border-cream-border bg-cream-deep text-graphite-700"
                }`}
              >
                {m.display_name}
              </button>
            ))}
          </div>
        ) : null}

        <ul className="mt-4 space-y-4">
          {meals.map(({ meal, index }) => {
            const saveKey = `${memberId ?? 0}:${meal.meal_type}`;
            const current = statusByMeal.get(meal.meal_type);
            return (
              <li
                key={`${meal.meal_type}-${index}`}
                className="border-b border-cream-border pb-4 last:border-0 last:pb-0"
              >
                <button
                  type="button"
                  onClick={() => setDetailMeal({ meal, index })}
                  className="w-full text-left"
                >
                  <p className="text-xs font-semibold uppercase text-sage-700">
                    {MEAL_LABELS[meal.meal_type]}
                  </p>
                  <p className="mt-0.5 font-semibold text-graphite-900">{meal.name}</p>
                  <p className="mt-0.5 line-clamp-2 text-sm text-graphite-500">
                    {meal.description}
                  </p>
                  <p className="mt-1 text-xs text-graphite-400">
                    {meal.prep_time_minutes} мин
                    {meal.calories_estimate
                      ? ` · ~${Math.round(meal.calories_estimate)} ккал`
                      : ""}
                  </p>
                </button>

                <div className="mt-2 flex flex-wrap gap-1.5">
                  {MEAL_CHECKIN_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      disabled={saving === saveKey}
                      onClick={() =>
                        void markMeal(
                          meal.meal_type,
                          opt.value,
                          meal.name,
                          meal.recipe_id,
                        )
                      }
                      className={`pa-chip px-2 py-1 text-[11px] ${
                        current === opt.value
                          ? "border-sage-500 bg-sage-600 text-white"
                          : "border-cream-border bg-cream-deep text-graphite-700"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => onReplaceMeal(index)}
                  className="pa-btn-ghost mt-2 text-xs text-sage-700"
                >
                  Заменить блюдо
                </button>
              </li>
            );
          })}
        </ul>
      </section>

      <Sheet
        open={detailMeal !== null}
        title={detailMeal ? MEAL_LABELS[detailMeal.meal.meal_type] : ""}
        onClose={() => setDetailMeal(null)}
      >
        {detailMeal ? (
          <div className="space-y-3">
            <p className="text-lg font-bold text-graphite-900">
              {detailMeal.meal.name}
            </p>
            <p className="text-sm text-graphite-600">{detailMeal.meal.description}</p>
            <p className="text-xs text-graphite-500">
              {detailMeal.meal.prep_time_minutes} мин
              {detailMeal.meal.calories_estimate
                ? ` · ~${Math.round(detailMeal.meal.calories_estimate)} ккал`
                : ""}
            </p>
            {detailMeal.meal.recipe_id ? (
              <Link
                href={`/recipes/${detailMeal.meal.recipe_id}`}
                className="pa-btn-primary inline-flex min-h-[44px] items-center px-4 text-sm"
                onClick={() => setDetailMeal(null)}
              >
                Открыть рецепт
              </Link>
            ) : null}
            <button
              type="button"
              onClick={() => {
                onReplaceMeal(detailMeal.index);
                setDetailMeal(null);
              }}
              className="pa-btn w-full py-2.5 text-sm"
            >
              Заменить блюдо
            </button>
          </div>
        ) : null}
      </Sheet>
    </>
  );
}
