"use client";

/**
 * PLANAM V2 — consumer UI primitives.
 * Тонкий слой над DS 2026 с единым стилем референса:
 * мягкие скругления, чистые поверхности, зелёный CTA, спокойные подписи.
 */

import type { ReactNode } from "react";

import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { cn } from "@/lib/planam/cn";

export const V2Button = Button2026;
export const V2BottomSheet = BottomSheet2026;
export const V2EmptyState = EmptyState2026;

export function V2Card({
  children,
  className,
  padding = true,
}: {
  children: ReactNode;
  className?: string;
  padding?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none",
        padding && "p-4",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function V2SectionHeader({
  title,
  subtitle,
  className,
}: {
  title: string;
  subtitle?: string;
  className?: string;
}) {
  return (
    <header className={className}>
      <h2 className="pa26-section-title">{title}</h2>
      {subtitle ? (
        <p className="pa26-micro mt-0.5 text-pa-muted">{subtitle}</p>
      ) : null}
    </header>
  );
}

export function V2PageHeader({
  title,
  subtitle,
  className,
}: {
  title: string;
  subtitle?: string;
  className?: string;
}) {
  return (
    <header className={cn("px-4 pt-[max(0.5rem,env(safe-area-inset-top))]", className)}>
      <h1 className="pa26-page-title">{title}</h1>
      {subtitle ? (
        <p className="pa26-micro mt-0.5 text-pa-muted">{subtitle}</p>
      ) : null}
    </header>
  );
}

export type V2ProgressTone = "brand" | "water" | "food" | "energy" | "danger";

const progressToneClasses: Record<V2ProgressTone, string> = {
  brand: "bg-sage-500 dark:bg-sage-400",
  water: "bg-water",
  food: "bg-food",
  energy: "bg-energy",
  danger: "bg-danger",
};

export function V2ProgressBar({
  percent,
  tone = "brand",
  className,
}: {
  percent: number;
  /** Семантический акцент: вода — голубой, еда — оранжевый и т.д. */
  tone?: V2ProgressTone;
  className?: string;
}) {
  const safe = Math.max(0, Math.min(100, Math.round(percent)));
  return (
    <div className={cn("h-2 overflow-hidden rounded-pill bg-pa-border/60", className)}>
      <div
        className={cn(
          "h-full rounded-pill transition-all",
          progressToneClasses[tone],
        )}
        style={{ width: `${safe}%` }}
      />
    </div>
  );
}

export function V2Chip({
  label,
  active = false,
  onClick,
  className,
}: {
  label: string;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "shrink-0 rounded-pill border px-3 py-1.5 pa26-micro font-semibold transition",
        active
          ? "border-sage-500 bg-sage-500 text-white dark:border-sage-400 dark:bg-sage-400"
          : "border-pa-border bg-pa-surface text-pa-muted hover:bg-sage-50 dark:hover:bg-pa-elevated/40",
        className,
      )}
    >
      {label}
    </button>
  );
}

export function V2ListRow({
  title,
  caption,
  trailing,
  onClick,
  muted = false,
  className,
}: {
  title: ReactNode;
  caption?: ReactNode;
  trailing?: ReactNode;
  onClick?: () => void;
  muted?: boolean;
  className?: string;
}) {
  const content = (
    <>
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "pa26-card-title truncate",
            muted && "text-pa-muted line-through",
          )}
        >
          {title}
        </p>
        {caption ? (
          <p className="pa26-micro mt-0.5 text-pa-muted">{caption}</p>
        ) : null}
      </div>
      {trailing ? (
        <div className="shrink-0 pa26-caption tabular-nums text-pa-muted">
          {trailing}
        </div>
      ) : null}
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "flex w-full min-h-[52px] items-center gap-3 px-4 py-3 text-left transition",
          "hover:bg-sage-50/60 dark:hover:bg-pa-elevated/30",
          className,
        )}
      >
        {content}
      </button>
    );
  }

  return (
    <div
      className={cn(
        "flex min-h-[52px] items-center gap-3 px-4 py-3",
        className,
      )}
    >
      {content}
    </div>
  );
}

export function V2AiTip({
  title = "Совет PLANAM",
  text,
  onClick,
  tone = "brand",
  className,
}: {
  title?: string;
  text: string;
  onClick?: () => void;
  /** "ai" — индиго-акцент для AI/Pro советов; "brand" — обычный контекст дня. */
  tone?: "brand" | "ai";
  className?: string;
}) {
  const body = (
    <div
      className={cn(
        "rounded-card border px-3 py-3 text-left",
        tone === "ai"
          ? "border-ai/30 bg-ai-soft/70 dark:border-ai/40 dark:bg-ai/10"
          : "border-sage-200/80 bg-sage-50/60 dark:border-sage-700/40 dark:bg-sage-900/20",
        className,
      )}
    >
      <p
        className={cn(
          "pa26-micro font-semibold",
          tone === "ai"
            ? "text-ai dark:text-ai/90"
            : "text-sage-800 dark:text-sage-300",
        )}
      >
        {title}
      </p>
      <p className="pa26-caption mt-1 line-clamp-3 text-pa-foreground">{text}</p>
    </div>
  );

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className="block w-full">
        {body}
      </button>
    );
  }
  return body;
}
