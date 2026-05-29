"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useTelegram } from "@/components/TelegramProvider";
import { FilterChip } from "@/components/recipes/FilterChip";
import { FromPantrySection } from "@/components/recipes/FromPantrySection";
import { RecipeCatalogSections } from "@/components/recipes/RecipeCatalogSections";
import { RecipeFiltersSheet } from "@/components/recipes/RecipeFiltersSheet";
import { RecipeResultsList } from "@/components/recipes/RecipeResultsList";
import { ScenarioChips } from "@/components/recipes/ScenarioChips";
import { CATALOG_MEAL_FILTERS } from "@/lib/recipes/labels";
import { RECIPE_SECTION_PAGE_SIZE } from "@/lib/recipes/catalog-sections";
import {
  fetchRecipeFilters,
  fetchRecipes,
  toggleRecipeFavorite,
} from "@/lib/recipes/api";
import type {
  RecipeFilters,
  RecipeQuery,
  RecipeSummary,
} from "@/lib/recipes/types";

type QueryPatch = Record<string, string | undefined>;

const FILTER_KEYS: (keyof RecipeQuery)[] = [
  "category",
  "diet",
  "difficulty",
  "max_prep_time",
  "protein_only",
  "for_sport",
  "drinks_only",
];

/** Собирает RecipeQuery из URL query (единый источник состояния каталога). */
function queryFromParams(sp: URLSearchParams): RecipeQuery {
  const query: RecipeQuery = {};
  const text = sp.get("q");
  if (text) query.q = text;
  const meal = sp.get("meal_type");
  if (meal) query.meal_type = meal;
  const scenario = sp.get("scenario");
  if (scenario) query.scenario = scenario;
  const category = sp.get("category");
  if (category) query.category = category;
  const diet = sp.get("diet");
  if (diet) query.diet = diet;
  const difficulty = sp.get("difficulty");
  if (difficulty) query.difficulty = difficulty;
  const maxPrep = sp.get("max_prep_time");
  if (maxPrep) query.max_prep_time = Number(maxPrep);
  if (sp.get("protein_only") === "true") query.protein_only = true;
  if (sp.get("for_sport") === "true") query.for_sport = true;
  if (sp.get("drinks_only") === "true") query.drinks_only = true;
  return query;
}

/**
 * Внутренняя вкладка «Рецепты» раздела «Меню» (Этап 2).
 *
 * Состояние поиска, сценария и фильтров живёт в URL query
 * (например /menu/recipes?q=курица&scenario=quick), чтобы экран был
 * шарящимся и переживал возврат назад. Деталь рецепта остаётся на /recipes/[id].
 */
