import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { MenuVariant } from "@/lib/menu/types";
import type { PantryList } from "@/lib/pantry/types";

import { isNutritionProfileComplete } from "@/lib/profile/nutrition-summary";

export type MainAdvice = {
  title: string;
  body: string;
};

export function pickMainAdvice(input: {
  profile: NutritionProfileData | null;
  menu: MenuVariant | null;
  pantry: PantryList | null;
  pantryActiveCount: number;
}): MainAdvice {
  const { profile, menu, pantry, pantryActiveCount } = input;

  if (!isNutritionProfileComplete(profile)) {
    return {
      title: "Начните с профиля",
      body: "Заполните цели и ограничения — тогда советы станут точными и полезными.",
    };
  }

  const expiring =
    pantry?.items.filter(
      (i) =>
        !i.is_expired && i.days_until_expiry >= 0 && i.days_until_expiry <= 3,
    ).length ?? 0;

  if (profile?.nutrition_goal === "lose" && menu) {
    return {
      title: "Не хватает белка",
      body: "Добавьте яйца или творог из запасов — так проще держать сытость на похудении.",
    };
  }

  if (expiring > 0 && menu) {
    return {
      title: "Используйте запасы",
      body: `В холодильнике ${expiring} продукта скоро испортятся — следующее меню можно собрать дешевле.`,
    };
  }

  if (pantryActiveCount > 5 && !menu) {
    return {
      title: "Экономьте на меню",
      body: "Следующее меню можно сделать дешевле за счёт продуктов, которые уже есть дома.",
    };
  }

  if (profile?.nutrition_goal === "child" || profile?.nutrition_goal === "kids") {
    return {
      title: "Детское питание",
      body: "Следите за разнообразием и мягкой текстурой — ПланАм учтёт возраст в меню.",
    };
  }

  return {
    title: "Сегодня всё по плану",
    body: menu
      ? "Следуйте выбранному меню и отмечайте покупки — так рекомендации останутся точными."
      : "Составьте план в разделе «Меню», чтобы получать персональные подсказки.",
  };
}
