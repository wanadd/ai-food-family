"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  createRecipeCollection,
  fetchRecipeCollections,
} from "@/lib/recipes/api";
import type { RecipeCollection } from "@/lib/recipes/types";

/**
 * Внутренняя вкладка «Коллекции» раздела «Меню» (Этап 2, минимальный UI).
 * Доступно: список коллекций и создание новой. Переименование/удаление и
 * богатые карточки рецептов отложены (backend не трогаем).
 */
export function CollectionsView() {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [collections, setCollections] = useState<RecipeCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [visibility, setVisibility] = useState<"personal" | "family">(
    "personal",
  );
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecipeCollections(initData, mode);
      setCollections(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить коллекции",
      );
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreate() {
    const trimmed = name.trim();
    if (!initData || !trimmed || creating) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createRecipeCollection(initData, mode, {
        name: trimmed,
        visibility,
      });
      setCollections((prev) => [created, ...prev]);
      setName("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось создать коллекцию",
      );
    } finally {
      setCreating(false);
    }
  }

  if (!initData) {
    return (
      <p className="py-12 text-center text-sm text-graphite-500">
        Коллекции доступны в Telegram Mini App после авторизации.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {error ? (
        <p className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <section className="pa-card p-4">
        <p className="text-sm font-bold text-graphite-900">Новая коллекция</p>
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Например: На неделю"
          className="mt-3 w-full rounded-control border border-cream-border bg-cream-surface py-2.5 px-3 text-sm text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
        />
        {mode === "family" ? (
          <div className="mt-3 flex gap-2">
            {(["personal", "family"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setVisibility(value)}
                className={`rounded-pill px-3 py-1.5 text-xs font-semibold transition ${
                  visibility === value
                    ? "bg-sage-500 text-white"
                    : "bg-cream-surface text-graphite-700 ring-1 ring-cream-border"
                }`}
              >
                {value === "personal" ? "Личная" : "Семейная"}
              </button>
            ))}
          </div>
        ) : null}
        <button
          type="button"
          disabled={!name.trim() || creating}
          onClick={() => void handleCreate()}
          className="pa-btn-primary mt-3 w-full disabled:opacity-50"
        >
          {creating ? "Создаю…" : "Создать коллекцию"}
        </button>
      </section>

      {loading ? (
        <div className="space-y-2" aria-label="Загрузка коллекций">
          {[0, 1].map((item) => (
            <div
              key={item}
              className="h-16 animate-pulse rounded-card border border-cream-border bg-cream-surface"
            />
          ))}
        </div>
      ) : collections.length === 0 ? (
        <p className="py-8 text-center text-sm text-graphite-500">
          Коллекций пока нет. Создайте первую выше.
        </p>
      ) : (
        <ul className="space-y-2">
          {collections.map((collection) => (
            <li key={collection.id}>
              <Link
                href={`/menu/collections/${collection.id}`}
                className="flex items-center justify-between gap-3 rounded-card border border-cream-border bg-cream-surface px-4 py-3 shadow-soft transition hover:border-sage-200"
              >
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-graphite-900">
                    {collection.emoji ? `${collection.emoji} ` : ""}
                    {collection.name}
                  </span>
                  <span className="text-xs text-graphite-500">
                    {collection.recipes_count}{" "}
                    {collection.recipes_count === 1 ? "рецепт" : "рецептов"}
                    {collection.visibility === "family" ? " · семейная" : ""}
                    {collection.is_dynamic ? " · авто" : ""}
                  </span>
                </span>
                <span className="text-graphite-400">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
