"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useTelegram } from "@/components/TelegramProvider";
import { RecipeCard } from "@/components/recipes/RecipeCard";
import { RecipeDetailModal } from "@/components/recipes/RecipeDetailModal";
import {
  fetchRecipe,
  fetchRecipeFilters,
  fetchRecipes,
  toggleRecipeFavorite,
} from "@/lib/recipes/api";
import type {
  RecipeDetail,
  RecipeFilters,
  RecipeQuery,
  RecipeSummary,
} from "@/lib/recipes/types";
type RecipeCatalogProps = {
  menuMode?: boolean;
};

export function RecipeCatalog({ menuMode = false }: RecipeCatalogProps) {
  const router = useRouter();
  const { initData } = useTelegram();
  const [filters, setFilters] = useState<RecipeFilters | null>(null);
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState<RecipeQuery>({});
  const [searchInput, setSearchInput] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<RecipeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadRecipes = useCallback(
    async (telegramInitData: string, params: RecipeQuery) => {
      setError(null);
      try {
        const data = await fetchRecipes(telegramInitData, params);
        setRecipes(data.items);
        setTotal(data.total);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Не удалось загрузить рецепты",
        );
      }
    },
    [],
  );

  useEffect(() => {
    if (!initData) {
      setLoading(false);
      return;
    }

    async function init() {
      setLoading(true);
      try {
        const filterData = await fetchRecipeFilters(initData);
        setFilters(filterData);
        await loadRecipes(initData, {});
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Не удалось загрузить рецепты",
        );
      } finally {
        setLoading(false);
      }
    }

    void init();
  }, [initData, loadRecipes]);

  useEffect(() => {
    if (!initData) {
      return;
    }
    const timer = window.setTimeout(() => {
      setQuery((prev) => {
        const next: RecipeQuery = { ...prev };
        const trimmed = searchInput.trim();
        if (trimmed) {
          next.q = trimmed;
        } else {
          delete next.q;
        }
        loadRecipes(initData, next);
        return next;
      });
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput, initData, loadRecipes]);

  function updateFilter(patch: Partial<RecipeQuery>) {
    if (!initData) {
      return;
    }
    const next = { ...query, ...patch };
    if (!next.meal_type) {
      delete next.meal_type;
    }
    if (!next.category) {
      delete next.category;
    }
    if (!next.diet) {
      delete next.diet;
    }
    if (!next.difficulty) {
      delete next.difficulty;
    }
    if (next.max_prep_time === undefined) {
      delete next.max_prep_time;
    }
    setQuery(next);
    loadRecipes(initData, next);
  }

  async function openRecipe(recipeId: number) {
    if (!initData) {
      return;
    }
    if (!menuMode) {
      router.push(`/recipes/${recipeId}`);
      return;
    }
    setSelectedId(recipeId);
    setLoadingDetail(true);
    try {
      const data = await fetchRecipe(initData, recipeId);
      setDetail(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось открыть рецепт",
      );
      setSelectedId(null);
    } finally {
      setLoadingDetail(false);
    }
  }

  async function handleToggleFavorite(recipeId: number) {
    if (!initData) {
      return;
    }
    setTogglingId(recipeId);
    try {
      const result = await toggleRecipeFavorite(initData, recipeId);
      setRecipes((prev) =>
        prev.map((item) =>
          item.id === recipeId
            ? { ...item, is_favorited: result.is_favorited }
            : item,
        ),
      );
      if (detail?.id === recipeId) {
        setDetail({ ...detail, is_favorited: result.is_favorited });
      }
      if (query.favorites_only && !result.is_favorited) {
        await loadRecipes(initData, query);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось обновить избранное",
      );
    } finally {
      setTogglingId(null);
    }
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">
          Рецепты доступны в Telegram Mini App после авторизации.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-emerald-700"
        >
          На главную
        </Link>
      </div>
    );
  }

  return (
    <ScreenLayout
      title="Рецепты"
      subtitle="База блюд · поиск · фильтры · избранное"
      back={{ label: menuMode ? "Меню" : "ПланАм", href: menuMode ? "/menu" : "/" }}
      contentClassName="space-y-5"
    >
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <div className="relative">
          <input
            type="search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Поиск по названию, ингредиентам…"
            className="w-full rounded-xl border border-stone-200 bg-white py-3 pl-4 pr-10 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
          />
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-stone-400">
            🔍
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() =>
              updateFilter({
                favorites_only: !query.favorites_only,
              })
            }
            className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
              query.favorites_only
                ? "bg-amber-400 text-amber-950"
                : "bg-white text-stone-600 ring-1 ring-stone-200"
            }`}
          >
            ★ Избранное
          </button>
          <FilterChip
            active={Boolean(query.drinks_only)}
            label="Напитки"
            onClick={() =>
              updateFilter({
                drinks_only: !query.drinks_only,
                alcoholic_only: false,
              })
            }
          />
          <FilterChip
            active={Boolean(query.for_children)}
            label="Для детей"
            onClick={() =>
              updateFilter({ for_children: !query.for_children })
            }
          />
          <FilterChip
            active={Boolean(query.for_sport)}
            label="Спорт"
            onClick={() => updateFilter({ for_sport: !query.for_sport })}
          />
          <FilterChip
            active={Boolean(query.from_pantry)}
            label="Из запасов"
            onClick={() =>
              updateFilter({ from_pantry: !query.from_pantry })
            }
          />
          <FilterChip
            active={Boolean(query.non_alcoholic)}
            label="Безалк."
            onClick={() =>
              updateFilter({
                non_alcoholic: !query.non_alcoholic,
                alcoholic_only: false,
              })
            }
          />
          <FilterChip
            active={Boolean(query.alcoholic_only)}
            label="Алкоголь"
            onClick={() =>
              updateFilter({
                alcoholic_only: !query.alcoholic_only,
                drinks_only: true,
              })
            }
          />
        </div>

        {filters ? (
          <div className="space-y-3 rounded-2xl border border-stone-200 bg-white p-4">
            <FilterSelect
              label="Приём пищи"
              value={query.meal_type ?? ""}
              options={filters.meal_types}
              onChange={(value) => updateFilter({ meal_type: value || undefined })}
            />
            <FilterSelect
              label="Категория"
              value={query.category ?? ""}
              options={filters.categories}
              onChange={(value) => updateFilter({ category: value || undefined })}
            />
            <FilterSelect
              label="Диета"
              value={query.diet ?? ""}
              options={filters.diets}
              onChange={(value) => updateFilter({ diet: value || undefined })}
            />
            <FilterSelect
              label="Сложность"
              value={query.difficulty ?? ""}
              options={filters.difficulties}
              onChange={(value) =>
                updateFilter({ difficulty: value || undefined })
              }
            />
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">
                До {query.max_prep_time ?? filters.max_prep_time} мин
              </span>
              <input
                type="range"
                min={10}
                max={filters.max_prep_time}
                step={5}
                value={query.max_prep_time ?? filters.max_prep_time}
                onChange={(event) =>
                  updateFilter({ max_prep_time: Number(event.target.value) })
                }
                className="mt-2 w-full accent-emerald-600"
              />
            </label>
          </div>
        ) : null}

        <p className="text-sm text-stone-500">
          {loading ? "Загрузка…" : `Найдено: ${total}`}
        </p>

        <div className="space-y-3 pb-8">
          {recipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              onOpen={() => openRecipe(recipe.id)}
              onToggleFavorite={() => handleToggleFavorite(recipe.id)}
              togglingFavorite={togglingId === recipe.id}
            />
          ))}
          {!loading && recipes.length === 0 ? (
            <p className="py-12 text-center text-sm text-stone-400">
              Ничего не найдено. Измените поиск или фильтры.
            </p>
          ) : null}
        </div>

      {detail && selectedId !== null && !loadingDetail ? (
        <RecipeDetailModal
          recipe={detail}
          menuMode={menuMode}
          onClose={() => {
            setDetail(null);
            setSelectedId(null);
          }}
          onToggleFavorite={() => handleToggleFavorite(detail.id)}
          togglingFavorite={togglingId === detail.id}
        />
      ) : null}
    </ScreenLayout>
  );
}

type FilterSelectProps = {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
};

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
        active
          ? "bg-emerald-600 text-white"
          : "bg-white text-stone-600 ring-1 ring-stone-200"
      }`}
    >
      {label}
    </button>
  );
}

function FilterSelect({ label, value, options, onChange }: FilterSelectProps) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
      >
        <option value="">Все</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
