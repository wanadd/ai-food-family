"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { StickyBottomBar } from "@/components/layout/StickyBottomBar";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  createMealLeftover,
  deleteMealLeftover,
  fetchMealLeftovers,
  type MealLeftover,
} from "@/lib/meal-leftovers/api";

export function MealLeftoversPage() {
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();
  const [items, setItems] = useState<MealLeftover[]>([]);
  const [loading, setLoading] = useState(true);
  const [dishName, setDishName] = useState("");
  const [portions, setPortions] = useState("2");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!initData) return;
    setLoading(true);
    try {
      setItems(await fetchMealLeftovers(initData, mode));
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading) return;
    void load();
  }, [load, modeLoading]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!initData || !dishName.trim()) return;
    setSaving(true);
    try {
      await createMealLeftover(initData, mode, {
        dish_name: dishName.trim(),
        portions_remaining: parseInt(portions, 10) || 1,
      });
      setDishName("");
      setPortions("2");
      await load();
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50">
        <PageLoading message="Загрузка…" />
      </div>
    );
  }

  return (
    <ScreenLayout
      title="Остатки блюд"
      subtitle="Учтём при следующем меню и покупках"
      back={{ label: "Меню", href: "/menu" }}
      contentClassName="space-y-3"
    >
      <ul className="space-y-2">
        {items.length === 0 ? (
          <li className="rounded-xl border border-dashed border-stone-200 px-4 py-6 text-center text-sm text-stone-500">
            Пока нет остатков. Отметьте блюдо, которое осталось с прошлого дня.
          </li>
        ) : (
          items.map((item) => (
            <li
              key={item.id}
              className="flex items-start justify-between gap-2 rounded-2xl border border-stone-100 bg-white p-4 shadow-sm"
            >
              <div>
                <p className="font-semibold text-stone-900">{item.dish_name}</p>
                <p className="mt-0.5 text-sm text-stone-500">
                  {item.portions_remaining} порц.
                  {item.valid_until
                    ? ` · до ${new Date(item.valid_until).toLocaleDateString("ru-RU")}`
                    : ""}
                </p>
              </div>
              <button
                type="button"
                onClick={() => void deleteMealLeftover(initData!, mode, item.id).then(load)}
                className="text-xs font-semibold text-red-600"
              >
                Удалить
              </button>
            </li>
          ))
        )}
      </ul>

      <StickyBottomBar>
        <form onSubmit={(e) => void handleAdd(e)} className="space-y-2">
          <input
            value={dishName}
            onChange={(e) => setDishName(e.target.value)}
            placeholder="Название блюда, например Борщ"
            className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm"
          />
          <div className="flex gap-2">
            <input
              type="number"
              min={1}
              max={50}
              value={portions}
              onChange={(e) => setPortions(e.target.value)}
              className="w-24 rounded-xl border border-stone-200 px-3 py-2.5 text-sm"
              aria-label="Порций"
            />
            <button
              type="submit"
              disabled={saving || !dishName.trim()}
              className="flex-1 rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
            >
              {saving ? "…" : "Добавить остаток"}
            </button>
          </div>
        </form>
      </StickyBottomBar>
    </ScreenLayout>
  );
}
