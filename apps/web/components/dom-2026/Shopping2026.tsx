"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import {
  groupShoppingItems,
  shoppingProgress,
} from "@/lib/dom/shopping-groups";
import { cn } from "@/lib/planam/cn";
import {
  fetchShoppingCategories,
  fetchShoppingList,
  syncShoppingList,
  toggleShoppingItem,
} from "@/lib/shopping/api";
import type { ShoppingList, ShoppingListItem } from "@/lib/shopping/types";

export function Shopping2026() {
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
  const [search, setSearch] = useState("");
  const [hideChecked, setHideChecked] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());

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
    const q = search.trim().toLowerCase();
    return list.items.filter((item) => {
      if (hideChecked && item.checked) {
        return false;
      }
      if (!q) {
        return true;
      }
      return item.name.toLowerCase().includes(q);
    });
  }, [list, search, hideChecked]);

  const groups = useMemo(
    () => groupShoppingItems(filtered, list?.categories ?? []),
    [filtered, list?.categories],
  );

  const progress = shoppingProgress(
    list?.total_count ?? 0,
    list?.checked_count ?? 0,
  );

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
    if (
      !nextChecked &&
      item.checked &&
      (item.added_to_pantry || item.linked_pantry_item_id)
    ) {
      const remove = window.confirm(
        "Товар уже в запасах. Убрать и оттуда?",
      );
      setTogglingId(item.id);
      try {
        const data = await toggleShoppingItem(initData, mode, item.id, false, {
          removeFromPantry: remove,
        });
        setCached(cacheK, data);
        setList(data);
        if (remove) {
          invalidateCache("pantry");
          invalidateCache("menu-overview");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Не удалось обновить");
      } finally {
        setTogglingId(null);
      }
      return;
    }

    setTogglingId(item.id);
    try {
      const data = await toggleShoppingItem(initData, mode, item.id, nextChecked);
      setCached(cacheK, data);
      setList(data);
      if (nextChecked) {
        invalidateCache("pantry");
        invalidateCache("menu-overview");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось обновить");
    } finally {
      setTogglingId(null);
    }
  }

  function toggleGroup(category: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }

  useEffect(() => {
    if (groups.length > 0) {
      setExpanded((prev) =>
        prev.size === 0 ? new Set(groups.map((g) => g.category)) : prev,
      );
    }
  }, [groups]);

  if (loading && !list) {
    return (
      <div className="space-y-3 px-4 pb-6 pt-4">
        <Skeleton2026 variant="rect" className="h-3 rounded-pill" />
        <Skeleton2026 variant="rect" className="h-24 rounded-card" />
        <Skeleton2026 variant="rect" className="h-24 rounded-card" />
      </div>
    );
  }

  if (!initData) {
    return (
      <div className="px-4 py-8">
        <EmptyState2026
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
      <div className="sticky top-0 z-20 border-b border-pa-border bg-pa-canvas/95 px-4 py-3 backdrop-blur-md">
        {list && list.total_count > 0 ? (
          <div className="mb-3">
            <div className="flex items-center justify-between gap-2">
              <p className="pa26-caption font-medium text-pa-foreground">
                {progress.label}
              </p>
              <span className="pa26-micro text-pa-muted">{progress.percent}%</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-pill bg-cream-deep dark:bg-graphite-700/40">
              <div
                className="h-full rounded-pill bg-sage-500 transition-all dark:bg-sage-400"
                style={{ width: `${progress.percent}%` }}
              />
            </div>
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <Button2026
            variant="secondary"
            className="flex-1 min-w-[120px]"
            onClick={() => void handleSync()}
            loading={syncing}
          >
            Из меню
          </Button2026>
          <button
            type="button"
            onClick={() => setHideChecked((v) => !v)}
            className={cn(
              "rounded-control border px-3 py-2 pa26-micro font-semibold",
              hideChecked
                ? "border-sage-400 bg-sage-50 text-sage-700 dark:bg-sage-700/30 dark:text-sage-300"
                : "border-pa-border bg-pa-surface text-pa-muted",
            )}
          >
            Скрыть купленное
          </button>
        </div>

        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Найти в списке…"
          className="mt-3 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
        />
      </div>

      <div className="px-4 pt-4">
        {error ? (
          <p className="mb-3 rounded-card border border-pa-error/30 bg-pa-error/5 px-3 py-2 pa26-caption text-pa-error">
            {error}
          </p>
        ) : null}

        {emptyList ? (
          <EmptyState2026
            icon={<span aria-hidden>🛒</span>}
            title="Список покупок пуст"
            description="Создайте меню — продукты появятся здесь. Или обновите список из плана."
            actionLabel="Обновить из меню"
            onAction={() => void handleSync()}
          />
        ) : null}

        {noResults && !emptyList ? (
          <EmptyState2026
            title="Ничего не найдено"
            description={
              hideChecked
                ? "Все позиции уже отмечены купленными."
                : "Попробуйте другой запрос."
            }
            actionLabel={hideChecked ? "Показать всё" : "Сбросить поиск"}
            onAction={() => {
              if (hideChecked) {
                setHideChecked(false);
              } else {
                setSearch("");
              }
            }}
          />
        ) : null}

        <div className="max-h-[70vh] space-y-2 overflow-y-auto overscroll-contain">
          {groups.map((group) => {
            const open = expanded.has(group.category);
            const unchecked = group.items.filter((i) => !i.checked).length;
            return (
              <section
                key={group.category}
                className="rounded-card border border-pa-border bg-pa-surface shadow-soft dark:shadow-none"
              >
                <button
                  type="button"
                  onClick={() => toggleGroup(group.category)}
                  className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
                >
                  <span className="pa26-card-title">
                    <span className="mr-1.5" aria-hidden>
                      {group.emoji}
                    </span>
                    {group.label}
                  </span>
                  <span className="pa26-caption text-pa-muted">
                    {unchecked}/{group.items.length}
                    <span className="ml-1">{open ? "▾" : "▸"}</span>
                  </span>
                </button>
                {open ? (
                  <ul className="divide-y divide-pa-border border-t border-pa-border">
                    {group.items.map((item) => (
                      <li key={item.id}>
                        <button
                          type="button"
                          disabled={togglingId === item.id}
                          onClick={() => void handleToggle(item)}
                          className={cn(
                            "flex w-full items-start gap-3 px-4 py-3 text-left transition",
                            item.checked && "opacity-60",
                          )}
                        >
                          <span
                            className={cn(
                              "mt-0.5 flex size-5 shrink-0 items-center justify-center rounded border text-xs",
                              item.checked
                                ? "border-sage-500 bg-sage-500 text-white dark:border-sage-400 dark:bg-sage-400"
                                : "border-pa-border bg-pa-canvas",
                            )}
                          >
                            {item.checked ? "✓" : ""}
                          </span>
                          <span className="min-w-0 flex-1">
                            <span
                              className={cn(
                                "pa26-body block",
                                item.checked && "line-through",
                              )}
                            >
                              {item.name}
                            </span>
                            {(item.quantity || item.unit) && (
                              <span className="pa26-caption text-pa-muted">
                                {[item.quantity, item.unit].filter(Boolean).join(" ")}
                              </span>
                            )}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </section>
            );
          })}
        </div>

        {!emptyList ? (
          <p className="mt-4 text-center">
            <button
              type="button"
              onClick={() => router.push("/home/pantry?returnTo=/home/shopping")}
              className="pa26-caption font-semibold text-sage-700 dark:text-sage-300"
            >
              Перейти к запасам →
            </button>
          </p>
        ) : null}
      </div>
    </div>
  );
}
