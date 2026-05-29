import type { ReactNode } from "react";

import {
  ScreenBackNav,
  type ScreenBackConfig,
} from "@/components/layout/ScreenBackNav";

type SectionHubProps = {
  /** Заголовок раздела (где я нахожусь). */
  title: string;
  /** Короткий тёплый подзаголовок. Не обязателен. */
  subtitle?: string;
  /** Опциональная навигация назад (для подэкранов). */
  back?: ScreenBackConfig;
  /** Действие в шапке (иконка/ссылка справа). */
  headerExtra?: ReactNode;
  /**
   * «Что важно сейчас» — один главный ответ над деревом кнопок.
   * Держим коротким: одна мысль, не dashboard.
   */
  lead?: ReactNode;
  /** Дерево функций: набор HubTile. */
  children: ReactNode;
  /** Низ экрана (доп. ссылка/подсказка). Не обязателен. */
  footer?: ReactNode;
};

/**
 * SectionHub — каркас «один экран» для главных разделов (ONE SCREEN UX).
 *
 * Структура отвечает на 3 вопроса за 5–10 секунд: где я (title), что важно
 * (lead), куда нажать (крупные HubTile). Глубина — через подэкраны и листы,
 * а не через длинный скролл. Строится на дизайн-токенах Фазы 1 (cream/.pa-*).
 */
export function SectionHub({
  title,
  subtitle,
  back,
  headerExtra,
  lead,
  children,
  footer,
}: SectionHubProps) {
  return (
    <div className="min-h-screen bg-cream">
      <div className="mx-auto max-w-lg px-5 pb-28 pt-7">
        {back ? <ScreenBackNav back={back} className="mb-2" /> : null}
        <header className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-[1.7rem] font-bold leading-tight text-graphite-900">
              {title}
            </h1>
            {subtitle ? (
              <p className="mt-1 text-sm text-graphite-500">{subtitle}</p>
            ) : null}
          </div>
          {headerExtra ? <div className="shrink-0">{headerExtra}</div> : null}
        </header>

        {lead ? <div className="mt-4">{lead}</div> : null}

        <div className="mt-4 grid gap-3">{children}</div>

        {footer ? <div className="mt-5">{footer}</div> : null}
      </div>
    </div>
  );
}
