"use client";

import type { ReactNode } from "react";

type NutritionSectionProps = {
  id: string;
  title: string;
  summary: string;
  complete?: boolean;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
};

export function NutritionSection({
  id,
  title,
  summary,
  complete = false,
  open,
  onToggle,
  children,
}: NutritionSectionProps) {
  return (
    <section className="overflow-hidden rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none">
      <button
        type="button"
        id={`${id}-header`}
        aria-expanded={open}
        aria-controls={`${id}-panel`}
        onClick={onToggle}
        className="flex w-full min-h-[58px] items-center gap-3 px-4 py-3 text-left transition active:bg-cream-deep/60 dark:active:bg-pa-elevated/50"
      >
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-2 text-sm font-semibold text-pa-foreground">
            {title}
            {complete ? (
              <span className="rounded-pill bg-sage-100 px-2 py-0.5 text-[10px] font-bold uppercase text-sage-800 dark:bg-sage-700/30 dark:text-sage-200">
                ✓
              </span>
            ) : null}
          </p>
          {!open ? (
            <p className="mt-0.5 truncate text-xs text-pa-muted">{summary}</p>
          ) : null}
        </div>
        <span
          className={`shrink-0 text-pa-muted transition ${open ? "rotate-90" : ""}`}
          aria-hidden
        >
          ›
        </span>
      </button>
      {open ? (
        <div
          id={`${id}-panel`}
          role="region"
          aria-labelledby={`${id}-header`}
          className="border-t border-pa-border px-4 pb-4 pt-3"
        >
          {children}
        </div>
      ) : null}
    </section>
  );
}
