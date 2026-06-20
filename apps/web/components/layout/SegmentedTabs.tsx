"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { isSubTabActive, type SubTab } from "@/lib/navigation/nav-config";

type SegmentedTabsProps = {
  tabs: SubTab[];
  /** Доп. классы контейнера. */
  className?: string;
  "aria-label"?: string;
};

/**
 * Переиспользуемые внутренние вкладки раздела (Меню / Покупки).
 *
 * Создан в Этапе 1 как часть фундамента навигации. Монтируется в свои
 * разделы в Этапах 2–3, когда переедет контент. Горизонтально-скроллируемая
 * сегментированная панель, безопасная для узких экранов Mini App.
 */
export function SegmentedTabs({
  tabs,
  className = "",
  "aria-label": ariaLabel = "Разделы",
}: SegmentedTabsProps) {
  const pathname = usePathname();

  return (
    <nav
      aria-label={ariaLabel}
      className={`flex gap-1.5 overflow-x-auto pb-1 ${className}`}
    >
      {tabs.map((tab) => {
        const active = isSubTabActive(pathname, tab);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={active ? "page" : undefined}
            className={`shrink-0 rounded-pill px-3.5 py-1.5 text-sm font-semibold transition ${
              active
                ? "bg-sage-500 text-white"
                : "bg-cream-surface text-graphite-700 ring-1 ring-cream-border hover:bg-sage-50"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
