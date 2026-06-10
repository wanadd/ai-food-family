"use client";

/**
 * PLANAM V2 — Список покупок (/shopping).
 * Простой чеклист: фильтры [Купить][Все][Куплено], нормализованные
 * категории (taxonomy guard), full-row toggle, один page scroll.
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { AiProcessLoadingV2 } from "@/components/planam-v2/ai/AiProcessLoadingV2";
import { HomeDomainSegmentV2 } from "@/components/planam-v2/home-domain/HomeDomainSegmentV2";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
  V2EmptyState,
  V2ProgressBar,
} from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { groupShoppingItems } from "@/lib/dom/shopping-groups";
import { cn } from "@/lib/planam/cn";
import {
  formatProductQuantity,
  normalizeProductName,
  detectProductCategory,
} from "@/lib/planam/productTaxonomy";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import {
  createShoppingItem,
  fetchShoppingCategories,
  fetchShoppingList,
  syncShoppingList,
  toggleShoppingItem,
} from "@/lib/shopping/api";
import { SHOPPING_CATEGORIES_V1 } from "@/lib/shopping/categories-v1";
import type {
  ShoppingItemDraft,
  ShoppingList,
  ShoppingListItem,
} from "@/lib/shopping/types";
import { EMPTY_SHOPPING_DRAFT } from "@/lib/shopping/types";

type ShoppingFilter = "to-buy" | "all" | "bought";

const FILTERS: { id: ShoppingFilter; label: string }[] = [
  { id: "to-buy", label: "Купить" },
  { id: "all", label: "Все" },
  { id: "bought", label: "Куплено" },
];

export function ShoppingV2() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const cacheK = cacheKey.shoppingList(mode);

  const [list, setList] = useState<ShoppingList | null>(() =>
    initData ? getCached<ShoppingList>(cacheK) : null,
  );
  const [loading, setLoading] = useState(list == null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<ShoppingFilter>("to-buy");
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [draft, setDraft] = useState<ShoppingItemDraft>(EMPTY_SHOPPING_DRAFT);
  const [adding, setAdding] = useState(false);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const [data, extraCats] = await Promise.all([
        fetchShoppingList(initData, mode),
        fetchShoppingCategories(initData, mode).catch(() => []),
      ]);
      const catMap = new Map<number, ShoppingList["categories"][number]>();
      for (const c of [...(data.categories ?? []), ...extraCats]) {
        catMap.set(c.id, c);
      }
      const merged: ShoppingList = {
        ...data,
        categories: Array.from(catMap.values()),
      };
      setCached(cacheK, merged);
      setList(merged);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить список");
    } finally {
      setLoading(false);
    }
  }, [initData, mode, cacheK]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    if (!list) {
      return [];
    }
    return list.items.filter((item) => {
      if (filter === "to-buy") {
        return !item.checked;
      }
      if (filter === "bought") {
        return item.checked;
      }
      return true;
    });
  }, [list, filter]);

  const groups = useMemo(
    () => groupShoppingItems(filtered, list?.categories ?? []),
    [filtered, list?.categories],
  );

  const uncheckedCount = list ? list.total_count - list.checked_count : 0;
  const percent =
    list && list.total_count > 0
      ? Math.round((list.checked_count / list.total_count) * 100)
      : 0;

  async function handleSync() {
    if (!initData) {
      return;
    }
    setSyncing(true);
    setError(null);
    try {
      const data = await syncShoppingList(initData, mode);
      setCached(cacheK, data);
      setList(data);
      invalidateCache("menu-overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось обновить из меню");
    } finally {
      setSyncing(false);
    }
  }

  async function handleToggle(item: ShoppingListItem) {
    if (!initData) {
      return;
    }
    const nextChecked = !item.checked;
    let removeFromPantry: boolean | undefined;
    if (
      !nextChecked &&
      item.checked &&
      (item.added_to_pantry || item.linked_pantry_item_id)
    ) {
      removeFromPantry = window.confirm("Товар уже в запасах. Убрать и оттуда?");
    }
    setTogglingId(item.id);
    try {
      const data = await toggleShoppingItem(initData, mode, item.id, nextChecked, {
        removeFromPantry,
      });
      setCached(cacheK, data);
      setList(data);
      if (nextChecked || removeFromPantry) {
        invalidateCache("pantry");
        invalidateCache("menu-overview");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось обновить");
    } finally {
      setTogglingId(null);
    }
  }

  async function handleAdd() {
    if (!initData || !draft.name.trim()) {
      return;
    }
    setAdding(true);
    setError(null);
    try {
      const category =
        draft.category && draft.category !== "другое"
          ? draft.category
          : detectProductCategory(draft.name, draft.category);
      const data = await createShoppingItem(initData, mode, {
        ...draft,
        category,
      });
      setCached(cacheK, data);
      setList(data);
      setAddOpen(false);
      setDraft(EMPTY_SHOPPING_DRAFT);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось добавить продукт");
    } finally {
      setAdding(false);
    }
  }

  if (loading && !list) {
    return (
      <div className="px-4 pb-6 pt-4">
        <AiProcessLoadingV2
          variant="shopping"
          title="Загружаем список покупок"
          subtitle="Проверяем меню и запасы дома"
        />
      </div>
    );
  }

  if (!initData) {
    return (
      <div className="px-4 py-8">
        <V2EmptyState
          icon={<span aria-hidden>🛒</span>}
          title="Список покупок"
          description="Откройте ПланАм в Telegram — список появится после меню или синхронизации."
          actionLabel="На главную"
          onAction={() => router.push("/")}
        />
      </div>
    );
  }

  const emptyList = list && list.total_count === 0;
  const noResults = list && list.total_count > 0 && filtered.length === 0;

  return (
    <div className="pb-6">
      <div className="px-4 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <h1 className="pa26-page-title">Список покупок</h1>
        <p className="pa26-micro mt-0.5 text-pa-muted">
          {uncheckedCount > 0
            ? `${uncheckedCount} ${plural(uncheckedCount, "товар", "товара", "товаров")} к покупке`
            : "Всё куплено"}
        </p>

        <HomeDomainSegmentV2 active="shopping" className="mt-3" />

        {list && list.total_count > 0 ? (
          <V2ProgressBar percent={percent} className="mt-3" />
        ) : null}

        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {FILTERS.map((f) => (
            <V2Chip
              key={f.id}
              label={f.label}
              active={filter === f.id}
              onClick={() => setFilter(f.id)}
            />
          ))}
          <V2Chip label={syncing ? "Обновляем…" : "Из меню"} onClick={() => void handleSync()} />
        </div>
      </div>

      <div className="px-4 pt-3">
        {error ? (
          <p className="mb-3 rounded-card border border-pa-error/30 bg-pa-error/5 px-3 py-2 pa26-caption text-pa-error">
            {error}
          </p>
        ) : null}

        {emptyList ? (
          <V2EmptyState
            icon={<span aria-hidden>🛒</span>}
            title="Покупок пока нет"
            description="Соберите меню или добавьте продукт вручную."
            actionLabel="Собрать меню"
            onAction={() => router.push(PLANAM_ROUTES.planGenerate)}
          />
        ) : noResults ? (
          <V2EmptyState
            title={filter === "bought" ? "Куплено пока ничего" : "Всё куплено"}
            description={
              filter === "bought"
                ? "Отмечайте товары — они появятся здесь."
                : "Можно собрать меню или добавить продукт вручную."
            }
            actionLabel="Показать все"
            onAction={() => setFilter("all")}
          />
        ) : (
          <div className="space-y-4">
            {groups.map((group) => (
              <section key={group.category}>
                <h2 className="pa26-section-title flex items-center gap-2">
                  <span aria-hidden>{group.emoji}</span>
                  {group.label}
                </h2>
                <ul className="mt-2 overflow-hidden rounded-card border border-pa-border bg-pa-surface">
                  {group.items.map((item, idx) => (
                    <ShoppingRowV2
                      key={item.id}
                      item={item}
                      busy={togglingId === item.id}
                      divider={idx > 0}
                      onToggle={() => void handleToggle(item)}
                    />
                  ))}
                </ul>
              </section>
            ))}
          </div>
        )}

        <div className="mt-5 space-y-2">
          <V2Button variant="primary" size="wide" onClick={() => setAddOpen(true)}>
            Добавить продукт
          </V2Button>
        </div>
      </div>

      <V2BottomSheet
        open={addOpen}
        title="Добавить продукт"
        onClose={() => setAddOpen(false)}
        footer={
          <V2Button
            variant="primary"
            size="wide"
            loading={adding}
            disabled={!draft.name.trim()}
            onClick={() => void handleAdd()}
          >
            Добавить
          </V2Button>
        }
      >
        <div className="space-y-3 pb-2">
          <label className="block">
            <span className="pa26-micro font-semibold text-pa-muted">Название</span>
            <input
              type="text"
              value={draft.name}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  name: e.target.value,
                  category: detectProductCategory(e.target.value),
                }))
              }
              placeholder="Например: брокколи"
              className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
            />
          </label>
          <div className="flex gap-2">
            <label className="block flex-1">
              <span className="pa26-micro font-semibold text-pa-muted">Количество</span>
              <input
                type="text"
                inputMode="decimal"
                value={draft.quantity}
                onChange={(e) => setDraft((d) => ({ ...d, quantity: e.target.value }))}
                className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
              />
            </label>
            <label className="block flex-1">
              <span className="pa26-micro font-semibold text-pa-muted">Единица</span>
              <select
                value={draft.unit}
                onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value }))}
                className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
              >
                {["шт", "г", "кг", "мл", "л", "уп"].map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="block">
            <span className="pa26-micro font-semibold text-pa-muted">Категория</span>
            <select
              value={draft.category}
              onChange={(e) => setDraft((d) => ({ ...d, category: e.target.value }))}
              className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
            >
              {SHOPPING_CATEGORIES_V1.map((c) => (
                <option key={c.slug} value={c.slug}>
                  {c.emoji} {c.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </V2BottomSheet>
    </div>
  );
}

function ShoppingRowV2({
  item,
  busy,
  divider,
  onToggle,
}: {
  item: ShoppingListItem;
  busy: boolean;
  divider: boolean;
  onToggle: () => void;
}) {
  const qty = formatProductQuantity({
    quantity: item.quantity,
    unit: item.unit,
    amount: item.amount,
    name: item.name,
  });

  return (
    <li className={cn(divider && "border-t border-pa-border/70")}>
      <button
        type="button"
        onClick={onToggle}
        disabled={busy}
        className={cn(
          "flex w-full min-h-[52px] items-center gap-3 px-4 py-3 text-left transition",
          "hover:bg-sage-50/60 disabled:opacity-60 dark:hover:bg-pa-elevated/30",
        )}
      >
        <span
          aria-hidden
          className={cn(
            "flex size-5 shrink-0 items-center justify-center rounded-full border-2 transition",
            item.checked
              ? "border-sage-500 bg-sage-500 text-white dark:border-sage-400 dark:bg-sage-400"
              : "border-pa-border bg-pa-surface",
          )}
        >
          {item.checked ? (
            <svg viewBox="0 0 12 12" className="size-3" fill="none">
              <path
                d="M2.5 6.5L5 9l4.5-5.5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : null}
        </span>
        <span
          className={cn(
            "pa26-body min-w-0 flex-1 truncate",
            item.checked && "text-pa-muted line-through",
          )}
        >
          {normalizeProductName(item.name)}
        </span>
        {qty ? (
          <span className="pa26-caption shrink-0 tabular-nums text-pa-muted">{qty}</span>
        ) : null}
      </button>
    </li>
  );
}

function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return one;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return few;
  }
  return many;
}
