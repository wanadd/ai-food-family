"use client";

import { cn } from "@/lib/planam/cn";

export type ChipOption<T extends string> = {
  id: T;
  label: string;
  hint?: string;
};

type OnboardingChipGrid2026Props<T extends string> = {
  options: ChipOption<T>[];
  value: T | null;
  onChange: (id: T) => void;
  columns?: 1 | 2;
};

export function OnboardingChipGrid2026<T extends string>({
  options,
  value,
  onChange,
  columns = 1,
}: OnboardingChipGrid2026Props<T>) {
  return (
    <div
      className={cn(
        "grid gap-2",
        columns === 2 ? "grid-cols-2" : "grid-cols-1",
      )}
    >
      {options.map((opt) => {
        const selected = value === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onChange(opt.id)}
            className={cn(
              "rounded-card border px-4 py-3 text-left transition active:scale-[0.99]",
              selected
                ? "border-sage-500 bg-sage-50 shadow-soft dark:border-sage-400 dark:bg-sage-700/25"
                : "border-pa-border bg-pa-surface hover:bg-sage-50/80 dark:hover:bg-white/5",
            )}
            aria-pressed={selected}
          >
            <span className="pa26-card-title block">{opt.label}</span>
            {opt.hint ? (
              <span className="pa26-caption mt-0.5 block text-pa-muted">{opt.hint}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

type MultiChipProps = {
  options: readonly string[];
  selected: string[];
  onToggle: (tag: string) => void;
};

export function OnboardingMultiChip2026({
  options,
  selected,
  onToggle,
}: MultiChipProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((tag) => {
        const on = selected.includes(tag);
        return (
          <button
            key={tag}
            type="button"
            onClick={() => onToggle(tag)}
            className={cn(
              "rounded-pill px-3 py-1.5 pa26-micro font-semibold transition",
              on
                ? "bg-sage-500 text-white dark:bg-sage-400"
                : "border border-pa-border bg-pa-surface text-sage-700 dark:text-sage-300",
            )}
            aria-pressed={on}
          >
            {tag}
          </button>
        );
      })}
    </div>
  );
}
