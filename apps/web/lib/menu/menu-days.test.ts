import { describe, expect, it } from "vitest";

import { mergeReplaceResult } from "./menu-days";
import type { MenuMeal, MenuVariant } from "./types";

const meal = (
  meal_type: MenuMeal["meal_type"],
  name: string,
  recipe_id: number,
): MenuMeal => ({
  meal_type,
  name,
  description: "",
  prep_time_minutes: 10,
  recipe_id,
});

const baseMenu: MenuVariant = {
  variant: "balanced",
  title: "Week",
  tagline: "",
  explanation: "",
  estimated_daily_cost: null,
  total_prep_minutes: 30,
  ingredients: [{ name: "Old", amount: "1 pc" }],
  meals: [
    meal("breakfast", "Breakfast A", 1),
    meal("lunch", "Lunch B", 2),
    meal("dinner", "Dinner C", 3),
  ],
  plan_days: 7,
  days: [
    {
      day_index: 1,
      label: "Day 1",
      date_iso: "2026-06-05",
      meals: [
        meal("breakfast", "Breakfast A", 1),
        meal("lunch", "Lunch B", 2),
        meal("dinner", "Dinner C", 3),
      ],
    },
    {
      day_index: 2,
      label: "Day 2",
      date_iso: "2026-06-06",
      meals: [meal("lunch", "Day 2 Lunch", 22)],
    },
  ],
};

describe("mergeReplaceResult", () => {
  it("copies only the requested meal index back into the full menu", () => {
    const replaceResult: MenuVariant = {
      ...baseMenu,
      meals: [
        meal("breakfast", "Random Breakfast", 91),
        meal("lunch", "New Lunch X", 4),
        meal("dinner", "Random Dinner", 93),
        meal("snack", "Random Snack", 94),
      ],
      ingredients: [{ name: "New", amount: "1 pc" }],
    };

    const merged = mergeReplaceResult(baseMenu, replaceResult, 1, 1);

    expect(merged.days?.[0].meals.map((item) => item.name)).toEqual([
      "Breakfast A",
      "New Lunch X",
      "Dinner C",
    ]);
    expect(merged.days?.[1].meals.map((item) => item.name)).toEqual([
      "Day 2 Lunch",
    ]);
    expect(merged.meals.map((item) => item.name)).toEqual([
      "Breakfast A",
      "New Lunch X",
      "Dinner C",
    ]);
  });
});