export function RecipesView() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { initData } = useTelegram();

  const paramString = searchParams.toString();
  const query = useMemo(
    () => queryFromParams(new URLSearchParams(paramString)),
    [paramString],
  );

  const [filters, setFilters] = useState<RecipeFilters | null>(null);
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [visible, setVisible] = useState(RECIPE_SECTION_PAGE_SIZE);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [searchInput, setSearchInput] = useState(query.q ?? "");

  const activeFilterCount = FILTER_KEYS.filter(
    (key) => query[key] !== undefined,
  ).length;
  const isSearchMode =
    Boolean(query.q) ||
    Boolean(query.meal_type) ||
    Boolean(query.scenario) ||
    activeFilterCount > 0;

  const updateParams = useCallback(
    (patch: QueryPatch) => {
      const next = new URLSearchParams(paramString);
      for (const [key, value] of Object.entries(patch)) {
        if (value === undefined || value === "") next.delete(key);
        else next.set(key, value);
      }
      const qs = next.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [paramString, pathname, router],
  );

  const clearAll = useCallback(() => {
    setSearchInput("");
    router.replace(pathname, { scroll: false });
  }, [pathname, router]);

  useEffect(() => {
    if (!initData) return;
    let cancelled = false;
    fetchRecipeFilters(initData)
      .then((data) => {
        if (!cancelled) setFilters(data);
      })
      .catch(() => {
        /* фильтры не критичны для работы каталога */
      });
    return () => {
      cancelled = true;
    };
  }, [initData]);

  useEffect(() => {
    if (!initData) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchRecipes(initData, query)
      .then((data) => {
        if (cancelled) return;
        setRecipes(data.items);
        setTotal(data.total);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Не удалось загрузить рецепты",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [initData, query]);

  useEffect(() => {
    setVisible(RECIPE_SECTION_PAGE_SIZE);
  }, [query]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      const current = query.q ?? "";
      const trimmed = searchInput.trim();
      if (trimmed !== current) {
        updateParams({ q: trimmed || undefined });
      }
    }, 300);
    return () => window.clearTimeout(handle);
  }, [searchInput, query.q, updateParams]);

  const openRecipe = useCallback(
    (id: number) => {
      router.push(`/recipes/${id}`);
    },
    [router],
  );

  const handleToggleFavorite = useCallback(
    async (id: number) => {
      if (!initData) return;
      setTogglingId(id);
      try {
        const result = await toggleRecipeFavorite(initData, id);
        setRecipes((prev) =>
          prev.map((item) =>
            item.id === id
              ? { ...item, is_favorited: result.is_favorited }
              : item,
          ),
        );
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Не удалось обновить избранное",
        );
      } finally {
        setTogglingId(null);
      }
    },
    [initData],
  );

  if (!initData) {
    return (
      <p className="py-12 text-center text-sm text-stone-600">
        Рецепты доступны в Telegram Mini App после авторизации.
      </p>
    );
  }

  return (
    <div className="space-y-5">
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

      <div className="flex flex-wrap items-center gap-2">
        {CATALOG_MEAL_FILTERS.map((meal) => (
          <FilterChip
            key={meal.value}
            active={query.meal_type === meal.value}
            label={meal.label}
            onClick={() =>
              updateParams({
                meal_type:
                  query.meal_type === meal.value ? undefined : meal.value,
              })
            }
          />
        ))}
        <button
          type="button"
          onClick={() => setFiltersOpen(true)}
          className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
            activeFilterCount > 0
              ? "bg-emerald-600 text-white"
              : "bg-white text-stone-600 ring-1 ring-stone-200 hover:bg-stone-50"
          }`}
        >
          Фильтры{activeFilterCount > 0 ? ` · ${activeFilterCount}` : ""}
        </button>
        {isSearchMode ? (
          <button
            type="button"
            onClick={clearAll}
            className="shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold text-stone-500 hover:bg-stone-100"
          >
            Сбросить
          </button>
        ) : null}
      </div>

      <ScenarioChips
        active={query.scenario}
        onSelect={(value) => updateParams({ scenario: value })}
      />

      <FromPantrySection onOpen={openRecipe} />

      {isSearchMode ? (
        <div className="space-y-3 pb-4">
          <p className="text-sm text-stone-500">
            {loading ? "Загрузка…" : `Найдено: ${total}`}
          </p>
          <RecipeResultsList
            recipes={recipes.slice(0, visible)}
            onOpen={openRecipe}
            onToggleFavorite={handleToggleFavorite}
            togglingId={togglingId}
          />
          {!loading && recipes.length === 0 ? (
            <p className="py-12 text-center text-sm text-stone-400">
              Ничего не найдено. Измените поиск или фильтр.
            </p>
          ) : null}
          {recipes.length > visible ? (
            <button
              type="button"
              onClick={() => setVisible((v) => v + RECIPE_SECTION_PAGE_SIZE)}
              className="w-full rounded-xl border border-stone-200 py-2.5 text-sm font-semibold text-stone-700"
            >
              Показать ещё
            </button>
          ) : null}
        </div>
      ) : loading ? (
        <div className="space-y-3 pb-4" aria-label="Загрузка каталога">
          {[0, 1, 2].map((item) => (
            <div
              key={item}
              className="h-28 animate-pulse rounded-2xl border border-stone-100 bg-stone-50"
            />
          ))}
        </div>
      ) : (
        <RecipeCatalogSections
          initData={initData}
          onOpen={openRecipe}
          onToggleFavorite={handleToggleFavorite}
          togglingId={togglingId}
        />
      )}

      <p className="pt-1 text-center text-xs text-stone-400">
        Не нашли нужное?{" "}
        <Link href="/menu/generate" className="font-semibold text-emerald-700">
          Составить меню с ПланАм
        </Link>
      </p>

      <RecipeFiltersSheet
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        filters={filters}
        query={query}
        onChange={updateParams}
      />
    </div>
  );
}
