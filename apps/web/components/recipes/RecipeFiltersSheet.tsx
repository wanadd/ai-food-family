"use client";

import type { ReactNode } from "react";

import { FilterChip } from "@/components/recipes/FilterChip";
import { Sheet } from "@/components/ui/Sheet";
import { CATALOG_MEAL_FILTERS } from "@/lib/recipes/labels";
import type { RecipeFilters, RecipeQuery } from "@/lib/recipes/types";

type QueryPatch = Record<string, string | undefined>;

type RecipeFiltersSheetProps = {
  open: boolean;
  onClose: () => void;
  filters: RecipeFilters | null;
  query: RecipeQuery;
  onChange: (patch: QueryPatch) => void;
};

const PREP_TIME_PRESETS = [15, 30, 45, 60];

const FILTER_PATCH_KEYS: QueryPatch = {
  meal_type: undefined,
  category: undefined,
  diet: undefined,
  difficulty: undefined,
  max_prep_time: undefined,
  protein_only: undefined,
  for_sport: undefined,
  drinks_only: undefined,
};

/** Bottom-sheet с дополнительными фильтрами каталога рецептов. */
export function RecipeFiltersSheet({
  open,
  onClose,
  filters,
  query,
  onChange,
}: RecipeFiltersSheetProps) {
  function toggleBool(key: "protein_only" | "for_sport" | "drinks_only") {
    onChange({ [key]: query[key] ? undefined : "true" });
  }

  return (
    <Sheet open={open} title="Фильтры" onClose={onClose}>
      <div className="space-y-5 pb-2">
        <FilterGroup title="Когда">
          {CATALOG_MEAL_FILTERS.map((option) => (
            <FilterChip
              key={option.value}
              label={option.label}
              active={query.meal_type === option.value}
              onClick={() =>
                onChange({
                  meal_type:
                    query.meal_type === option.value ? undefined : option.value,
                })
              }
            />
          ))}
        </FilterGroup>

        <FilterGroup title="Тип блюда" hidden={!filters?.categories.length}>
          {filters?.categories.map((option) => (
            <FilterChip
              key={option.value}
              label={option.label}
              active={query.category === option.value}
              onClick={() =>
                onChange({
                  category:
                    query.category === option.value ? undefined : option.value,
                })
              }
            />
          ))}
        </FilterGroup>

        <FilterGroup title="Питание" hidden={!filters?.diets.length}>
          {filters?.diets.map((option) => (
            <FilterChip
              key={option.value}
              label={option.label}
              active={query.diet === option.value}
              onClick={() =>
                onChange({
                  diet: query.diet === option.value ? undefined : option.value,
                })
              }
            />
          ))}
        </FilterGroup>

        <FilterGroup title="Сложность" hidden={!filters?.difficulties.length}>
          {filters?.difficulties.map((option) => (
            <FilterChip
              key={option.value}
              label={option.label}
              active={query.difficulty === option.value}
              onClick={() =>
                onChange({
                  difficulty:
                    query.difficulty === option.value
                      ? undefined
                      : option.value,
                })
              }
            />
          ))}
        </FilterGroup>

        <FilterGroup title="Время на готовку">
          {PREP_TIME_PRESETS.map((preset) => (
            <FilterChip
              key={preset}
              label={`≤ ${preset} мин`}
              active={query.max_prep_time === preset}
              onClick={() =>
                onChange({
                  max_prep_time:
                    query.max_prep_time === preset ? undefined : String(preset),
                })
              }
            />
          ))}
        </FilterGroup>

        <FilterGroup title="Особое">
          <FilterChip
            label="Белок"
            active={Boolean(query.protein_only)}
            onClick={() => toggleBool("protein_only")}
          />
          <FilterChip
            label="Спорт"
            active={Boolean(query.for_sport)}
            onClick={() => toggleBool("for_sport")}
          />
          <FilterChip
            label="Напитки"
            active={Boolean(query.drinks_only)}
            onClick={() => toggleBool("drinks_only")}
          />
        </FilterGroup>

        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={() => onChange(FILTER_PATCH_KEYS)}
            className="flex-1 rounded-control border border-cream-border bg-cream-surface py-2.5 text-sm font-semibold text-graphite-700"
          >
            Сбросить фильтры
          </button>
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-control bg-sage-500 py-2.5 text-sm font-semibold text-white"
          >
            Готово
          </button>
        </div>
      </div>
    </Sheet>
  );
}

function FilterGroup({
  title,
  hidden = false,
  children,
}: {
  title: string;
  hidden?: boolean;
  children: ReactNode;
}) {
  if (hidden) return null;
  return (
    <div>
      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-graphite-400">
        {title}
      </p>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}
