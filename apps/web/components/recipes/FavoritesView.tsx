"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useTelegram } from "@/components/TelegramProvider";
import { RecipeResultsList } from "@/components/recipes/RecipeResultsList";
import { fetchRecipes, toggleRecipeFavorite } from "@/lib/recipes/api";
import type { RecipeSummary } from "@/lib/recipes/types";

/** Внутренняя вкладка «Избранное» раздела «Меню» (Этап 2). */
export function FavoritesView() {
  const router = useRouter();
  const { initData } = useTelegram();
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecipes(initData, { favorites_only: true });
      setRecipes(data.items);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить избранное",
      );
    } finally {
      setLoading(false);
    }
  }, [initData]);

  useEffect(() => {
    void load();
  }, [load]);

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
          result.is_favorited
            ? prev.map((item) =>
                item.id === id ? { ...item, is_favorited: true } : item,
              )
            : prev.filter((item) => item.id !== id),
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
      <p className="py-12 text-center text-sm text-graphite-500">
        Избранное доступно в Telegram Mini App после авторизации.
      </p>
    );
  }

  if (loading) {
    return (
      <div className="space-y-3" aria-label="Загрузка избранного">
        {[0, 1, 2].map((item) => (
          <div
            key={item}
            className="h-28 animate-pulse rounded-card border border-cream-border bg-cream-surface"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </p>
    );
  }

  if (recipes.length === 0) {
    return (
      <div className="pa-card p-6 text-center">
        <p className="text-2xl" aria-hidden>
          ⭐
        </p>
        <p className="mt-2 font-semibold text-graphite-900">
          Здесь будут любимые рецепты
        </p>
        <p className="mt-1.5 text-sm text-graphite-500">
          Нажмите ★ на рецепте — и он сохранится сюда.
        </p>
        <Link
          href="/menu/recipes"
          className="pa-btn pa-btn-primary mt-5 inline-flex"
        >
          К рецептам
        </Link>
      </div>
    );
  }

  return (
    <RecipeResultsList
      recipes={recipes}
      onOpen={openRecipe}
      onToggleFavorite={handleToggleFavorite}
      togglingId={togglingId}
    />
  );
}
