"use client";

import { SegmentedTabs } from "@/components/layout/SegmentedTabs";
import { MENU_SUBTABS } from "@/lib/navigation/nav-config";

/**
 * Внутренние вкладки раздела «Меню»: Моё меню · Рецепты · Избранное · Коллекции.
 * Используется и в MenuHub (Моё меню), и в MenuSectionLayout (остальные вкладки),
 * чтобы переключение между ними было единообразным (Этап 2).
 */
export function MenuSubTabs() {
  return (
    <SegmentedTabs
      tabs={MENU_SUBTABS}
      aria-label="Разделы меню"
      className="-mx-1 px-1"
    />
  );
}
