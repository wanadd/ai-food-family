import { describe, expect, it } from "vitest";

import {
  buildPlanTodaySearchParams,
  parsePlanTodayDay,
  planTodayPath,
  planTodayReturnPath,
  planTodayScrollQuery,
  resolvePlanTodayDay,
} from "./plan-today-nav";
import type { MenuVariant } from "@/lib/menu/types";

function menuTwoDays(): MenuVariant {
  return {
    variant: "balanced",
    title: "Test",
    tagline: "",
    explanation: "",
    estimated_daily_cost: null,
    total_prep_minutes: 60,
    ingredients: [{ name: "Вода", amount: "1 л" }],
    plan_days: 2,
    days: [
      {
        day_index: 1,
        label: "День 1",
        date_iso: "2026-06-10",
        meals: [
          {
            meal_type: "lunch",
            name: "Суп",
            description: "",
            prep_time_minutes: 30,
          },
        ],
      },
      {
        day_index: 2,
        label: "День 2",
        date_iso: "2026-06-11",
        meals: [
          {
            meal_type: "dinner",
            name: "Курица",
            description: "",
            prep_time_minutes: 35,
          },
        ],
      },
    ],
    meals: [],
  };
}

describe("planTodayNav", () => {
  it("parses day from query", () => {
    expect(parsePlanTodayDay("2", 1)).toBe(2);
    expect(parsePlanTodayDay("bad", 1)).toBe(1);
  });

  it("builds plan today path with day query", () => {
    expect(planTodayPath(2)).toBe("/plan/today?day=2");
    expect(planTodayPath(3)).toBe("/plan/today?day=3");
  });

  it("returns same dayIndex from URL param", () => {
    expect(resolvePlanTodayDay("3", menuTwoDays())).toBe(3);
  });

  it("uses default day when query is absent", () => {
    expect(resolvePlanTodayDay(null, menuTwoDays())).toBe(1);
  });

  it("preserves day in return path", () => {
    expect(planTodayReturnPath(2, menuTwoDays())).toBe("/plan/today?day=2");
    expect(planTodayReturnPath(3, menuTwoDays())).toBe("/plan/today?day=3");
  });

  it("updates day param in search params", () => {
    const next = buildPlanTodaySearchParams(new URLSearchParams("saved=1"), 2);
    expect(next.get("day")).toBe("2");
    expect(next.get("saved")).toBeNull();
  });

  it("uses stable scroll query key per day", () => {
    expect(planTodayScrollQuery(2)).toBe("day=2");
  });
});
