"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  createMealCheckin,
  fetchTodayMealCheckins,
  type MealCheckin,
} from "@/lib/meal-checkins/api";
import {
  MEAL_CHECKIN_OPTIONS,
  MEAL_TYPE_LABELS,
  type MealCheckinStatus,
} from "@/lib/meal-checkins/constants";
import type { MenuVariant } from "@/lib/menu/types";

type Props = {
  menu: MenuVariant;
  plannedDate: string;
  onUpdated?: () => void;
};

export function MealCheckinPanel({ menu, plannedDate, onUpdated }: Props) {
  const { initData } = useTelegram();
  const { mode, context } = useAppMode();
  const [checkins, setCheckins] = useState<MealCheckin[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [memberId, setMemberId] = useState<number | null>(null);

  const familyMembers = useMemo(() => {
    if (mode !== "family" || !context?.family?.members?.length) {
      return [];
    }
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

  const mainMeals = menu.meals.filter((m) =>
    ["breakfast", "lunch", "dinner", "snack"].includes(m.meal_type),
  );

  if (mainMeals.length === 0) return null;

  const isToday = plannedDate === new Date().toISOString().slice(0, 10);

  return (
    <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
      <p className="text-sm font-bold text-stone-900">
        {isToday ? "Где вы поели сегодня" : "Где вы поели"}
      </p>
      <p className="mt-1 text-xs text-stone-500">
        Учтём калории в нутрициологе. Домашние блюда не списываем при питании вне
        дома.
      </p>

      {familyMembers.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {familyMembers.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMemberId(m.id)}
              className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition ${
                memberId === m.id
                  ? "bg-emerald-600 text-white"
                  : "bg-stone-100 text-stone-700"
              }`}
            >
              {m.display_name}
            </button>
          ))}
        </div>
      ) : null}

      <ul className="mt-4 space-y-4">
        {mainMeals.map((meal) => {
          const saveKey = `${memberId ?? 0}:${meal.meal_type}`;
          const current = statusByMeal.get(meal.meal_type);
          return (
            <li key={meal.meal_type}>
              <p className="text-sm font-semibold text-stone-800">
                {MEAL_TYPE_LABELS[meal.meal_type] ?? meal.meal_type}: {meal.name}
              </p>
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
                    className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition ${
                      current === opt.value
                        ? "bg-emerald-600 text-white"
                        : "bg-stone-100 text-stone-700"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </li>
          );
        })}
      </ul>

      <Link
        href="/menu/leftovers"
        className="mt-4 flex min-h-[40px] items-center justify-center rounded-xl border border-dashed border-stone-200 bg-stone-50 px-3 text-xs font-semibold text-emerald-800"
      >
        Остатки блюд
      </Link>
    </section>
  );
}
