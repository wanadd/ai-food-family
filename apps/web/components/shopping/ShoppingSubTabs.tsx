"use client";

import { SegmentedTabs } from "@/components/layout/SegmentedTabs";
import { SHOPPING_SUBTABS } from "@/lib/navigation/nav-config";

/**
 * Внутренние вкладки раздела «Покупки»: Покупки · Запасы · Остатки (Этап 3).
 * Единый ответ на вопрос «что купить?»: список покупок, запасы дома и остатки блюд.
 */
export function ShoppingSubTabs() {
  return (
    <SegmentedTabs
      tabs={SHOPPING_SUBTABS}
      aria-label="Разделы покупок"
      className="-mx-1 px-1"
    />
  );
}
