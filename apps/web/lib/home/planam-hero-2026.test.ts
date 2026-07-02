import { describe, expect, it } from "vitest";

import type { MenuOverview } from "@/lib/menu/overview-types";
import { PLANAM_ROUTES } from "@/lib/planam/routes";

import type { Home2026TodayMeal } from "./home-2026-data";
import {
  greetingForPlanAm,
  isShoppingHeroPriority,
  mealTypesForHour,
  pickNextMealByTime,
  resolvePlanAmHeroState,
  mealPlanTodayHref,
  menuStatusLabel,
} from "./planam-hero-2026";

const meals: Home2026TodayMeal[] = [
  {
    meal_type: "breakfast",
    label: "Завтрак",
    name: "Овсянка",
    recipe_id: 1,
    slot_id: "2026-06-03:breakfast",
    day_index: 1,
    planned_date: "2026-06-03",
    image_url: null,
    prep_time_minutes: 10,
    calories: 300,
  },
  {
    meal_type: "lunch",
    label: "Обед",
    name: "Суп",
    recipe_id: 2,
    slot_id: "2026-06-03:lunch",
    day_index: 1,
    planned_date: "2026-06-03",
    image_url: null,
    prep_time_minutes: 20,
    calories: 400,
  },
  {
    meal_type: "dinner",
    label: "Ужин",
    name: "Курица",
    recipe_id: 3,
    slot_id: "2026-06-03:dinner",
    day_index: 1,
    planned_date: "2026-06-03",
    image_url: null,
    prep_time_minutes: 30,
    calories: 500,
  },
];

function baseOverview(partial: Partial<MenuOverview> = {}): MenuOverview {
  return {
    plan_summary: {
      goal_label: "",
      persons_label: "",
      plan_mode_label: "",
      estimated_cost_rub: null,
      pantry_used_rub: null,
      savings_rub: null,
      has_selected_menu: true,
      menu_title: "Меню",
    },
    why_reasons: [],
    nutritionist_advice: {
      level: "ok",
      title: "В норме",
      body: "",
      freshness_status: "current",
      update_reason: null,
    },
    selected_menu: null,
    pro_coverage: null,
    is_pro: false,
    persons_count: 1,
    plan_mode: null,
    meal_leftovers_count: 0,
    today_meals: [],
    shopping_unchecked_count: 0,
    home_attendance: null,
    settings_summary: null,
    ...partial,
  };
}

describe("planam-hero-2026", () => {
  it("greeting follows time bands", () => {
    expect(greetingForPlanAm(new Date("2026-06-03T08:00:00"))).toBe("Доброе утро");
    expect(greetingForPlanAm(new Date("2026-06-03T14:00:00"))).toBe("Добрый день");
    expect(greetingForPlanAm(new Date("2026-06-03T19:00:00"))).toBe("Добрый вечер");
    expect(greetingForPlanAm(new Date("2026-06-03T02:00:00"))).toBe("Здравствуйте");
  });

  it("picks meal by time of day", () => {
    const morning = new Date("2026-06-03T09:00:00");
    expect(pickNextMealByTime(meals, morning)?.meal_type).toBe("breakfast");
    const afternoon = new Date("2026-06-03T14:00:00");
    expect(pickNextMealByTime(meals, afternoon)?.meal_type).toBe("lunch");
    const evening = new Date("2026-06-03T20:00:00");
    expect(pickNextMealByTime(meals, evening)?.meal_type).toBe("dinner");
  });

  it("mealTypesForHour orders lunch first at noon", () => {
    expect(mealTypesForHour(13)[0]).toBe("lunch");
  });

  it("builds plan today href with canonical slot identity", () => {
    expect(mealPlanTodayHref(meals[1], { action: "1" })).toBe(
      "/plan/today?meal=lunch&menuItemId=2026-06-03%3Alunch&day=1&action=1",
    );
  });

  it("shopping hero when unchecked >= 8", () => {
    expect(isShoppingHeroPriority(8, new Date("2026-06-03T10:00:00"))).toBe(true);
    expect(isShoppingHeroPriority(7, new Date("2026-06-03T10:00:00"))).toBe(false);
  });

  it("shopping hero evening window with >= 3", () => {
    expect(isShoppingHeroPriority(3, new Date("2026-06-03T18:00:00"))).toBe(true);
    expect(isShoppingHeroPriority(2, new Date("2026-06-03T18:00:00"))).toBe(false);
    expect(isShoppingHeroPriority(3, new Date("2026-06-03T16:00:00"))).toBe(false);
  });

  it("resolve no menu state", () => {
    const state = resolvePlanAmHeroState(null, [], false);
    expect(state.variant).toBe("no_menu");
    expect(state.ctaLabel).toBe("Собрать меню");
  });

  it("resolve P0 nutrition profile over meal", () => {
    const overview = baseOverview({
      next_action: {
        id: "complete_nutrition",
        cta_label: "Заполнить",
        redirect_path: "/profile/nutrition",
      },
    });
    const state = resolvePlanAmHeroState(
      overview,
      meals,
      true,
      new Date("2026-06-03T13:00:00"),
    );
    expect(state.variant).toBe("nutrition_profile");
    expect(state.priority).toBe("P0");
  });

  it("resolve meal over shopping when meals exist", () => {
    const overview = baseOverview({ shopping_unchecked_count: 10 });
    const state = resolvePlanAmHeroState(
      overview,
      meals,
      true,
      new Date("2026-06-03T13:00:00"),
    );
    expect(state.variant).toBe("meal");
    expect(state.ctaLabel).toBe("Готовить");
    expect(state.secondaryCtaLabel).toBe("Заменить");
  });

  it("resolve meal over wellness when meals exist", () => {
    const overview = baseOverview({
      nutritionist_advice: {
        level: "update_recommended",
        title: "Рекомендация нутрициолога",
        body: "Обновите профиль",
        freshness_status: "current",
        update_reason: null,
      },
    });
    const state = resolvePlanAmHeroState(
      overview,
      meals,
      true,
      new Date("2026-06-03T13:00:00"),
    );
    expect(state.variant).toBe("meal");
  });

  it("resolve shopping when menu exists but no meals today", () => {
    const overview = baseOverview({ shopping_unchecked_count: 10 });
    const state = resolvePlanAmHeroState(overview, [], true);
    expect(state.variant).toBe("shopping");
    expect(state.ctaHref).toBe(PLANAM_ROUTES.shopping);
  });

  it("does not count explicit empty slots as menu dishes", () => {
    const overview = baseOverview({
      today_meals: [
        { meal_type: "lunch", label: "Обед", name: "Свободно", recipe_id: null },
        {
          meal_type: "dinner",
          label: "Ужин",
          name: "Курица с яблоками",
          recipe_id: 259,
        },
      ],
    });

    expect(menuStatusLabel(overview)).toBe("1 блюдо");
  });

  it("resolve P3 pantry expiry hero", () => {
    const overview = baseOverview({
      pantry_expiring_preview: { name: "Молоко", days_until_expiry: 2 },
    });
    const state = resolvePlanAmHeroState(overview, [], true);
    expect(state.variant).toBe("pantry_expiry");
    expect(state.ctaHref).toBe("/home/leftovers");
  });
});
