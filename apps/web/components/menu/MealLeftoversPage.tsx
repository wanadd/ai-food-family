"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ShoppingSectionLayout } from "@/components/shopping/ShoppingSectionLayout";
import { StickyBottomBar } from "@/components/layout/StickyBottomBar";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  createMealLeftover,
  deleteMealLeftover,
  fetchMealLeftovers,
  updateMealLeftover,
  type MealLeftover,
} from "@/lib/meal-leftovers/api";
import {
  LEFTOVER_STATUS_OPTIONS,
  leftoverStatusLabel,
  type LeftoverStatus,
} from "@/lib/meal-leftovers/status";

export function MealLeftoversPage() {
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();
  const [items, setItems] = useState<MealLeftover[]>([]);
  const [loading, setLoading] = useState(true);
  const [dishName, setDishName] = useState("");
  const [portions, setPortions] = useState("2");
  const [saving, setSaving] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

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
    setSaveSuccess(null);
    try {
      await createMealLeftover(initData, mode, {
        dish_name: dishName.trim(),
        portions_remaining: parseInt(portions, 10) || 1,
      });
      setDishName("");
      setSaveSuccess("✓ Добавлено");
      await load();
      window.setTimeout(() => document.getElementById("leftover-dish-name")?.focus(), 80);
    } finally {
      setSaving(false);
    }
  }

  async function setStatus(item: MealLeftover, status: LeftoverStatus) {
    if (!initData) return;
    setUpdatingId(item.id);
    try {
      const portions =
        status === "consumed" || status === "discarded" ? 0 : item.portions_remaining;
      await updateMealLeftover(initData, mode, item.id, {
        leftover_status: status,
        portions_remaining: portions,
      });
      await load();
    } finally {
      setUpdatingId(null);
    }
  }

  if (loading) {
    return (
      <ShoppingSectionLayout subtitle="Остатки блюд · влияют на меню и запасы">
        <PageLoading message="Загрузка…" />
      </ShoppingSectionLayout>
    );
  }

  return (
    <ShoppingSectionLayout
      subtitle="Остатки блюд · влияют на меню, запасы и покупки"
      contentClassName="space-y-3 pb-32"
    >
      <p className="text-xs text-stone-500">
        Отметьте статус — ПланАм учтёт при следующем плане. «Осталось» и «Заморожено»
        попадают в генерацию меню.
      </p>

      <ul className="space-y-2">
        {items.length === 0 ? (
          <li className="rounded-xl border border-dashed border-stone-200 px-4 py-6 text-center text-sm text-stone-500">
            Пока нет остатков. Добавьте блюдо ниже или отметьте приём пищи в текущем
            меню.
          </li>
        ) : (
          items.map((item) => (
            <li
              key={item.id}
              className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-stone-900">{item.dish_name}</p>
                  <p className="mt-0.5 text-sm text-stone-500">
                    {item.portions_remaining} порц. ·{" "}
                    {leftoverStatusLabel(item.leftover_status ?? "active")}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void deleteMealLeftover(initData!, mode, item.id).then(load)}
                  className="text-xs font-semibold text-red-600"
                >
                  Удалить
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {LEFTOVER_STATUS_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    disabled={updatingId === item.id}
                    onClick={() => void setStatus(item, opt.value)}
                    className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                      (item.leftover_status ?? "active") === opt.value
                        ? "bg-emerald-600 text-white"
                        : "bg-stone-100 text-stone-700"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </li>
          ))
        )}
      </ul>

      <Link
        href="/menu/current"
        className="block text-center text-sm font-semibold text-emerald-700"
      >
        Отметить приёмы пищи в меню →
      </Link>

      <StickyBottomBar>
        <form onSubmit={(e) => void handleAdd(e)} className="space-y-2">
          {saveSuccess ? (
            <p className="text-center text-sm font-semibold text-emerald-800">
              {saveSuccess}
            </p>
          ) : null}
          <input
            id="leftover-dish-name"
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
    </ShoppingSectionLayout>
  );
}
