"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { RecipeDetailModal } from "@/components/recipes/RecipeDetailModal";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchRecipe, toggleRecipeFavorite } from "@/lib/recipes/api";
import type { RecipeDetail } from "@/lib/recipes/types";

export default function RecipeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { initData } = useTelegram();
  const recipeId = Number(params.id);
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState(false);

  const load = useCallback(async () => {
    if (!initData || !recipeId) return;
    try {
      const data = await fetchRecipe(initData, recipeId);
      setRecipe(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Рецепт не найден");
    }
  }, [initData, recipeId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleFavorite() {
    if (!initData || !recipe) return;
    setToggling(true);
    try {
      const result = await toggleRecipeFavorite(initData, recipe.id);
      setRecipe({ ...recipe, is_favorited: result.is_favorited });
    } finally {
      setToggling(false);
    }
  }

  if (!initData) {
    return (
      <ScreenLayout title="Рецепт" back={{ label: "Меню", href: "/menu" }}>
        <p className="text-sm text-graphite-600">Откройте в Telegram Mini App.</p>
      </ScreenLayout>
    );
  }

  if (error) {
    return (
      <ScreenLayout title="Рецепт" back={{ label: "Рецепты", href: "/menu/recipes" }}>
        <p className="text-sm text-red-600">{error}</p>
        <Link
          href="/menu/recipes"
          className="mt-4 text-sm font-semibold text-emerald-700"
        >
          ← К рецептам
        </Link>
      </ScreenLayout>
    );
  }

  if (!recipe) {
    return (
      <ScreenLayout title="Рецепт" back={{ label: "Рецепты", href: "/menu/recipes" }}>
        <p className="text-sm text-graphite-500">Загрузка…</p>
      </ScreenLayout>
    );
  }

  return (
    <RecipeDetailModal
      recipe={recipe}
      onClose={() => router.push("/menu/recipes")}
      onToggleFavorite={handleFavorite}
      togglingFavorite={toggling}
    />
  );
}
