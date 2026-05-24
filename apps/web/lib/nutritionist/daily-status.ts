import type { MenuVariant } from "@/lib/menu/types";
import type { ProgressOverview } from "@/lib/progress/types";

export type DailyStatus = {
  title: string;
  caloriesLine: string;
  proteinLine: string;
  waterLine: string;
  trainingLine: string;
  menuLine: string;
  todoLine: string | null;
};

export function buildDailyStatus(input: {
  progress: ProgressOverview | null;
  menu: MenuVariant | null;
  mode: string;
}): DailyStatus {
  const { progress, menu, mode } = input;
  const t = progress?.targets;

  const title =
    mode === "family" ? "Семья сегодня" : "Мой день";

  const caloriesLine =
    t?.calories_target != null
      ? `Калории: план ~${t.calories_target} ккал (отметьте приёмы пищи)`
      : "Калории: задайте цель в профиле питания";

  const proteinLine =
    t?.protein_target_g != null
      ? `Белок: цель ~${t.protein_target_g} г`
      : "Белок: укажите цель в профиле";

  const waterLine =
    t?.water_target_ml != null
      ? `Вода: ~${Math.round(t.water_target_ml / 1000)} л в день`
      : "Вода: пейте регулярно в течение дня";

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
    title,
    caloriesLine,
    proteinLine,
    waterLine,
    trainingLine,
    menuLine,
    todoLine,
  };
}
