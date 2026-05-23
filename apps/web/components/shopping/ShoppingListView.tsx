"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BotQuickInputHint } from "@/components/bot/BotQuickInputHint";
import { ModeBanner } from "@/components/app-mode/ModeBanner";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { PageLoading } from "@/components/ui/PageLoading";
import { ShoppingCategorySection } from "@/components/shopping/ShoppingCategorySection";
import { ShoppingCategorySheet } from "@/components/shopping/ShoppingCategorySheet";
import { ShoppingItemSheet } from "@/components/shopping/ShoppingItemSheet";
import {
  createShoppingCategory,
  createShoppingItem,
  deleteShoppingItem,
  fetchShoppingList,
  syncShoppingList,
  toggleShoppingItem,
  updateShoppingItem,
} from "@/lib/shopping/api";
import { categoryMeta } from "@/lib/shopping/labels";
import {
  EMPTY_SHOPPING_DRAFT,
  type ShoppingItemDraft,
  type ShoppingList,
  type ShoppingListItem,
} from "@/lib/shopping/types";

const POLL_INTERVAL_MS = 4000;

export function ShoppingListView() {
  const { mode } = useAppMode();
  const { initData } = useTelegram();
  const [list, setList] = useState<ShoppingList | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [hideChecked, setHideChecked] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [itemSheetOpen, setItemSheetOpen] = useState(false);
  const [categorySheetOpen, setCategorySheetOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ShoppingListItem | null>(null);
  const [itemDraft, setItemDraft] = useState<ShoppingItemDraft>(EMPTY_SHOPPING_DRAFT);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [newCategoryIsFood, setNewCategoryIsFood] = useState(false);
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
    if (!initData) {
      setLoading(false);
      return;
    }
    loadList(initData, mode);
  }, [initData, loadList, mode]);

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

  const filteredItems = useMemo(() => {
    if (!list) {
      return [];
    }
    const query = search.trim().toLowerCase();
    return list.items.filter((item) => {
      if (hideChecked && item.checked) {
        return false;
      }
      if (!query) {
        return true;
      }
      return item.name.toLowerCase().includes(query);
    });
  }, [list, search, hideChecked]);

  const grouped = useMemo(() => {
    const buckets = new Map<string, ShoppingListItem[]>();
    for (const item of filteredItems) {
      const existing = buckets.get(item.category) ?? [];
      existing.push(item);
      buckets.set(item.category, existing);
    }
    const categories = list?.categories ?? [];
    return Array.from(buckets.entries()).sort(([a], [b]) => {
      const labelA = categoryMeta(a, categories).label;
      const labelB = categoryMeta(b, categories).label;
      return labelA.localeCompare(labelB, "ru");
    });
  }, [filteredItems, list?.categories]);

  const categorySlugsFromItems = useMemo(() => {
    if (!list) {
      return [];
    }
    return Array.from(new Set(list.items.map((item) => item.category)));
  }, [list]);

  const progress =
    list && list.total_count > 0
      ? Math.round((list.checked_count / list.total_count) * 100)
      : 0;

  function openAddItem() {
    setEditingItem(null);
    setItemDraft({ ...EMPTY_SHOPPING_DRAFT });
    setItemSheetOpen(true);
  }

  function openEditItem(item: ShoppingListItem) {
    setEditingItem(item);
    setItemDraft({
      name: item.name,
      category: item.category,
      quantity: item.quantity || "1",
      unit: item.unit || "шт",
      note: item.note ?? "",
      is_food: true,
    });
    setItemSheetOpen(true);
  }

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
        err instanceof Error ? err.message : "Не удалось обновить из меню",
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
      (current.added_to_pantry || current.linked_pantry_item_id)
    ) {
      const remove = window.confirm("Убрать товар из запасов?");
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

  async function handleSaveItem() {
    if (!initData) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      let data: ShoppingList;
      if (editingItem) {
        data = await updateShoppingItem(initData, mode, editingItem.id, {
          name: itemDraft.name,
          category: itemDraft.category,
          quantity: itemDraft.quantity,
          unit: itemDraft.unit,
          note: itemDraft.note || null,
        });
      } else {
        data = await createShoppingItem(initData, mode, itemDraft);
      }
      updatedAtRef.current = data.updated_at;
      setList(data);
      setItemSheetOpen(false);
      setEditingItem(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteItem(item: ShoppingListItem) {
    if (!initData) {
      return;
    }
    if (!window.confirm(`Удалить «${item.name}» из списка?`)) {
      return;
    }
    setError(null);
    try {
      const data = await deleteShoppingItem(initData, mode, item.id);
      updatedAtRef.current = data.updated_at;
      setList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить");
    }
  }

  async function handleCreateCategory() {
    if (!initData) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createShoppingCategory(
        initData,
        mode,
        newCategoryName.trim(),
        newCategoryIsFood,
      );
      await loadList(initData, mode, true);
      setCategorySheetOpen(false);
      setNewCategoryName("");
      setNewCategoryIsFood(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось создать категорию",
      );
    } finally {
      setSaving(false);
    }
  }

  function toggleCategoryExpanded(slug: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      return next;
    });
  }

  function expandAll() {
    setExpanded(new Set(grouped.map(([slug]) => slug)));
  }

  function collapseAll() {
    setExpanded(new Set());
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">
          Покупки доступны в Telegram Mini App после авторизации.
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
    return <PageLoading message="Загружаем покупки..." />;
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="sticky top-0 z-10 border-b border-stone-100 bg-white/95 px-4 py-4 backdrop-blur-sm">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-stone-900">Покупки</h1>
            <p className="mt-0.5 text-xs text-stone-500">
              Всё, что нужно купить для дома и меню
            </p>
          </div>
          <button
            type="button"
            onClick={openAddItem}
            className="shrink-0 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white"
          >
            + Добавить
          </button>
        </div>

        {list ? (
          <div className="mt-3">
            <div className="mb-1 flex justify-between text-[11px] font-medium text-stone-500">
              <span>
                Куплено {list.checked_count} из {list.total_count}
              </span>
              <span>{progress}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-stone-100">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : null}
      </header>

      <main className="mx-auto max-w-lg space-y-3 px-4 py-4">
        <BotQuickInputHint />
        <ModeBanner />

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Найти товар"
          className="w-full rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm"
        />

        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={expandAll}
            className="rounded-md border border-stone-200 bg-white px-2 py-1 text-[11px] font-semibold text-stone-600"
          >
            Развернуть всё
          </button>
          <button
            type="button"
            onClick={collapseAll}
            className="rounded-md border border-stone-200 bg-white px-2 py-1 text-[11px] font-semibold text-stone-600"
          >
            Свернуть всё
          </button>
          <button
            type="button"
            onClick={() => setHideChecked((value) => !value)}
            className={`rounded-md border px-2 py-1 text-[11px] font-semibold ${
              hideChecked
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-stone-200 bg-white text-stone-600"
            }`}
          >
            Скрыть купленные
          </button>
          <button
            type="button"
            onClick={() => setCategorySheetOpen(true)}
            className="rounded-md border border-stone-200 bg-white px-2 py-1 text-[11px] font-semibold text-stone-600"
          >
            + Категория
          </button>
          <button
            type="button"
            onClick={handleSync}
            disabled={syncing}
            className="rounded-md border border-emerald-200 bg-white px-2 py-1 text-[11px] font-semibold text-emerald-700 disabled:opacity-50"
          >
            {syncing ? "…" : "Из меню"}
          </button>
        </div>

        {list && list.items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-stone-200 bg-white px-4 py-8 text-center">
            <p className="text-sm text-stone-600">
              Список пуст. Выберите меню — ингредиенты появятся после синхронизации.
            </p>
            <Link
              href="/menu"
              className="mt-3 inline-block text-sm font-semibold text-emerald-700"
            >
              Перейти к меню →
            </Link>
          </div>
        ) : null}

        {grouped.length === 0 && list && list.items.length > 0 ? (
          <p className="py-6 text-center text-sm text-stone-400">
            Ничего не найдено
          </p>
        ) : null}

        <div className="space-y-2">
          {grouped.map(([category, items]) => (
            <ShoppingCategorySection
              key={category}
              category={category}
              items={items}
              categories={list?.categories ?? []}
              expanded={expanded.has(category)}
              togglingId={togglingId}
              onToggleExpand={() => toggleCategoryExpanded(category)}
              onToggleItem={handleToggle}
              onEditItem={openEditItem}
              onDeleteItem={handleDeleteItem}
            />
          ))}
        </div>
      </main>

      <ShoppingItemSheet
        open={itemSheetOpen}
        title={editingItem ? "Редактировать" : "Добавить товар"}
        draft={itemDraft}
        categories={list?.categories ?? []}
        categorySlugsFromItems={categorySlugsFromItems}
        onChange={setItemDraft}
        onClose={() => {
          setItemSheetOpen(false);
          setEditingItem(null);
        }}
        onSubmit={handleSaveItem}
        loading={saving}
      />

      <ShoppingCategorySheet
        open={categorySheetOpen}
        name={newCategoryName}
        isFood={newCategoryIsFood}
        onNameChange={setNewCategoryName}
        onIsFoodChange={setNewCategoryIsFood}
        onClose={() => setCategorySheetOpen(false)}
        onSubmit={handleCreateCategory}
        loading={saving}
      />
    </div>
  );
}
