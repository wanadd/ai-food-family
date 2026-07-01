"use client";

/**
 * PLANAM V2 — Список покупок (/shopping).
 * Простой чеклист: фильтры [Купить][Все][Куплено], нормализованные
 * категории (taxonomy guard), full-row toggle, один page scroll.
 */

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { AiProcessLoadingV2 } from "@/components/planam-v2/ai/AiProcessLoadingV2";
import { HomeDomainSegmentV2 } from "@/components/planam-v2/home-domain/HomeDomainSegmentV2";
import { useToast } from "@/components/ui/ToastProvider";
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
import { fetchPantry } from "@/lib/pantry/api";
import type { PantryItem } from "@/lib/pantry/types";
import { fetchRecipesFromPantry } from "@/lib/recipes/api";
import type { FromPantryRecipe } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";
import {
  formatProductQuantity,
  normalizeProductName,
  detectProductCategory,
} from "@/lib/planam/productTaxonomy";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import {
  createShoppingItem,
  deleteShoppingItem,
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
import {
  computeShoppingFlowStatus,
  isBoughtToday,
} from "@/lib/shopping/shopping-flow-summary";

type ShoppingFilter = "to-buy" | "all" | "bought" | "from-menu";

const FILTERS: { id: ShoppingFilter; label: string }[] = [
  { id: "to-buy", label: "Купить" },
  { id: "all", label: "Все" },
  { id: "bought", label: "Куплено" },
  { id: "from-menu", label: "Из меню" },
];

export function ShoppingV2() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const { showToast } = useToast();
  const cacheK = cacheKey.shoppingList(mode);

  const [list, setList] = useState<ShoppingList | null>(() =>
    initData ? getCached<ShoppingList>(cacheK) : null,
  );
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [fromPantryRecipes, setFromPantryRecipes] = useState<FromPantryRecipe[]>(
    [],
  );
  const [boughtTodayOpen, setBoughtTodayOpen] = useState(false);
  const [menuLinkedOpen, setMenuLinkedOpen] = useState(false);
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
      const [data, extraCats, pantryData, fromPantry] = await Promise.all([
        fetchShoppingList(initData, mode),
        fetchShoppingCategories(initData, mode).catch(() => []),
        fetchPantry(initData, mode).catch(() => null),
        fetchRecipesFromPantry(initData, mode).catch(() => ({ items: [] })),
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
      setPantryItems(pantryData?.items ?? []);
      setFromPantryRecipes(fromPantry.items ?? []);
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
      if (filter === "from-menu") {
        return item.source === "menu" || item.source === "recipe";
      }
      return true;
    });
  }, [list, filter]);

  const listForMain = useMemo(() => {
    if (filter === "from-menu") {
      return filtered;
    }
    return filtered.filter(
      (item) => item.source !== "menu" && item.source !== "recipe",
    );
  }, [filtered, filter]);

  const groups = useMemo(
    () => groupShoppingItems(listForMain, list?.categories ?? []),
    [listForMain, list?.categories],
  );

  const uncheckedCount = list ? list.total_count - list.checked_count : 0;
  const percent =
    list && list.total_count > 0
      ? Math.round((list.checked_count / list.total_count) * 100)
      : 0;
  const flowStatus = useMemo(
    () => computeShoppingFlowStatus(list, pantryItems, fromPantryRecipes),
    [list, pantryItems, fromPantryRecipes],
  );

  const boughtToday = useMemo(
    () => list?.items.filter((i) => i.checked && isBoughtToday(i.checked_at)) ?? [],
    [list],
  );

  const menuLinkedGroups = useMemo(() => {
    if (!list) {
      return [];
    }
    const menuItems = list.items.filter(
      (i) => !i.checked && (i.source === "menu" || i.source === "recipe"),
    );
    return groupShoppingItems(menuItems, list.categories ?? []);
  }, [list]);

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
      const updated = data.items.find((i) => i.id === item.id);
      if (nextChecked) {
        if (updated?.added_to_pantry) {
          showToast("Куплено · добавлено в запасы");
        } else {
          showToast("Куплено");
        }
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

  async function handleDelete(item: ShoppingListItem) {
    if (!initData) {
      return;
    }
    setTogglingId(item.id);
    setError(null);
    try {
      const data = await deleteShoppingItem(initData, mode, item.id);
      setCached(cacheK, data);
      setList(data);
      invalidateCache("menu-overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить продукт");
    } finally {
      setTogglingId(null);
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
  const hasMenuContext = Boolean(list?.menu_title);
  const firstRun = searchParams.get("firstRun") === "1";
  const allBought = Boolean(list && list.total_count > 0 && uncheckedCount === 0);
  const noResults = list && list.total_count > 0 && listForMain.length === 0;

  return (
    <div className="pb-6">
      <div className="px-4 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <h1 className="pa26-page-title">Покупки</h1>

        <div
          className="mt-2 space-y-1 rounded-card border border-pa-border bg-pa-surface px-3 py-2.5"
          data-testid="shopping-status-strip"
        >
          <p className="pa26-caption text-pa-foreground">
            {flowStatus.toBuy > 0
              ? `${flowStatus.toBuy} ${plural(flowStatus.toBuy, "товар", "товара", "товаров")} к покупке`
              : list && list.total_count > 0
                ? "Всё куплено"
                : "Список пуст"}
          </p>
          {flowStatus.atHome > 0 ? (
            <p className="pa26-micro text-pa-muted">
              {flowStatus.atHome} уже есть дома
            </p>
          ) : null}
          {flowStatus.dishesCovered > 0 ? (
            <p className="pa26-micro text-pa-muted">
              {flowStatus.dishesCovered}{" "}
              {plural(flowStatus.dishesCovered, "блюдо", "блюда", "блюд")} покрыты
              запасами
            </p>
          ) : null}
        </div>

        <div data-testid="shopping-go-pantry">
          <HomeDomainSegmentV2 active="shopping" className="mt-3" />
        </div>

        {list && list.total_count > 0 ? (
          <V2ProgressBar percent={percent} className="mt-3" />
        ) : null}

        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {FILTERS.map((f) => (
            <V2Chip
              key={f.id}
              label={f.label}
              active={filter === f.id}
              data-testid={`shopping-filter-${f.id}`}
              onClick={() => setFilter(f.id)}
            />
          ))}
        </div>

        <div className="mt-3" aria-label="Действия списка покупок">
          <V2Button
            variant="primary"
            className="w-full"
            data-testid="shopping-add-open-top"
            onClick={() => setAddOpen(true)}
          >
            Добавить товар
          </V2Button>
        </div>
      </div>

      <div className="px-4 pt-3">
        {error ? (
          <p className="mb-3 rounded-card border border-pa-error/30 bg-pa-error/5 px-3 py-2 pa26-caption text-pa-error">
            {error}
          </p>
        ) : null}

        {flowStatus.menuLinkedItems > 0 ? (
          <section className="mb-4" data-testid="shopping-menu-linked">
            <button
              type="button"
              onClick={() => setMenuLinkedOpen((v) => !v)}
              className="flex w-full items-center justify-between rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left"
            >
              <div>
                <h2 className="pa26-caption font-semibold">Связано с меню</h2>
                <p className="pa26-micro mt-0.5 text-pa-muted">
                  {flowStatus.menuTitle
                    ? flowStatus.menuTitle
                    : `${flowStatus.menuLinkedItems} ${plural(flowStatus.menuLinkedItems, "товар", "товара", "товаров")}`}
                </p>
              </div>
              <span className="pa26-micro text-pa-muted">
                {menuLinkedOpen ? "Свернуть" : "Показать блюда"}
              </span>
            </button>
            {menuLinkedOpen ? (
              <div className="mt-2 space-y-3">
                {menuLinkedGroups.map((group) => (
                  <div key={`menu-${group.category}`}>
                    <h3 className="pa26-micro font-semibold text-pa-muted">
                      {group.emoji} {group.label}
                    </h3>
                    <ul className="mt-1 overflow-hidden rounded-card border border-pa-border/70 bg-pa-surface/80">
                      {group.items.map((item, idx) => (
                        <li
                          key={item.id}
                          className={cn(
                            "flex items-center justify-between gap-2 px-3 py-2 pa26-caption",
                            idx > 0 && "border-t border-pa-border/50",
                          )}
                        >
                          <span className="truncate">{normalizeProductName(item.name)}</span>
                          <span className="shrink-0 text-pa-muted">
                            {formatProductQuantity({
                              quantity: item.quantity,
                              unit: item.unit,
                              amount: item.amount,
                              name: item.name,
                            })}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        ) : null}

        {emptyList ? (
          hasMenuContext ? (
            <ShoppingEmptyPanel
              icon="🛒"
              title="Список пока пуст"
              description="Можно добавить продукты вручную или пересобрать меню."
              primaryLabel="Добавить продукт"
              onPrimary={() => setAddOpen(true)}
              secondaryLabel={syncing ? "Обновляем..." : "Обновить из меню"}
              onSecondary={() => void handleSync()}
            />
          ) : (
            <ShoppingEmptyPanel
              icon="🛒"
              title="Покупок пока нет"
              description="Сначала соберите меню — PLANAM сам добавит продукты в список."
              primaryLabel="Собрать меню"
              onPrimary={() => router.push(PLANAM_ROUTES.planGenerate)}
            />
          )
        ) : firstRun && flowStatus.menuLinkedItems > 0 ? (
          <ShoppingEmptyPanel
            icon="🛒"
            title="Покупки готовы"
            description="Мы собрали продукты для меню на выбранный период."
            primaryLabel="Начать покупки"
            onPrimary={() => setMenuLinkedOpen(true)}
            secondaryLabel="Открыть меню"
            onSecondary={() => router.push(PLANAM_ROUTES.planToday)}
          />
        ) : noResults ? (
          allBought && filter === "to-buy" ? (
            <ShoppingEmptyPanel
              title="Всё куплено"
              description="Отлично, список на это меню закрыт."
              primaryLabel="Открыть меню"
              onPrimary={() => router.push(PLANAM_ROUTES.planToday)}
            />
          ) : (
            <V2EmptyState
              title={filter === "bought" ? "Куплено пока ничего" : "Ничего не найдено"}
              description={
                filter === "bought"
                  ? "Отмечайте товары — они появятся здесь."
                  : "Попробуйте другой фильтр или покажите весь список."
              }
              actionLabel="Показать все"
              onAction={() => setFilter("all")}
            />
          )
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
                      onDelete={() => void handleDelete(item)}
                    />
                  ))}
                </ul>
              </section>
            ))}
          </div>
        )}

        {boughtToday.length > 0 ? (
          <section className="mt-5" data-testid="shopping-bought-today">
            <button
              type="button"
              onClick={() => setBoughtTodayOpen((v) => !v)}
              className="flex w-full items-center justify-between rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left"
            >
              <span className="pa26-caption font-semibold">
                Куплено сегодня · {boughtToday.length}
              </span>
              <span className="pa26-micro text-pa-muted">
                {boughtTodayOpen ? "Свернуть" : "Показать"}
              </span>
            </button>
            {boughtTodayOpen ? (
              <ul className="mt-2 overflow-hidden rounded-card border border-pa-border bg-pa-surface">
                {boughtToday.map((item, idx) => (
                  <li
                    key={item.id}
                    className={cn(
                      "flex items-center justify-between gap-2 px-4 py-2.5 pa26-caption text-pa-muted",
                      idx > 0 && "border-t border-pa-border/70",
                    )}
                  >
                    <span className="truncate line-through">
                      {normalizeProductName(item.name)}
                    </span>
                    {item.added_to_pantry ? (
                      <span className="shrink-0 pa26-micro text-sage-700 dark:text-sage-300">
                        в запасах
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}

        {!emptyList ? (
        <div className="sticky bottom-[calc(4.5rem+env(safe-area-inset-bottom))] z-10 mt-5 border-t border-pa-border bg-pa-background/95 px-0 py-3 backdrop-blur-sm">
          <V2Button
            variant="primary"
            size="wide"
            loading={syncing}
            data-testid="shopping-sync-from-menu-sticky"
            onClick={() => void handleSync()}
          >
            Обновить из меню
          </V2Button>
        </div>
        ) : null}
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
            data-testid="shopping-add-submit"
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
              data-testid="shopping-add-input"
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

function ShoppingEmptyPanel({
  icon,
  title,
  description,
  primaryLabel,
  onPrimary,
  secondaryLabel,
  onSecondary,
}: {
  icon?: string;
  title: string;
  description: string;
  primaryLabel: string;
  onPrimary: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-10 text-center">
      {icon ? (
        <div className="flex size-14 items-center justify-center rounded-card bg-sage-50 text-2xl dark:bg-sage-700/20">
          <span aria-hidden>{icon}</span>
        </div>
      ) : null}
      <h3 className="pa26-section-title">{title}</h3>
      <p className="pa26-body max-w-[300px] text-pa-muted">{description}</p>
      <div className="mt-2 flex w-full max-w-xs flex-col gap-2">
        <V2Button variant="primary" size="wide" onClick={onPrimary}>
          {primaryLabel}
        </V2Button>
        {secondaryLabel && onSecondary ? (
          <V2Button variant="secondary" size="wide" onClick={onSecondary}>
            {secondaryLabel}
          </V2Button>
        ) : null}
      </div>
    </div>
  );
}

function ShoppingRowV2({
  item,
  busy,
  divider,
  onToggle,
  onDelete,
}: {
  item: ShoppingListItem;
  busy: boolean;
  divider: boolean;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const qty = formatProductQuantity({
    quantity: item.quantity,
    unit: item.unit,
    amount: item.amount,
    name: item.name,
  });

  return (
    <li className={cn(divider && "border-t border-pa-border/70")}>
      <div className="flex min-h-[52px] items-center gap-2 px-4 py-3">
        <button
          type="button"
          onClick={onToggle}
          disabled={busy}
          data-testid="shopping-item-toggle"
          className={cn(
            "flex min-w-0 flex-1 items-center gap-3 text-left transition",
            "hover:opacity-90 disabled:opacity-60",
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
        <button
          type="button"
          onClick={onDelete}
          disabled={busy}
          data-testid="shopping-item-delete"
          className="shrink-0 rounded-pill border border-pa-border px-2.5 py-1.5 pa26-micro font-semibold text-pa-muted disabled:opacity-50"
        >
          Удалить
        </button>
      </div>
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
