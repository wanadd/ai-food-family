"use client";

import { useState } from "react";

import { FilterChip } from "@/components/recipes/FilterChip";
import { Sheet } from "@/components/ui/Sheet";

type Scenario = { label: string; value: string };

/**
 * Сценарии — это фильтры/подборки внутри «Рецептов», а НЕ отдельная вкладка.
 * ONE SCREEN UX: на первом уровне только 4 главные подборки, остальные — под
 * кнопкой «Ещё» (bottom sheet). Значения сценариев — без изменений бэкенда.
 */
export const MAIN_SCENARIOS: Scenario[] = [
  { label: "Быстро", value: "quick" },
  { label: "Для семьи", value: "kids_loved" },
  { label: "Из запасов", value: "from_pantry" },
  { label: "Полезнее", value: "lose_weight" },
];

export const MORE_SCENARIOS: Scenario[] = [
  { label: "15 минут", value: "ultra_quick" },
  { label: "Дёшево", value: "cheap" },
  { label: "Набор массы", value: "gain_weight" },
  { label: "На работу", value: "work_lunch" },
  { label: "Гости", value: "guests" },
  { label: "Праздник", value: "holiday" },
  { label: "Без готовки", value: "almost_no_cooking" },
];

type ScenarioChipsProps = {
  active?: string;
  onSelect: (value: string | undefined) => void;
};

export function ScenarioChips({ active, onSelect }: ScenarioChipsProps) {
  const [moreOpen, setMoreOpen] = useState(false);
  const activeMore = MORE_SCENARIOS.find((s) => s.value === active);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {MAIN_SCENARIOS.map((scenario) => (
        <FilterChip
          key={scenario.value}
          active={active === scenario.value}
          label={scenario.label}
          onClick={() =>
            onSelect(active === scenario.value ? undefined : scenario.value)
          }
        />
      ))}

      <button
        type="button"
        onClick={() => setMoreOpen(true)}
        aria-pressed={Boolean(activeMore)}
        className={`shrink-0 rounded-pill px-3 py-1.5 text-xs font-semibold transition ${
          activeMore
            ? "bg-sage-500 text-white"
            : "bg-cream-surface text-graphite-700 ring-1 ring-cream-border hover:bg-sage-50"
        }`}
      >
        {activeMore ? activeMore.label : "Ещё"}
      </button>

      <Sheet open={moreOpen} title="Ещё подборки" onClose={() => setMoreOpen(false)}>
        <div className="flex flex-wrap gap-2 pb-2">
          {MORE_SCENARIOS.map((scenario) => (
            <FilterChip
              key={scenario.value}
              active={active === scenario.value}
              label={scenario.label}
              onClick={() => {
                onSelect(active === scenario.value ? undefined : scenario.value);
                setMoreOpen(false);
              }}
            />
          ))}
        </div>
      </Sheet>
    </div>
  );
}
