import type { MenuOverview } from "@/lib/menu/overview-types";
import type { ProgressOverview } from "@/lib/progress/types";
import type { WaterToday } from "@/lib/water-intake/api";

const GLASS_ML = 250;
const MAX_LEN = 120;

function clampInsight(text: string): string {
  const oneLine = text.replace(/\s+/g, " ").trim();
  if (oneLine.length <= MAX_LEN) {
    return oneLine;
  }
  return `${oneLine.slice(0, MAX_LEN - 1).trim()}…`;
}

function overviewInsightLine(
  advice: MenuOverview["nutritionist_advice"] | null | undefined,
): string | null {
  if (!advice || advice.freshness_status === "no_menu") {
    return null;
  }
  const body = advice.body?.trim();
  if (body) {
    return clampInsight(body);
  }
  const title = advice.title?.trim();
  if (title && advice.level !== "ok") {
    return clampInsight(title);
  }
  return null;
}

export function buildWellnessInsight(input: {
  overview: MenuOverview | null;
  progress: ProgressOverview | null;
  water: WaterToday | null;
  profileComplete: boolean;
  mealsCompleted: number;
}): string | null {
  const { overview, progress, water, profileComplete, mealsCompleted } = input;

  if (!profileComplete) {
    return "Задайте цель питания — подскажем ритм дня.";
  }

  const fromOverview = overviewInsightLine(overview?.nutritionist_advice);
  if (fromOverview) {
    return fromOverview;
  }

  const targets = progress?.targets;
  const actual = progress?.daily_actual;
  const waterTarget = water?.target_ml ?? targets?.water_target_ml ?? null;
  const waterTotal = water?.total_ml ?? actual?.water_consumed_ml ?? 0;

  if (waterTarget && waterTarget > 0) {
    const remainingMl = Math.max(0, waterTarget - waterTotal);
    const glassesLeft = Math.ceil(remainingMl / GLASS_ML);
    if (glassesLeft >= 2) {
      return `Осталось выпить ${glassesLeft} стаканов воды.`;
    }
    if (glassesLeft === 1) {
      return "Осталось выпить 1 стакан воды.";
    }
  }

  if (actual?.meals_logged && targets?.protein_target_g) {
    const proteinPct =
      (actual.protein_consumed_g / targets.protein_target_g) * 100;
    if (proteinPct < 55) {
      return "Сегодня мало белка — добавьте белковый перекус.";
    }
  }

  if (mealsCompleted > 0 && mealsCompleted < 2) {
    return "Завтрак выполнен — отличный старт дня.";
  }

  if (mealsCompleted >= 2) {
    return "Сегодня вы движетесь по плану — так держать.";
  }

  if (!overview?.plan_summary.has_selected_menu) {
    return "Составьте меню — персональные советы станут точнее.";
  }

  return "Отметьте приёмы пищи — так виден реальный прогресс дня.";
}
