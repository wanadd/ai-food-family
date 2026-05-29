"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useTelegram } from "@/components/TelegramProvider";
import { RecipeCard } from "@/components/recipes/RecipeCard";
import { fetchRecipes, toggleRecipeFavorite } from "@/lib/recipes/api";
import type { RecipeSummary } from "@/lib/recipes/types";

const HOME_RECS_LIMIT = 4;

/**
 * Блок «Подобрано для вас» — тонкая лента рекомендаций рецептов.
 * Загружается лениво (dynamic import в PlanAmHome) и делает один обычный
 * (не AI) запрос каталога. Это ранжированная подборка, не генерация ИИ.
 */
export function HomeRecommendations() {
  const router = useRouter();
  const { initData } = useTelegram();
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  useEffect(() => {
    if (!initData) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchRecipes(initData, {})
      .then((data) => {
        if (!cancelled) setRecipes(data.items.slice(0, HOME_RECS_LIMIT));
      })
      .catch(() => {
        if (!cancelled) setRecipes([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [initData]);

  const openRecipe = useCallback(
    (id: number) => router.push(`/recipes/${id}`),
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
      } catch {
        /* избранное не критично для Home */
      } finally {
        setTogglingId(null);
      }
    },
    [initData],
  );

  if (loading) {
    return (
      <section className="space-y-2" aria-busy="true">
        <div className="h-4 w-40 rounded bg-stone-100" />
        <div className="h-24 animate-pulse rounded-2xl border border-stone-100 bg-stone-50" />
        <div className="h-24 animate-pulse rounded-2xl border border-stone-100 bg-stone-50" />
      </section>
    );
  }

  if (recipes.length === 0) {
    return null;
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-2 px-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Подобрано для вас
        </p>
        <Link
          href="/menu/recipes"
          className="text-xs font-semibold text-emerald-700"
        >
          Все рецепты →
        </Link>
      </div>
      <div className="space-y-3">
        {recipes.map((recipe) => (
          <RecipeCard
            key={recipe.id}
            recipe={recipe}
            onOpen={() => openRecipe(recipe.id)}
            onToggleFavorite={() => handleToggleFavorite(recipe.id)}
            togglingFavorite={togglingId === recipe.id}
          />
        ))}
      </div>
    </section>
  );
}
