"use client";

import { usePlanamTheme } from "@/components/planam-2026/theme/ThemeProvider";
import { cn } from "@/lib/planam/cn";
import type { ThemePreference } from "@/lib/planam/theme";

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: "light", label: "Светлая" },
  { value: "dark", label: "Тёмная" },
  { value: "system", label: "Система" },
];

type ThemeToggle2026Props = {
  className?: string;
};

export function ThemeToggle2026({ className }: ThemeToggle2026Props) {
  const { preference, setPreference } = usePlanamTheme();

  return (
    <div
      className={cn(
        "inline-flex rounded-control border border-pa-border bg-pa-surface p-1",
        className,
      )}
      role="group"
      aria-label="Тема оформления"
    >
      {OPTIONS.map((opt) => {
        const selected = preference === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => setPreference(opt.value)}
            className={cn(
              "min-h-[36px] rounded-control px-3 text-[13px] font-medium leading-[18px] transition",
              selected
                ? "bg-sage-500 text-white shadow-soft dark:bg-sage-400"
                : "text-pa-muted hover:bg-sage-50 dark:hover:bg-white/5",
            )}
            aria-pressed={selected}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
