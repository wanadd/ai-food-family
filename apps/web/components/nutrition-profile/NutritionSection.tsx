"use client";

import type { ReactNode } from "react";

type NutritionSectionProps = {
  id: string;
  title: string;
  summary: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
};

export function NutritionSection({
  id,
  title,
  summary,
  open,
  onToggle,
  children,
}: NutritionSectionProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-stone-100 bg-white shadow-sm">
      <button
        type="button"
        id={`${id}-header`}
        aria-expanded={open}
        aria-controls={`${id}-panel`}
        onClick={onToggle}
        className="flex w-full min-h-[56px] items-center gap-3 px-4 py-3.5 text-left transition active:bg-stone-50"
      >
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-stone-900">{title}</p>
          {!open ? (
            <p className="mt-0.5 truncate text-sm text-stone-500">{summary}</p>
          ) : null}
        </div>
        <span
          className={`shrink-0 text-stone-400 transition ${open ? "rotate-90" : ""}`}
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
          className="border-t border-stone-100 px-4 pb-4 pt-3"
        >
          {children}
        </div>
      ) : null}
    </section>
  );
}
