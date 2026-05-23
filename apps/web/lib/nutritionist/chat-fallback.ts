import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { MenuVariant } from "@/lib/menu/types";

import { formatGoalLabel } from "@/lib/menu/planner-summary";

const QUICK_REPLIES: Record<string, string> = {
  protein:
    "Добавьте белок в обед и ужин: яйца, творог, рыбу или бобовые. ПланАм учтёт это при следующем меню.",
  healthier:
    "Больше овощей к каждому приёму, меньше жареного и сладкого между приёмами. В меню выберите режим «Полезно».",
  pantry:
    "Откройте «Запасы» и «Меню» — режим «Использовать запасы» подберёт блюда из того, что уже есть дома.",
  calories:
    "Снижайте калории постепенно: больше овощей, меньше сладкого напитков, не пропускайте белок — так проще удержать цель.",
};

export function getQuickActionReply(
  actionId: string,
  profile: NutritionProfileData | null,
  menu: MenuVariant | null,
): string {
  if (QUICK_REPLIES[actionId]) {
    return QUICK_REPLIES[actionId];
  }
  return buildFallbackReply("", profile, menu);
}

export function buildFallbackReply(
  message: string,
  profile: NutritionProfileData | null,
  menu: MenuVariant | null,
): string {
  const lower = message.toLowerCase();

  if (!profile?.nutrition_goal) {
    return "Заполните профиль питания — тогда смогу давать персональные советы.";
  }

  if (lower.includes("белок") || lower.includes("протеин")) {
    return QUICK_REPLIES.protein;
  }
  if (lower.includes("калор") || lower.includes("похуд")) {
    return QUICK_REPLIES.calories;
  }
  if (lower.includes("запас") || lower.includes("холодильник")) {
    return QUICK_REPLIES.pantry;
  }

  const goal = formatGoalLabel(profile.nutrition_goal);
  if (menu) {
    return `Сейчас у вас план «${menu.title}», цель — ${goal}. Следуйте меню и отмечайте покупки — ПланАм подстроит следующие рекомендации.`;
  }

  return `Ваша цель — ${goal}. Составьте план в разделе «Меню», и я смогу советовать точнее.`;
}
