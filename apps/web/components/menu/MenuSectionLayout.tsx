import type { ReactNode } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { MenuSubTabs } from "@/components/menu/MenuSubTabs";

type MenuSectionLayoutProps = {
  subtitle?: string;
  children: ReactNode;
  contentClassName?: string;
};

/**
 * Оболочка внутренних вкладок «Меню» (Рецепты / Избранное / Коллекции).
 * Заголовок «Меню» + сегментированные вкладки сверху + контент вкладки.
 * «Моё меню» (MenuHub) рендерит вкладки самостоятельно из-за своих состояний
 * загрузки/ошибки, поэтому общий layout здесь — для остальных вкладок (Этап 2).
 */
export function MenuSectionLayout({
  subtitle,
  children,
  contentClassName = "space-y-4 pb-28",
}: MenuSectionLayoutProps) {
  return (
    <ScreenLayout title="Меню" subtitle={subtitle} contentClassName={contentClassName}>
      <MenuSubTabs />
      {children}
    </ScreenLayout>
  );
}
