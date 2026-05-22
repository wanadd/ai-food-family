"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ModeBanner } from "@/components/app-mode/ModeBanner";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { ShoppingCategorySection } from "@/components/shopping/ShoppingCategorySection";
import {
  fetchShoppingList,
  syncShoppingList,
  toggleShoppingItem,
} from "@/lib/shopping/api";
import { CATEGORY_ORDER } from "@/lib/shopping/labels";
import type { ShoppingList } from "@/lib/shopping/types";
import { getTelegramInitData } from "@/lib/telegram-webapp";

const POLL_INTERVAL_MS = 4000;

export function ShoppingListView() {
  const { mode } = useAppMode();
  const [initData, setInitData] = useState("");
  const [list, setList] = useState<ShoppingList | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const updatedAtRef = useRef<string | null>(null);

  const loadList = useCallback(
    async (telegramInitData: string, appMode: typeof mode, silent = false) => {
      if (!silent) {
        setLoading(true);
      }
      setError(null);
      try {
        const data = await fetchShoppingList(telegramInitData, appMode);
        if (
          silent &&
          updatedAtRef.current &&
          updatedAtRef.current === data.updated_at
        ) {
          return;
        }
        updatedAtRef.current = data.updated_at;
        setList(data);
      } catch (err) {
        if (!silent) {
          setError(
            err instanceof Error ? err.message : "Не удалось загрузить список",
          );
        }
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    const data = getTelegramInitData();
    setInitData(data);
    if (!data) {
      setLoading(false);
      return;
    }
    loadList(data, mode);
  }, [loadList, mode]);

  useEffect(() => {
    if (!initData) {
      return;
    }

    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        loadList(initData, mode, true);
      }
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(interval);
  }, [initData, mode, loadList]);

  const grouped = useMemo(() => {
    if (!list) {
      return [];
    }
    const buckets = new Map<string, typeof list.items>();
    for (const item of list.items) {
      const existing = buckets.get(item.category) ?? [];
      existing.push(item);
      buckets.set(item.category, existing);
    }

    const orderIndex = Object.fromEntries(
      CATEGORY_ORDER.map((category, index) => [category, index]),
    );

    return Array.from(buckets.entries()).sort(
      ([a], [b]) =>
        (orderIndex[a] ?? CATEGORY_ORDER.length) -
        (orderIndex[b] ?? CATEGORY_ORDER.length),
    );
  }, [list]);

  async function handleSync() {
    if (!initData) {
      return;
    }
    setSyncing(true);
    setError(null);
    try {
      const data = await syncShoppingList(initData, mode);
      updatedAtRef.current = data.updated_at;
      setList(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось обновить список",
      );
    } finally {
      setSyncing(false);
    }
  }

  async function handleToggle(itemId: string, checked: boolean) {
    if (!initData) {
      return;
    }

    const current = list?.items.find((item) => item.id === itemId);
    if (
      !checked &&
      current?.checked &&
      current.linked_pantry_item_id
    ) {
      const remove = window.confirm(
        `Убрать «${current.name}» из запасов?`,
      );
      setTogglingId(itemId);
      setError(null);
      try {
        const data = await toggleShoppingItem(initData, mode, itemId, false, {
          removeFromPantry: remove,
        });
        updatedAtRef.current = data.updated_at;
        setList(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Не удалось обновить позицию",
        );
      } finally {
        setTogglingId(null);
      }
      return;
    }

    setTogglingId(itemId);
    setError(null);
    try {
      const data = await toggleShoppingItem(initData, mode, itemId, checked);
      updatedAtRef.current = data.updated_at;
      setList(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось обновить позицию",
      );
    } finally {
      setTogglingId(null);
    }
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">
          Список покупок доступен в Telegram Mini App после авторизации.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-emerald-700"
        >
          На главную
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <p className="py-20 text-center text-sm text-stone-500">
        Загрузка списка…
      </p>
    );
  }

  const progress =
    list && list.total_count > 0
      ? Math.round((list.checked_count / list.total_count) * 100)
      : 0;

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-stone-100 bg-white px-5 py-6">
        <h1 className="text-2xl font-bold text-stone-900">Список покупок</h1>
        <p className="mt-1 text-sm text-stone-500">
          Из выбранного меню · синхронизация каждые 4 сек
        </p>
      </header>

      <main className="mx-auto max-w-lg space-y-6 px-5 py-8">
        <ModeBanner />
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        {list ? (
          <section className="rounded-2xl border border-stone-200 bg-white p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                  Из меню
                </p>
                <p className="mt-1 font-semibold text-stone-900">
                  {list.menu_title ?? "Меню не выбрано"}
                </p>
              </div>
              <button
                type="button"
                onClick={handleSync}
                disabled={syncing}
                className="shrink-0 rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
              >
                {syncing ? "…" : "Обновить"}
              </button>
            </div>

            <div className="mt-4">
              <div className="mb-1 flex justify-between text-xs font-medium text-stone-500">
                <span>
                  Куплено {list.checked_count} из {list.total_count}
                </span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-stone-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </section>
        ) : null}

        {list && list.items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-stone-200 bg-white p-8 text-center">
            <p className="text-sm text-stone-600">
              Список пуст. Выберите меню на странице AI Меню — ингредиенты
              появятся автоматически.
            </p>
            <Link
              href="/menu"
              className="mt-4 inline-block text-sm font-semibold text-emerald-700"
            >
              Перейти к меню →
            </Link>
          </div>
        ) : null}

        {grouped.map(([category, items]) => (
          <ShoppingCategorySection
            key={category}
            category={category}
            items={items}
            togglingId={togglingId}
            onToggle={handleToggle}
          />
        ))}
      </main>

      <BottomBackButton className="pb-4 pt-2" />
    </div>
  );
}
