"use client";

import type { MenuVariant } from "@/lib/menu/types";
import { getMenuDays, menuHasMultipleDays } from "@/lib/menu/menu-days";

type Props = {
  menu: MenuVariant;
  dayIndex: number;
  onDayIndexChange: (dayIndex: number) => void;
};

export function MenuDayPicker({ menu, dayIndex, onDayIndexChange }: Props) {
  if (!menuHasMultipleDays(menu)) {
    return null;
  }

  const days = getMenuDays(menu);

  return (
    <div className="flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {days.map((day) => {
        const active = day.day_index === dayIndex;
        return (
          <button
            key={day.day_index}
            type="button"
            onClick={() => onDayIndexChange(day.day_index)}
            className={`shrink-0 rounded-pill px-3 py-1.5 text-xs font-semibold transition ${
              active
                ? "bg-sage-600 text-white shadow-soft"
                : "bg-cream-surface text-graphite-700 ring-1 ring-cream-border"
            }`}
          >
            {day.label}
          </button>
        );
      })}
    </div>
  );
}
