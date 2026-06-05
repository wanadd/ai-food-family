"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { RecipeGridCard2026 } from "@/components/recipes-2026/RecipeGridCard2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useToast } from "@/components/ui/ToastProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { replaceMenuSlot } from "@/lib/menu/api";
import {
  buildReplaceDetailUrl,
  parseCurrentRecipeId,
  parseReplaceSlot,
} from "@/lib/menu/replace-slot";
import { readReturnTo } from "@/lib/navigation/return-to";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";
import {
  fetchRecipeFilters,
  fetchRecipes,
  toggleRecipeFavorite,
} from "@/lib/recipes/api";
import { CATALOG_MEAL_FILTERS } from "@/lib/recipes/labels";
import type { RecipeFilters, RecipeQuery, RecipeSummary } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";

function queryFromParams(sp: URLSearchParams): RecipeQuery {
  const query: RecipeQuery = {};
  const q = sp.get("q");
  if (q) query.q = q;
  const meal = sp.get("meal_type");
  if (meal) query.meal_type = meal;
  if (sp.get("favorites_only") === "true") query.favorites_only = true;
  return query;
}

export function RecipeCatalog2026() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { showToast } = useToast();
  const paramString = searchParams.toString();
  const query = useMemo(
    () => queryFromParams(new URLSearchParams(paramString)),
    [paramString],
  );

  const replaceSlot = useMemo(
    () => parseReplaceSlot(searchParams.get("replaceSlot")),
    [searchParams],
  );
  const currentRecipeId = useMemo(
    () => parseCurrentRecipeId(searchParams.get("currentRecipeId")),
    [searchParams],
  );
  const replaceMode = replaceSlot != null;
  const returnTo = readReturnTo(searchParams, "/plan/today");

  const [filters, setFilters] = useState<RecipeFilters | null>(null);
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState(query.q ?? "");
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [replacingId, setReplacingId] = useState<number | null>(null);

  const isFavorites = Boolean(query.favorites_only);
  const hasFilters = Boolean(query.q || query.meal_type || isFavorites);

  const displayRecipes = useMemo(() => {
    if (!currentRecipeId) {
      return recipes;
    }
    return [...recipes].sort((a, b) => {
      if (a.id === currentRecipeId) return 1;
      if (b.id === currentRecipeId) return -1;
      return 0;
    });
  }, [recipes, currentRecipeId]);

  const updateParams = useCallback(
    (patch: Record<string, string | undefined>) => {
      const next = new URLSearchParams(paramString);
      for (const [key, value] of Object.entries(patch)) {
        if (!value) next.delete(key);
        else next.set(key, value);
      }
      const qs = next.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [paramString, pathname, router],
  );

  useEffect(() => {
    if (!initData) return;
    fetchRecipeFilters(initData)
      .then(setFilters)
      .catch(() => setFilters(null));
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
      .then((list) => {
        if (cancelled) return;
        setRecipes(list.items);
        setTotal(list.total);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Не удалось загрузить рецепты");
        setRecipes([]);
        setTotal(0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [initData, query, paramString]);

  useEffect(() => {
    setSearchInput(query.q ?? "");
  }, [query.q]);

  async function handleFavorite(recipeId: number) {
    if (!initData) return;
    setTogglingId(recipeId);
    try {
      const result = await toggleRecipeFavorite(initData, recipeId);
      setRecipes((prev) =>
        prev.map((r) =>
          r.id === recipeId ? { ...r, is_favorited: result.is_favorited } : r,
        ),
      );
      if (isFavorites && !result.is_favorited) {
        setRecipes((prev) => prev.filter((r) => r.id !== recipeId));
      }
    } finally {
      setTogglingId(null);
    }
  }

  async function handleReplace(recipeId: number) {
    if (!initData || !replaceSlot) {
      showToast("Не удалось заменить блюдо");
      return;
    }
    setReplacingId(recipeId);
    try {
      await replaceMenuSlot(initData, mode, replaceSlot, recipeId, 2);
      showToast("Блюдо заменено");
      router.push("/plan/today?saved=1");
    } catch {
      showToast("Не удалось заменить блюдо");
    } finally {
      setReplacingId(null);
    }
  }

  function handleSearchSubmit() {
    updateParams({ q: searchInput.trim() || undefined });
  }

  let emptyContent = null;
  if (!loading && recipes.length === 0) {
    if (isFavorites) {
      emptyContent = (
        <EmptyState2026
          icon={<span aria-hidden>★</span>}
          title="Пока нет избранных"
          description="Отмечайте понравившиеся рецепты — они появятся здесь."
          actionLabel="В каталог"
          onAction={() => updateParams({ favorites_only: undefined })}
        />
      );
    } else if (query.q) {
      emptyContent = (
        <EmptyState2026
          title="Ничего не нашли"
          description={`По запросу «${query.q}» рецептов нет. Попробуйте другое название.`}
          actionLabel="Сбросить поиск"
          onAction={() => {
            setSearchInput("");
            updateParams({ q: undefined });
          }}
        />
      );
    } else if (query.meal_type) {
      emptyContent = (
        <EmptyState2026
          title="В этой категории пусто"
          description="Выберите другой приём пищи или посмотрите весь каталог."
          actionLabel="Все рецепты"
          onAction={() => updateParams({ meal_type: undefined })}
        />
      );
    } else {
      emptyContent = (
        <EmptyState2026
          title="Каталог пока пуст"
          description="Рецепты появятся после наполнения базы. Создайте меню — ПланАм подберёт блюда."
          actionLabel="Создать меню"
          onAction={() => router.push(PLAN_PATHS.generate)}
        />
      );
    }
  }

  return (
    <div className="pb-6">
      {replaceMode ? (
        <div className="border-b border-sage-200 bg-sage-50 px-4 py-3 dark:border-sage-700/40 dark:bg-sage-700/20">
          <p className="pa26-caption font-semibold text-sage-800 dark:text-sage-300">
            Выберите новое блюдо для замены
          </p>
        </div>
      ) : null}
      <div className="sticky top-0 z-20 border-b border-pa-border bg-pa-canvas/95 px-4 py-3 backdrop-blur-md">
        <div className="flex gap-2">
          <input
            type="search"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit()}
            placeholder="Поиск рецепта…"
            className="min-w-0 flex-1 rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
          />
          <button
            type="button"
            onClick={handleSearchSubmit}
            className="rounded-control bg-sage-500 px-3 py-2 text-sm font-semibold text-white dark:bg-sage-400"
          >
            Найти
          </button>
        </div>
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          <FilterChip
            active={!query.meal_type && !isFavorites}
            label="Все"
            onClick={() => updateParams({ meal_type: undefined, favorites_only: undefined })}
          />
          {CATALOG_MEAL_FILTERS.map((f) => (
            <FilterChip
              key={f.value}
              active={query.meal_type === f.value}
              label={f.label}
              onClick={() =>
                updateParams({
                  meal_type: query.meal_type === f.value ? undefined : f.value,
                  favorites_only: undefined,
                })
              }
            />
          ))}
          <FilterChip
            active={isFavorites}
            label="Избранное"
            onClick={() =>
              updateParams({
                favorites_only: isFavorites ? undefined : "true",
                meal_type: undefined,
              })
            }
          />
        </div>
      </div>

      <div className="px-4 pt-4">
        {error ? (
          <EmptyState2026
            title="Ошибка загрузки"
            description={error}
            actionLabel="Повторить"
            onAction={() => router.refresh()}
          />
        ) : null}

        {loading ? (
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton2026
                key={i}
                variant="rect"
                aspectRatio="1/1"
                className="rounded-card"
              />
            ))}
          </div>
        ) : emptyContent ? (
          emptyContent
        ) : (
          <>
            <p className="pa26-caption mb-3 text-pa-muted">
              {total} {total === 1 ? "рецепт" : total < 5 ? "рецепта" : "рецептов"}
              {filters ? "" : ""}
            </p>
            <div className="grid grid-cols-2 gap-3">
              {displayRecipes.map((recipe) => (
                <RecipeGridCard2026
                  key={recipe.id}
                  recipe={recipe}
                  href={
                    replaceSlot
                      ? buildReplaceDetailUrl(
                          recipe.id,
                          replaceSlot,
                          currentRecipeId,
                          returnTo,
                        )
                      : `/plan/recipes/${recipe.id}`
                  }
                  onToggleFavorite={
                    replaceMode ? undefined : () => void handleFavorite(recipe.id)
                  }
                  togglingFavorite={togglingId === recipe.id}
                  replaceMode={replaceMode}
                  isCurrentRecipe={currentRecipeId === recipe.id}
                  onReplace={() => void handleReplace(recipe.id)}
                  replacing={replacingId === recipe.id}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function FilterChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "shrink-0 rounded-pill px-3 py-1.5 pa26-micro font-semibold transition",
        active
          ? "bg-sage-500 text-white dark:bg-sage-400"
          : "border border-pa-border bg-pa-surface text-pa-muted",
      )}
    >
      {label}
    </button>
  );
}
