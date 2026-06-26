import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { shouldShowBack2026 } from "@/lib/navigation/back-navigation-2026";
import { buildWellnessAdviceCard } from "./wellness-advice";
import { buildWellnessDayStatus } from "./wellness-day-status";
import { buildWellnessMealSlots } from "./wellness-meals";
import { buildWellnessRecommendations } from "./wellness-recommendations";
import { buildWellnessSummaryPhrase } from "./wellness-summary";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));

describe("wellness sprint 1.8d", () => {
  it("renders health summary from actual consumed only", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/wellness/WellnessV2.tsx`,
      "utf8",
    );
    expect(source).toContain('data-testid="wellness-summary"');
    expect(source).toContain("calories_consumed");
    expect(source).not.toContain("usePlanned");
    expect(source).not.toContain("sumMealNutrition");
  });

  it("shows water +250/+500 on wellness", () => {
    const wellness = readFileSync(
      `${repoRoot}/components/planam-v2/wellness/WellnessV2.tsx`,
      "utf8",
    );
    const water = readFileSync(
      `${repoRoot}/components/wellness-2026/WaterIntake2026.tsx`,
      "utf8",
    );
    expect(wellness).toContain("WaterIntake2026 compact");
    expect(water).toContain('data-testid="water-add-250"');
    expect(water).toContain('data-testid={`water-add-${amount}`}');
    expect(water).toContain("Добавили");
  });

  it("renders AI unavailable state gracefully", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/wellness/AiNutritionChatSheet.tsx`,
      "utf8",
    );
    expect(source).toContain("wellness-ai-unavailable");
    expect(source).toContain("временно недоступен");
    expect(source).not.toContain("traceback");
  });

  it("builds actionable advice or on-plan message", () => {
    const waterAdvice = buildWellnessAdviceCard({
      overview: null,
      progress: {
        is_pro: false,
        targets: {
          calories_target: 2000,
          protein_target_g: 100,
          fat_target_g: 70,
          carbs_target_g: 200,
          fiber_target_g: 25,
          water_target_ml: 2000,
          goal_type: "loss",
        },
        daily_actual: {
          calories_consumed: 500,
          protein_consumed_g: 20,
          fat_consumed_g: 10,
          carbs_consumed_g: 50,
          water_consumed_ml: 250,
          meals_logged: 1,
        },
      } as never,
      water: { total_ml: 250, target_ml: 2000 },
      checkins: [],
      profileComplete: true,
    });
    expect(waterAdvice?.action).toBe("add_water");
    expect(waterAdvice?.actionLabel).toBeTruthy();

    const onPlan = buildWellnessAdviceCard({
      overview: {
        plan_summary: { has_selected_menu: true },
        today_meals: [{ meal_type: "breakfast", name: "Овсянка", recipe_id: 1 }],
      } as never,
      progress: {
        targets: { protein_target_g: 100, calories_target: 2000 },
        daily_actual: {
          calories_consumed: 1200,
          protein_consumed_g: 80,
          meals_logged: 2,
        },
      } as never,
      water: { total_ml: 1800, target_ml: 2000 },
      checkins: [
        {
          id: 1,
          meal_type: "breakfast",
          actual_status: "ate_home",
          planned_date: "2026-01-01",
          actual_description: null,
          leftover_servings_delta: null,
          created_at: "2026-01-01T08:00:00Z",
        },
      ],
      profileComplete: true,
    });
    expect(onPlan?.text).toBe("День идёт по плану");
    expect(onPlan?.action).toBeUndefined();
  });

  it("labels recommendations without raw tags", () => {
    const items = buildWellnessRecommendations({
      overview: {
        today_meals: [
          {
            meal_type: "dinner",
            label: "Ужин",
            name: "Индейка с овощами",
            recipe_id: 42,
          },
        ],
      } as never,
      progress: null,
    });
    expect(items[0]?.categoryLabel).toBe("По вашему плану");
    expect(items[0]?.title).toBe("Индейка с овощами");
    expect(JSON.stringify(items)).not.toMatch(/gold_v3|raw_tag/);
  });

  it("shows Pro/training UI states", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/wellness/WellnessV2.tsx`,
      "utf8",
    );
    expect(source).toContain('data-testid="wellness-pro-teaser"');
    expect(source).toContain('data-testid="wellness-pro-enabled"');
    expect(source).toContain('data-testid="wellness-training-block"');
  });

  it("does not show BackButton on root wellness", () => {
    expect(shouldShowBack2026("/wellness")).toBe(false);
    expect(shouldShowBack2026("/wellness/chat")).toBe(true);
  });

  it("builds meal slots without counting planned as eaten", () => {
    const slots = buildWellnessMealSlots({
      overview: {
        today_meals: [
          {
            meal_type: "lunch",
            label: "Обед",
            name: "Суп",
            recipe_id: 10,
          },
        ],
      } as never,
      checkins: [],
    });
    expect(slots[0]?.status).toBe("planned");
    expect(slots[0]?.statusLabel).toBe("Запланировано");
  });

  it("detects day deviations from skipped meals", () => {
    const status = buildWellnessDayStatus({
      overview: {
        today_meals: [
          { meal_type: "lunch", label: "Обед", name: "Суп", recipe_id: 1 },
        ],
      } as never,
      progress: null,
      checkins: [
        {
          id: 1,
          meal_type: "lunch",
          actual_status: "skipped",
          planned_date: "2026-01-01",
          actual_description: null,
          leftover_servings_delta: null,
          created_at: "2026-01-01T12:00:00Z",
        },
      ],
    });
    expect(status.id).toBe("deviations");
  });

  it("builds summary phrase for remaining macros", () => {
    const phrase = buildWellnessSummaryPhrase({
      targets: { calories_target: 2000, protein_target_g: 100 },
      daily_actual: {
        calories_consumed: 1550,
        protein_consumed_g: 65,
        meals_logged: 2,
      },
    } as never);
    expect(phrase).toContain("450 ккал");
    expect(phrase).toContain("белка");
  });
});
