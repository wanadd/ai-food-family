"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MenuSectionLayout } from "@/components/menu/MenuSectionLayout";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchRecipeCollectionDetail } from "@/lib/recipes/api";
import type { RecipeCollectionDetail } from "@/lib/recipes/types";

/**
 * Деталь коллекции (Этап 2, минимальный UI). Показывает мету коллекции и
 * количество/список recipe_ids без N+1 запросов. Полные карточки рецептов —
 * позже (Этап 2 не расширяет backend GET /collections/{id}).
 */
export function CollectionDetailView() {
  const params = useParams();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const collectionId = Number(params.id);
  const [detail, setDetail] = useState<RecipeCollectionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!initData || !collectionId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecipeCollectionDetail(initData, mode, collectionId);
      setDetail(data);
      if (!data) setError("Коллекция не найдена");
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

  const recipeIds = detail?.recipe_ids ?? [];

  return (
    <MenuSectionLayout subtitle="Коллекция рецептов">
      <Link
        href="/menu/collections"
        className="inline-block text-sm font-semibold text-emerald-700"
      >
        ← Все коллекции
      </Link>

      {!initData ? (
        <p className="py-12 text-center text-sm text-stone-600">
          Коллекции доступны в Telegram Mini App после авторизации.
        </p>
      ) : loading ? (
        <div className="h-24 animate-pulse rounded-2xl border border-stone-100 bg-stone-50" />
      ) : error ? (
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : detail ? (
        <>
          <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
            <p className="text-lg font-bold text-stone-900">
              {detail.collection.emoji ? `${detail.collection.emoji} ` : ""}
              {detail.collection.name}
            </p>
            {detail.collection.description ? (
              <p className="mt-1 text-sm text-stone-600">
                {detail.collection.description}
              </p>
            ) : null}
            <p className="mt-2 text-xs text-stone-500">
              {recipeIds.length}{" "}
              {recipeIds.length === 1 ? "рецепт" : "рецептов"}
              {detail.collection.visibility === "family" ? " · семейная" : ""}
            </p>
          </section>

          {recipeIds.length === 0 ? (
            <p className="py-8 text-center text-sm text-stone-500">
              В коллекции пока нет рецептов. Откройте рецепт и добавьте его в
              эту коллекцию.
            </p>
          ) : (
            <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
              <p className="text-sm font-semibold text-stone-900">
                Рецепты в коллекции
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {recipeIds.map((id) => (
                  <Link
                    key={id}
                    href={`/recipes/${id}`}
                    className="rounded-full bg-stone-100 px-3 py-1.5 text-xs font-semibold text-stone-700 hover:bg-stone-200"
                  >
                    Рецепт #{id}
                  </Link>
                ))}
              </div>
              <p className="mt-3 text-xs text-stone-400">
                Полные карточки рецептов появятся здесь позже.
              </p>
            </section>
          )}
        </>
      ) : null}
    </MenuSectionLayout>
  );
}
