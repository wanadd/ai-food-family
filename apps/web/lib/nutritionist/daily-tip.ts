import { formatGoalLabel } from "@/lib/menu/planner-summary";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { MenuVariant } from "@/lib/menu/types";
import type { PantryList } from "@/lib/pantry/types";

import { isNutritionProfileComplete } from "@/lib/profile/nutrition-summary";

export function buildDailyTip(input: {
  profile: NutritionProfileData | null;
  menu: MenuVariant | null;
  pantry: PantryList | null;
  pantryActiveCount: number;
}): string {
  const { profile, menu, pantry, pantryActiveCount } = input;
  const hasProfile = isNutritionProfileComplete(profile);
  const hasPantry =
    pantryActiveCount > 0 || (pantry?.active_count ?? 0) > 0;
  const expiring =
    pantry?.items.filter(
      (i) =>
        !i.is_expired && i.days_until_expiry >= 0 && i.days_until_expiry <= 3,
    ).length ?? 0;

  if (!hasProfile) {
    return "Заполните профиль питания, чтобы получать точные рекомендации.";
  }

  if (menu) {
    const goal = formatGoalLabel(profile?.nutrition_goal ?? null);
    if (expiring > 0) {
      return `Следуйте плану «${menu.title}» и используйте ${expiring} продуктов из запасов, которые скоро истекают.`;
    }
    if (hasPantry) {
      return `Следуйте текущему плану «${menu.title}» — ПланАм учтёт запасы при следующем меню. Цель: ${goal}.`;
    }
    return `Следуйте текущему плану и отмечайте покупки — так ПланАм точнее подберёт рекомендации. Цель: ${goal}.`;
  }

  if (hasPantry) {
    if (expiring > 0) {
      return `В запасах есть продукты, которые лучше использовать в ближайшие дни — ПланАм подскажет блюда при составлении меню.`;
    }
    return "ПланАм будет учитывать ваши запасы при следующем меню.";
  }

  const goal = profile?.nutrition_goal;
  if (goal === "lose") {
    return "Держите ритм: регулярные приёмы пищи и вода помогают достигать цели без срывов.";
  }
  if (goal === "sport") {
    return "Не забывайте про белок после активности — это поддержит восстановление.";
  }

  return "Составьте план питания в разделе «Меню», чтобы советы стали ещё точнее.";
}
