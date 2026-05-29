import type { ReactNode } from "react";

import { ShoppingSubTabs } from "@/components/shopping/ShoppingSubTabs";

type ShoppingSectionLayoutProps = {
  /** Короткий подзаголовок, поясняющий текущую вкладку. */
  subtitle?: string;
  /** Действие в шапке (например, кнопка «+ Добавить»). */
  action?: ReactNode;
  children: ReactNode;
  contentClassName?: string;
};

/**
 * Единый каркас раздела «Покупки» (Этап 3): заголовок + подзаголовок +
 * внутренние вкладки (Покупки / Запасы / Остатки). Покупки отвечают на вопрос
 * «что купить?» и объединяют список покупок, запасы и остатки.
 *
 * Future Delivery Integration (НЕ в этом этапе): отсюда в будущем можно будет
 * заказать продукты из списка и оформить доставку. Доставка останется частью
 * Покупок, а НЕ отдельной нижней вкладкой/разделом. Большой нерабочей кнопки
 * сейчас не показываем — только задел в архитектуре (see docs/NAVIGATION_MAP.md).
 */
export function ShoppingSectionLayout({
  subtitle,
  action,
  children,
  contentClassName = "space-y-3 pb-24",
}: ShoppingSectionLayoutProps) {
  return (
    <div className="min-h-screen bg-cream">
      <header className="sticky top-0 z-10 border-b border-cream-border bg-cream-surface/95 px-4 pb-2 pt-4 backdrop-blur-sm">
        <div className="mx-auto max-w-lg">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h1 className="text-xl font-bold text-graphite-900">Покупки</h1>
              {subtitle ? (
                <p className="mt-0.5 text-xs text-graphite-500">{subtitle}</p>
              ) : null}
            </div>
            {action ? <div className="shrink-0">{action}</div> : null}
          </div>
          <div className="mt-3">
            <ShoppingSubTabs />
          </div>
        </div>
      </header>

      <main className={`mx-auto max-w-lg px-4 py-4 ${contentClassName}`}>
        {children}
      </main>
    </div>
  );
}
