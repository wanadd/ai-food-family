"use client";

import { RecipeCard } from "@/components/recipes/RecipeCard";
import { fetchRecipes } from "@/lib/recipes/api";
import {
  RECIPE_CATALOG_SECTIONS,
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
      } catch {
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
    for (const section of RECIPE_CATALOG_SECTIONS) {
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

  return (
    <div className="space-y-8 pb-24">
      {RECIPE_CATALOG_SECTIONS.map((def) => {
        const state = sections[def.id];
        if (!state || state.loading) {
          return (
            <section key={def.id}>
              <h2 className="text-base font-bold text-stone-900">{def.title}</h2>
              <p className="mt-2 text-sm text-stone-400">Загрузка…</p>
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
            <h2 className="text-base font-bold text-stone-900">{def.title}</h2>
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
                className="mt-3 w-full rounded-xl border border-stone-200 py-2.5 text-sm font-semibold text-stone-700"
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
