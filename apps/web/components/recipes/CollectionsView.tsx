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
      <p className="py-12 text-center text-sm text-stone-600">
        Коллекции доступны в Telegram Mini App после авторизации.
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

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-sm font-bold text-stone-900">Новая коллекция</p>
        <p className="mt-1 text-xs text-stone-500">
          Группируйте любимые рецепты. Добавлять рецепты можно из карточки
          рецепта.
        </p>
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Например: На неделю"
          className="mt-3 w-full rounded-xl border border-stone-200 bg-white py-2.5 px-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
        />
        {mode === "family" ? (
          <div className="mt-3 flex gap-2">
            {(["personal", "family"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setVisibility(value)}
                className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                  visibility === value
                    ? "bg-emerald-600 text-white"
                    : "bg-white text-stone-600 ring-1 ring-stone-200"
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
          className="mt-3 w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          {creating ? "Создаю…" : "Создать коллекцию"}
        </button>
      </section>

      {loading ? (
        <div className="space-y-2" aria-label="Загрузка коллекций">
          {[0, 1].map((item) => (
            <div
              key={item}
              className="h-16 animate-pulse rounded-2xl border border-stone-100 bg-stone-50"
            />
          ))}
        </div>
      ) : collections.length === 0 ? (
        <p className="py-8 text-center text-sm text-stone-500">
          Коллекций пока нет. Создайте первую выше.
        </p>
      ) : (
        <ul className="space-y-2">
          {collections.map((collection) => (
            <li key={collection.id}>
              <Link
                href={`/menu/collections/${collection.id}`}
                className="flex items-center justify-between gap-3 rounded-2xl border border-stone-100 bg-white px-4 py-3 shadow-sm transition hover:border-emerald-200"
              >
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-stone-900">
                    {collection.emoji ? `${collection.emoji} ` : ""}
                    {collection.name}
                  </span>
                  <span className="text-xs text-stone-500">
                    {collection.recipes_count}{" "}
                    {collection.recipes_count === 1 ? "рецепт" : "рецептов"}
                    {collection.visibility === "family" ? " · семейная" : ""}
                    {collection.is_dynamic ? " · авто" : ""}
                  </span>
                </span>
                <span className="text-stone-400">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
