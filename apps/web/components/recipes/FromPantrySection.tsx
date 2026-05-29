"use client";

import { useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchRecipesFromPantry } from "@/lib/recipes/api";
import { createShoppingItem } from "@/lib/shopping/api";
import type { FromPantryRecipe } from "@/lib/recipes/types";

type FromPantrySectionProps = {
  onOpen: (id: number) => void;
};

/**
 * «Что приготовить из того, что есть дома» — единственная точка входа
 * в подбор из запасов внутри Рецептов (Этап 2). Раздел загружает данные
 * сам и умеет докинуть недостающие ингредиенты в покупки.
 */
export function FromPantrySection({ onOpen }: FromPantrySectionProps) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [items, setItems] = useState<FromPantryRecipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [addingFor, setAddingFor] = useState<number | null>(null);

  useEffect(() => {
    if (!initData) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchRecipesFromPantry(initData, mode)
      .then((data) => {
        if (!cancelled) setItems(data.items);
      })
      .catch((err) => {
        if (cancelled) return;
        setItems([]);
        setError(
          err instanceof Error ? err.message : "Не удалось загрузить идеи из запасов",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [initData, mode]);

  async function handleAddMissing(item: FromPantryRecipe) {
    if (!initData || item.missing_ingredients.length === 0) return;
    setAddingFor(item.recipe_id);
    setNotice(null);
    setError(null);
    try {
      for (const name of item.missing_ingredients) {
        await createShoppingItem(initData, mode, {
          name,
          category: "продукты",
          quantity: "1",
          unit: "шт",
          note: `Для рецепта: ${item.title}`,
          is_food: true,
        });
      }
      setNotice("Недостающие ингредиенты добавлены в покупки.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось добавить в покупки",
      );
    } finally {
      setAddingFor(null);
    }
  }

  return (
    <section className="rounded-2xl border border-amber-100 bg-amber-50/50 p-3">
      <p className="text-sm font-bold text-stone-900">
        Что приготовить из того, что есть дома
      </p>
      <p className="mt-1 text-xs text-stone-600">
        Смотрим текущие запасы и показываем, чего не хватает.
      </p>

      {notice ? (
        <p className="mt-2 rounded-xl bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
          {notice}
        </p>
      ) : null}

      {loading ? (
        <div className="mt-3 space-y-2">
          <div className="h-16 animate-pulse rounded-xl bg-amber-100" />
          <div className="h-16 animate-pulse rounded-xl bg-amber-100/70" />
        </div>
      ) : error ? (
        <p className="mt-3 text-sm text-amber-900">{error}</p>
      ) : items.length === 0 ? (
        <p className="mt-3 text-sm text-stone-600">
          Пока не нашли совпадений. Добавьте продукты в запасы — и идеи появятся
          здесь.
        </p>
      ) : (
        <div className="mt-3 space-y-3">
          {items.slice(0, 3).map((item) => (
            <article
              key={item.recipe_id}
              className="rounded-xl border border-amber-100 bg-white p-3"
            >
              <p className="font-semibold text-stone-900">{item.title}</p>
              <p className="mt-1 text-xs text-stone-600">
                Совпадает: {item.have} из {item.total} ингредиентов
              </p>
              <p className="mt-1 text-xs text-stone-600">
                Нужно докупить: {item.missing_ingredients.length}{" "}
                {item.missing_ingredients.length === 1
                  ? "ингредиент"
                  : "ингредиента"}
              </p>
              {item.missing_ingredients.length > 0 ? (
                <p className="mt-1 line-clamp-2 text-xs text-stone-500">
                  {item.missing_ingredients.join(", ")}
                </p>
              ) : null}
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => onOpen(item.recipe_id)}
                  className="rounded-xl bg-stone-900 px-3 py-2 text-xs font-semibold text-white"
                >
                  Посмотреть рецепт
                </button>
                {item.missing_ingredients.length > 0 ? (
                  <button
                    type="button"
                    disabled={addingFor === item.recipe_id}
                    onClick={() => void handleAddMissing(item)}
                    className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-900 disabled:opacity-50"
                  >
                    {addingFor === item.recipe_id
                      ? "Добавляю…"
                      : "Добавить недостающее в покупки"}
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
