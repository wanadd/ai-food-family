"use client";

import Link from "next/link";
import type { ReactNode } from "react";

type HubTileProps = {
  title: string;
  /** Короткий хинт под заголовком (1 строка). Не обязателен. */
  hint?: string;
  /** Иконка слева (эмодзи или SVG). */
  icon?: ReactNode;
  /** Навигация (если задано — рендерится как ссылка). */
  href?: string;
  /** Действие (если href не задан — рендерится как кнопка). */
  onClick?: () => void;
  /** Визуальный акцент: основная (sage) или обычная (поверхность). */
  tone?: "primary" | "default";
  /** Доп. элемент справа (бейдж/счётчик). Шеврон добавляется автоматически. */
  trailing?: ReactNode;
  disabled?: boolean;
  ariaLabel?: string;
};

/**
 * HubTile — крупная кнопка-плитка для навигационных центров (SectionHub).
 * Одна понятная цель на тап: иконка + крупный заголовок + 1 короткий хинт.
 * ONE SCREEN UX: дерево функций строится из таких плиток, а не из карточек.
 */
export function HubTile({
  title,
  hint,
  icon,
  href,
  onClick,
  tone = "default",
  trailing,
  disabled = false,
  ariaLabel,
}: HubTileProps) {
  const isPrimary = tone === "primary";

  const base =
    "flex min-h-[68px] w-full items-center gap-3 rounded-card px-4 py-3 text-left transition active:scale-[0.99]";
  const toneCls = isPrimary
    ? "bg-sage-500 text-white shadow-soft"
    : "border border-cream-border bg-cream-surface text-graphite-900 shadow-soft";

  const iconCls = isPrimary
    ? "bg-white/15 text-white"
    : "bg-sage-50 text-sage-700";

  const hintCls = isPrimary ? "text-white/80" : "text-graphite-500";
  const chevronCls = isPrimary ? "text-white/70" : "text-graphite-400";

  const content = (
    <>
      {icon != null ? (
        <span
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-control text-xl ${iconCls}`}
          aria-hidden
        >
          {icon}
        </span>
      ) : null}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-base font-bold leading-tight">
          {title}
        </span>
        {hint ? (
          <span className={`mt-0.5 block truncate text-sm ${hintCls}`}>
            {hint}
          </span>
        ) : null}
      </span>
      {trailing != null ? <span className="shrink-0">{trailing}</span> : null}
      <span className={`shrink-0 text-lg ${chevronCls}`} aria-hidden>
        ›
      </span>
    </>
  );

  if (href && !disabled) {
    return (
      <Link href={href} aria-label={ariaLabel ?? title} className={`${base} ${toneCls}`}>
        {content}
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel ?? title}
      className={`${base} ${toneCls} disabled:opacity-50`}
    >
      {content}
    </button>
  );
}
