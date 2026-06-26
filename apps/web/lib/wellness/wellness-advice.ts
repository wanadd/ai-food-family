import type { MealCheckin } from "@/lib/meal-checkins/api";
import { MEAL_TYPE_LABELS } from "@/lib/meal-checkins/constants";
import type { MenuOverview } from "@/lib/menu/overview-types";
import type { ProgressOverview } from "@/lib/progress/types";
import type { WaterToday } from "@/lib/water-intake/api";

const GLASS_ML = 250;

export type WellnessAdviceAction =
  | "add_water"
  | "open_meal_sheet"
  | "open_snack_sheet"
  | "open_ai"
  | "show_recipes"
  | "setup_nutrition";

export type WellnessAdviceCard = {
  text: string;
  action?: WellnessAdviceAction;
  actionLabel?: string;
};

function skippedMealLabel(checkins: MealCheckin[]): string | null {
  for (const row of checkins) {
    if (row.actual_status === "skipped") {
      return MEAL_TYPE_LABELS[row.meal_type] ?? row.meal_type;
    }
  }
  return null;
}

export function buildWellnessAdviceCard(input: {
  overview: MenuOverview | null;
  progress: ProgressOverview | null;
  water: WaterToday | null;
  checkins: MealCheckin[];
  profileComplete: boolean;
}): WellnessAdviceCard | null {
  const { overview, progress, water, checkins, profileComplete } = input;

  if (!profileComplete) {
    return {
      text: "Задайте цель питания — подскажем ритм дня и точные нормы.",
      action: "setup_nutrition",
      actionLabel: "Настроить питание",
    };
  }

  const targets = progress?.targets;
  const actual = progress?.daily_actual;
  const waterTarget = water?.target_ml ?? targets?.water_target_ml ?? null;
  const waterTotal = water?.total_ml ?? actual?.water_consumed_ml ?? 0;

  if (waterTarget && waterTarget > 0) {
    const remainingMl = Math.max(0, waterTarget - waterTotal);
    if (remainingMl >= GLASS_ML) {
      const glasses = Math.ceil(remainingMl / GLASS_ML);
      return {
        text: `Вы отстаёте по воде на ${remainingMl} мл — это около ${glasses} стакан${glasses > 1 ? "ов" : "а"}.`,
        action: "add_water",
        actionLabel: "Добавить стакан",
      };
    }
  }

  const proteinTarget = targets?.protein_target_g;
  const proteinEaten = actual?.protein_consumed_g ?? 0;
  if (
    proteinTarget &&
    proteinTarget > 0 &&
    actual?.meals_logged &&
    proteinEaten / proteinTarget < 0.55
  ) {
    return {
      text: "Белка пока мало — на ужин лучше выбрать блюдо с индейкой или рыбой.",
      action: "show_recipes",
      actionLabel: "Показать варианты",
    };
  }

  const skipped = skippedMealLabel(checkins);
  if (skipped) {
    return {
      text: `${skipped} пропущен. Не нужно добирать всё сразу — можно добавить лёгкий перекус.`,
      action: "open_snack_sheet",
      actionLabel: "Добавить перекус",
    };
  }

  const planned =
    overview?.today_meals.filter((m) => m.name?.trim()).length ?? 0;
  const hasEaten = checkins.some((c) =>
    ["ate_home", "ate_work", "ate_cafe", "ate_restaurant", "ate_delivery", "ate_other", "completed"].includes(
      c.actual_status,
    ),
  );

  if (planned > 0 && !hasEaten) {
    return {
      text: "Отметьте приёмы пищи — так виден реальный прогресс дня.",
      action: "open_meal_sheet",
      actionLabel: "Отметить еду",
    };
  }

  if (!overview?.plan_summary.has_selected_menu) {
    return {
      text: "Составьте меню — персональные советы станут точнее.",
      action: "show_recipes",
      actionLabel: "К меню",
    };
  }

  return { text: "День идёт по плану" };
}
