"use client";

import Link from "next/link";

import { RecipeCard } from "@/components/recipes/RecipeCard";
import { RecipeListSkeleton } from "@/components/recipes/RecipeListSkeleton";
import { fetchRecipes } from "@/lib/recipes/api";
import {
  RECIPE_HOME_SECTIONS,
  RECIPE_SECTION_PAGE_SIZE,
} from "@/lib/recipes/catalog-sections";
import type { RecipeQuery, RecipeSummary } from "@/lib/recipes/types";
import { useCallback, useEffect, useState } from "react";

type SectionState = {
  items: RecipeSummary[];
  total: number;
  visible: number;
  loading: boolean;
};

type Props = {
  initData: string;
  onOpen: (id: number) => void;
  onToggleFavorite: (id: number) => void;
  togglingId: number | null;
};

export function RecipeCatalogSections({
  initData,
  onOpen,
  onToggleFavorite,
  togglingId,
}: Props) {
  const [sections, setSections] = useState<Record<string, SectionState>>({});

  const loadSection = useCallback(
    async (id: string, query: RecipeQuery) => {
      setSections((prev) => ({
        ...prev,
        [id]: {
          items: prev[id]?.items ?? [],
          total: prev[id]?.total ?? 0,
          visible: prev[id]?.visible ?? RECIPE_SECTION_PAGE_SIZE,
          loading: true,
        },
      }));
      try {
        const data = await fetchRecipes(initData, query);
        setSections((prev) => ({
          ...prev,
          [id]: {
            items: data.items,
            total: data.total,
            visible: RECIPE_SECTION_PAGE_SIZE,
            loading: false,
          },
        }));
      } catch (err) {
        if (process.env.NODE_ENV === "development") {
          console.error("[RecipeCatalogSections] load failed", id, query, err);
        }
        setSections((prev) => ({
          ...prev,
          [id]: {
            items: [],
            total: 0,
            visible: RECIPE_SECTION_PAGE_SIZE,
            loading: false,
          },
        }));
      }
    },
    [initData],
  );

  useEffect(() => {
    for (const section of RECIPE_HOME_SECTIONS) {
      void loadSection(section.id, section.query);
    }
  }, [loadSection]);

  function showMore(id: string) {
    setSections((prev) => {
      const s = prev[id];
      if (!s) return prev;
      return {
        ...prev,
        [id]: {
          ...s,
          visible: Math.min(s.visible + RECIPE_SECTION_PAGE_SIZE, s.items.length),
        },
      };
    });
  }

  const allLoaded = RECIPE_HOME_SECTIONS.every(
    (def) => sections[def.id] && !sections[def.id].loading,
  );
  const noResults =
    allLoaded &&
    RECIPE_HOME_SECTIONS.every(
      (def) => (sections[def.id]?.items.length ?? 0) === 0,
    );

  if (noResults) {
    return (
      <div className="pa-card p-6 text-center">
        <p className="text-2xl" aria-hidden>
          🍳
        </p>
        <p className="mt-2 font-semibold text-graphite-900">
          Подберём рецепты вместе
        </p>
        <p className="mt-1.5 text-sm text-graphite-500">
          Найдите блюдо через поиск или составьте меню — ПланАм предложит
          подходящие рецепты.
        </p>
        <Link
          href="/menu/generate"
          className="pa-btn-primary mt-5 inline-flex"
        >
          Составить меню
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-7 pb-24">
      {RECIPE_HOME_SECTIONS.map((def) => {
        const state = sections[def.id];
        if (!state || state.loading) {
          return (
            <section key={def.id}>
              <h2 className="text-base font-bold text-graphite-900">
                {def.title}
              </h2>
              <div className="mt-3">
                <RecipeListSkeleton count={2} />
              </div>
            </section>
          );
        }
        const visibleItems = state.items.slice(0, state.visible);
        if (visibleItems.length === 0) {
          return null;
        }
        const hasMore = state.visible < state.items.length;

        return (
          <section key={def.id}>
            <h2 className="text-base font-bold text-graphite-900">
              {def.title}
            </h2>
            <div className="mt-3 space-y-3">
              {visibleItems.map((recipe) => (
                <RecipeCard
                  key={recipe.id}
                  recipe={recipe}
                  onOpen={() => onOpen(recipe.id)}
                  onToggleFavorite={() => onToggleFavorite(recipe.id)}
                  togglingFavorite={togglingId === recipe.id}
                />
              ))}
            </div>
            {hasMore ? (
              <button
                type="button"
                onClick={() => showMore(def.id)}
                className="mt-3 w-full rounded-control border border-cream-border py-2.5 text-sm font-semibold text-graphite-700"
              >
                Показать ещё
              </button>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
