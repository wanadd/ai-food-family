import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { getNutritionGoalLabel } from "@/lib/profile/nutrition-summary";

export function buildAdviceWhy(profile: NutritionProfileData | null): string[] {
  if (!profile?.nutrition_goal) {
    return ["Заполните цель в профиле питания — так советы станут персональными."];
  }
  const goal = getNutritionGoalLabel(profile) ?? profile.nutrition_goal;
  const gd = profile.goal_details;
  const current = gd?.current_weight_kg ?? profile.weight_kg;
  const target = gd?.target_weight_kg;
  const lines: string[] = [`Цель: ${goal}`];
  if (current != null) lines.push(`Текущий вес: ${current} кг`);
  if (target != null) lines.push(`Цель по весу: ${target} кг`);

  switch (profile.nutrition_goal) {
    case "lose":
      lines.push(
        "Поэтому рекомендуется:",
        "• увеличить белок",
        "• контролировать калории",
        "• пить больше воды",
      );
      break;
    case "gain":
      lines.push(
        "Поэтому рекомендуется:",
        "• добавить калорийности",
        "• не пропускать белок",
        "• планировать перекусы",
      );
      break;
    case "sport":
      lines.push(
        "Поэтому рекомендуется:",
        "• следить за белком после нагрузки",
        "• пить воду до и после тренировки",
        "• не недоедать углеводы",
      );
      break;
    default:
      lines.push(
        "Поэтому рекомендуется:",
        "• придерживаться выбранного меню",
        "• отмечать вес и самочувствие",
      );
  }
  return lines;
}
