"use client";

import { FilterChip } from "@/components/recipes/FilterChip";

/**
 * Сценарии — это фильтры/подборки внутри «Рецептов», а НЕ отдельная вкладка.
 * ПланАм фильтрует каталог под ситуацию, выбор остаётся за пользователем.
 */
export const SCENARIO_CHIPS = [
  { label: "Быстро", value: "quick" },
  { label: "15 минут", value: "ultra_quick" },
  { label: "Дешево", value: "cheap" },
  { label: "Для детей", value: "kids_loved" },
  { label: "Из запасов", value: "from_pantry" },
  { label: "Похудение", value: "lose_weight" },
  { label: "Набор массы", value: "gain_weight" },
  { label: "На работу", value: "work_lunch" },
  { label: "Гости", value: "guests" },
  { label: "Праздник", value: "holiday" },
  { label: "Без готовки", value: "almost_no_cooking" },
] as const;

type ScenarioChipsProps = {
  active?: string;
  onSelect: (value: string | undefined) => void;
};

export function ScenarioChips({ active, onSelect }: ScenarioChipsProps) {
  return (
    <section className="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-3">
      <p className="text-sm font-bold text-stone-900">Подобрать под ситуацию</p>
      <p className="mt-1 text-xs text-stone-600">
        Быстрые подсказки: ПланАм фильтрует каталог, а выбираете вы.
      </p>
      <div className="mt-3 flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible">
        {SCENARIO_CHIPS.map((scenario) => (
          <FilterChip
            key={scenario.value}
            active={active === scenario.value}
            label={scenario.label}
            onClick={() =>
              onSelect(active === scenario.value ? undefined : scenario.value)
            }
          />
        ))}
      </div>
    </section>
  );
}
