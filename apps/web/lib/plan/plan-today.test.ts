import { describe, expect, it } from "vitest";

import { enrichMealsForDay } from "./plan-today";
import type { MenuVariant } from "@/lib/menu/types";

function menuWithImages(): MenuVariant {
  return {
    variant: "balanced",
    title: "Test",
    tagline: "",
    explanation: "",
    estimated_daily_cost: null,
    total_prep_minutes: 90,
    ingredients: [{ name: "Вода", amount: "1 л" }],
    plan_days: 2,
    days: [
      {
        day_index: 1,
        label: "День 1",
        date_iso: "2026-06-10",
        meals: [
          {
            meal_type: "breakfast",
            name: "Котлеты",
            description: "",
            prep_time_minutes: 30,
            recipe_id: 256,
            image_url: "/recipe-images/256/card_800.webp",
          },
        ],
      },
      {
        day_index: 2,
        label: "День 2",
        date_iso: "2026-06-11",
        meals: [
          {
            meal_type: "lunch",
            name: "Перловка",
            description: "",
            prep_time_minutes: 35,
            recipe_id: 257,
            image_url: "/recipe-images/257/card_800.webp",
          },
        ],
      },
    ],
    meals: [],
  };
}

describe("enrichMealsForDay images", () => {
  it("uses meal.image_url from menu payload for non-today days", () => {
    const rows = enrichMealsForDay(menuWithImages(), 2, [], new Map());
    expect(rows).toHaveLength(1);
    expect(rows[0]?.imageUrl).toBe("/recipe-images/257/card_800.webp");
  });

  it("keeps different image_url per recipe_id across days", () => {
    const day1 = enrichMealsForDay(menuWithImages(), 1, [], new Map());
    const day2 = enrichMealsForDay(menuWithImages(), 2, [], new Map());
    expect(day1[0]?.imageUrl).toBe("/recipe-images/256/card_800.webp");
    expect(day2[0]?.imageUrl).toBe("/recipe-images/257/card_800.webp");
    expect(day1[0]?.imageUrl).not.toBe(day2[0]?.imageUrl);
  });
});
