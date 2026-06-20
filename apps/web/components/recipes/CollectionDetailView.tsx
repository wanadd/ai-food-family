"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MenuSectionLayout } from "@/components/menu/MenuSectionLayout";
import { RecipeListSkeleton } from "@/components/recipes/RecipeListSkeleton";
import { RecipeResultsList } from "@/components/recipes/RecipeResultsList";
import { useTelegram } from "@/components/TelegramProvider";
import {
  fetchRecipeCollectionDetail,
  fetchRecipes,
  toggleRecipeFavorite,
} from "@/lib/recipes/api";
import type { RecipeCollectionDetail, RecipeSummary } from "@/lib/recipes/types";

export function CollectionDetailView() {
  const params = useParams();
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const collectionId = Number(params.id);
  const [detail, setDetail] = useState<RecipeCollectionDetail | null>(null);
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!initData || !collectionId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecipeCollectionDetail(initData, mode, collectionId);
      if (!data) {
        setDetail(null);
        setRecipes([]);
        setError("Коллекция не найдена");
        return;
      }
      setDetail(data);

      const ids = data.recipe_ids ?? [];
      if (ids.length === 0) {
        setRecipes([]);
        return;
      }

      const catalog = await fetchRecipes(initData, {});
      const byId = new Map(catalog.items.map((item) => [item.id, item]));
      setRecipes(
        ids
          .map((id) => byId.get(id))
          .filter((item): item is RecipeSummary => item != null),
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить коллекцию",
      );
    } finally {
      setLoading(false);
    }
  }, [initData, mode, collectionId]);

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
          prev.map((item) =>
            item.id === id ? { ...item, is_favorited: result.is_favorited } : item,
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

  const recipeIds = detail?.recipe_ids ?? [];

  return (
    <MenuSectionLayout subtitle="Коллекция рецептов">
      <Link
        href="/menu/collections"
        className="inline-block text-sm font-semibold text-sage-700"
      >
        ← Все коллекции
      </Link>

      {!initData ? (
        <p className="py-12 text-center text-sm text-graphite-500">
          Коллекции доступны в Telegram Mini App после авторизации.
        </p>
      ) : loading ? (
        <RecipeListSkeleton count={3} />
      ) : error ? (
        <p className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : detail ? (
        <>
          <section className="pa-card p-4">
            <p className="text-lg font-bold text-graphite-900">
              {detail.collection.emoji ? `${detail.collection.emoji} ` : ""}
              {detail.collection.name}
            </p>
            {detail.collection.description ? (
              <p className="mt-1 text-sm text-graphite-600">
                {detail.collection.description}
              </p>
            ) : null}
            <p className="mt-2 text-xs text-graphite-500">
              {recipeIds.length}{" "}
              {recipeIds.length === 1 ? "рецепт" : "рецептов"}
              {detail.collection.visibility === "family" ? " · семейная" : ""}
            </p>
          </section>

          {recipeIds.length === 0 ? (
            <p className="py-8 text-center text-sm text-graphite-500">
              В коллекции пока нет рецептов. Откройте рецепт и добавьте его в
              эту коллекцию.
            </p>
          ) : recipes.length === 0 ? (
            <p className="py-8 text-center text-sm text-graphite-500">
              Рецепты коллекции временно недоступны в каталоге.
            </p>
          ) : (
            <RecipeResultsList
              recipes={recipes}
              onOpen={openRecipe}
              onToggleFavorite={handleToggleFavorite}
              togglingId={togglingId}
            />
          )}
        </>
      ) : null}
    </MenuSectionLayout>
  );
}
