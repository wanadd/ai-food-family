import type { MenuVariant } from "@/lib/menu/types";
import type { ProgressOverview } from "@/lib/progress/types";

export type DailyMacroBlock = {
  calories: string;
  protein: string;
  fat: string;
  carbs: string;
  water: string;
};

export type DailyStatus = {
  planTitle: string;
  plan: DailyMacroBlock;
  actualTitle: string;
  actual: DailyMacroBlock;
  trainingLine: string;
  menuLine: string;
  todoLine: string | null;
};

function macroLine(
  label: string,
  value: number | null | undefined,
  unit: string,
): string {
  if (value == null) return `${label}: —`;
  return `${label}: ${Math.round(value)} ${unit}`;
}

function buildBlock(
  t: ProgressOverview["targets"] | null | undefined,
  prefix: "plan" | "actual",
  actual: ProgressOverview["daily_actual"] | null | undefined,
): DailyMacroBlock {
  const cal =
    prefix === "plan"
      ? t?.calories_target
      : actual?.meals_logged
        ? actual.calories_consumed
        : 0;
  const protein =
    prefix === "plan"
      ? t?.protein_target_g
      : actual?.meals_logged
        ? actual.protein_consumed_g
        : 0;
  const fat =
    prefix === "plan"
      ? t?.fat_target_g
      : actual?.meals_logged
        ? actual.fat_consumed_g
        : 0;
  const carbs =
    prefix === "plan"
      ? t?.carbs_target_g
      : actual?.meals_logged
        ? actual.carbs_consumed_g
        : 0;
  const water =
    prefix === "plan"
      ? t?.water_target_ml
      : actual?.meals_logged
        ? actual.water_consumed_ml
        : 0;

  return {
    calories: macroLine("Калории", cal, "ккал"),
    protein: macroLine("Белок", protein, "г"),
    fat: macroLine("Жиры", fat, "г"),
    carbs: macroLine("Углеводы", carbs, "г"),
    water:
      water != null
        ? macroLine("Вода", Math.round(water / 1000), "л")
        : "Вода: —",
  };
}

export function buildDailyStatus(input: {
  progress: ProgressOverview | null;
  menu: MenuVariant | null;
  mode: string;
}): DailyStatus {
  const { progress, menu, mode } = input;
  const t = progress?.targets;

  const trainings = progress?.trainings_this_week ?? 0;
  const trainingLine =
    trainings > 0
      ? `Тренировки: ${trainings} на этой неделе`
      : "Тренировки: не отмечены на этой неделе";

  const menuLine = menu
    ? `Меню: выбран план «${menu.title}»`
    : "Меню: не выбрано — составьте в разделе «Меню»";

  let todoLine: string | null = null;
  if (!menu) {
    todoLine = "Составить меню на сегодня";
  } else if (progress?.current_weight_kg == null) {
    todoLine = "Добавить вес для точного прогресса";
  } else if (trainings === 0 && progress?.goal_type === "sport") {
    todoLine = "Отметить тренировку";
  }

  return {
    planTitle: mode === "family" ? "План на сегодня (семья)" : "План на сегодня",
    plan: buildBlock(t, "plan", progress?.daily_actual),
    actualTitle: "Выполнено сегодня",
    actual: buildBlock(t, "actual", progress?.daily_actual),
    trainingLine,
    menuLine,
    todoLine,
  };
}
