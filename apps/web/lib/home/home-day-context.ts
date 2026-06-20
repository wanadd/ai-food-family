import type { MenuOverview } from "@/lib/menu/overview-types";

import { isWellnessHeroPriority } from "./planam-hero-2026";

export type HomeDayContext = {
  title: string;
  text: string;
};

/**
 * AI-совет на Home показываем только при значимом сигнале:
 * Pro-режим с содержательным советом или health-рекомендация
 * (update_recommended / suggest_update). В обычном режиме меню уже
 * собрано по профилю — generic «добавьте белок» не показываем.
 */
export function shouldShowAiTip(overview: MenuOverview | null): boolean {
  if (!overview) {
    return false;
  }
  if (overview.nutritionist_advice_error) {
    return false;
  }
  if (isWellnessHeroPriority(overview)) {
    return true;
  }
  return Boolean(overview.is_pro && overview.nutritionist_advice.body?.trim());
}

/** «Контекст дня» вместо generic-совета: что происходит с планом сейчас. */
export function buildHomeDayContext(overview: MenuOverview | null): HomeDayContext {
  if (!overview?.plan_summary.has_selected_menu) {
    return {
      title: "План на день",
      text: "Меню пока не собрано — PLANAM подберёт рацион под вашу цель.",
    };
  }

  const water = overview.is_pro
    ? (overview.pro_coverage?.water_percent ?? null)
    : null;
  if (water != null && water > 0 && water < 50) {
    return {
      title: "Не забудьте воду",
      text: "Сегодня выпито меньше половины нормы — добавьте пару стаканов.",
    };
  }

  const unchecked = overview.shopping_unchecked_count ?? 0;
  if (unchecked >= 5) {
    return {
      title: "Сегодня",
      text: `Меню собрано по вашей цели. В списке покупок ${unchecked} позиций.`,
    };
  }

  return {
    title: "Сегодня всё по плану",
    text: "Меню собрано с учётом вашей цели.",
  };
}
