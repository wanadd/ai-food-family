"use client";

/**
 * PLANAM V2 — Запасы (/home/pantry).
 * Поиск, фильтры, чистые rows «название · срок/количество»,
 * bottom sheet действий по продукту, CTA «Из того, что есть дома».
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { HomeDomainSegmentV2 } from "@/components/planam-v2/home-domain/HomeDomainSegmentV2";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
  V2EmptyState,
} from "@/components/planam-v2/ui/V2Primitives";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { isExcessPantryItem } from "@/lib/dom/pantry-sections";
import { cn } from "@/lib/planam/cn";
import {
  detectProductCategory,
  formatProductQuantity,
  normalizeProductName,
} from "@/lib/planam/productTaxonomy";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import {
  addPantryItem,
  deletePantryItem,
  fetchPantry,
} from "@/lib/pantry/api";
import type { PantryItem, PantryItemDraft } from "@/lib/pantry/types";
import { EMPTY_PANTRY_DRAFT } from "@/lib/pantry/types";
import { fetchShoppingCategories } from "@/lib/shopping/api";
import { categoryMeta } from "@/lib/shopping/labels";
import type { ShoppingCategory } from "@/lib/shopping/types";

type PantryV2Filter = "all" | "expiring" | "excess" | "expired";

const FILTERS: { id: PantryV2Filter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "expiring", label: "Скоро заканчивается" },
  { id: "excess", label: "Много" },
  { id: "expired", label: "Просрочено" },
];

export function PantryV2() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const cacheK = cacheKey.pantry(mode);

  const [items, setItems] = useState<PantryItem[]>(
    () => getCached<{ items: PantryItem[] }>(cacheK)?.items ?? [],
  );
  const [loading, setLoading] = useState(items.length === 0);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<ShoppingCategory[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<PantryV2Filter>("all");
  const [selected, setSelected] = useState<PantryItem | null>(null);
  const [busy, setBusy] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [draft, setDraft] = useState<PantryItemDraft>(EMPTY_PANTRY_DRAFT);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const [data, cats] = await Promise.all([
        fetchPantry(initData, mode),
        fetchShoppingCategories(initData, mode).catch(() => []),
      ]);
      setCached(cacheK, { items: data.items, active_count: data.active_count });
      setItems(data.items);
      setCategories(cats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить запасы");
    } finally {
      setLoading(false);
    }
  }, [initData, mode, cacheK]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter((item) => {
      if (q && !item.name.toLowerCase().includes(q)) {
        return false;
      }
      switch (filter) {
        case "expiring":
          return (
            !item.is_expired &&
            item.expires_at != null &&
            item.days_until_expiry <= 3
          );
        case "excess":
          return !item.is_expired && isExcessPantryItem(item);
        case "expired":
          return item.is_expired;
        default:
          return !item.is_expired;
      }
    });
  }, [items, search, filter]);

  async function handleDelete(item: PantryItem) {
    if (!initData) {
      return;
    }
    setBusy(true);
    try {
      await deletePantryItem(initData, mode, item.id);
      invalidateCache("pantry");
      invalidateCache("menu-overview");
      setSelected(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить");
    } finally {
      setBusy(false);
    }
  }

  async function handleAdd() {
    if (!initData || !draft.name.trim()) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await addPantryItem(initData, mode, {
        ...draft,
        category: detectProductCategory(draft.name, draft.category),
      });
      invalidateCache("pantry");
      invalidateCache("menu-overview");
      setAddOpen(false);
      setDraft(EMPTY_PANTRY_DRAFT);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось добавить продукт");
    } finally {
      setBusy(false);
    }
  }

  if (!initData) {
    return (
      <div className="px-4 py-8">
        <V2EmptyState
          icon={<span aria-hidden>🫙</span>}
          title="Запасы дома"
          description="Откройте ПланАм в Telegram — здесь появятся продукты из списка покупок и остатки."
          actionLabel="К покупкам"
          onAction={() => router.push(PLANAM_ROUTES.shopping)}
        />
      </div>
    );
  }

  if (loading && items.length === 0) {
    return (
      <div className="space-y-3 px-4 pb-6 pt-4">
        <Skeleton2026 variant="rect" className="h-20 rounded-card" />
        <Skeleton2026 variant="rect" className="h-20 rounded-card" />
      </div>
    );
  }

  const activeCount = items.filter((i) => !i.is_expired).length;

  return (
    <div className="pb-6">
      <div className="px-4 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <h1 className="pa26-page-title">Запасы</h1>
        <p className="pa26-micro mt-0.5 text-pa-muted">
          {activeCount > 0
            ? `${activeCount} ${plural(activeCount, "продукт", "продукта", "продуктов")} дома`
            : "Продукты, которые уже есть дома"}
        </p>

        <HomeDomainSegmentV2 active="pantry" className="mt-3" />

        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск продукта"
          className="mt-3 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
        />

        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {FILTERS.map((f) => (
            <V2Chip
              key={f.id}
              label={f.label}
              active={filter === f.id}
              onClick={() => setFilter(f.id)}
            />
          ))}
        </div>
      </div>

      <div className="px-4 pt-3">
        {error ? (
          <p className="mb-3 rounded-card border border-pa-error/30 bg-pa-error/5 px-3 py-2 pa26-caption text-pa-error">
            {error}
          </p>
        ) : null}

        {items.length === 0 ? (
          <V2EmptyState
            icon={<span aria-hidden>📦</span>}
            title="Запасы пока пустые"
            description="Добавьте продукты — и PLANAM будет учитывать их в меню."
            actionLabel="Добавить продукт"
            onAction={() => setAddOpen(true)}
          />
        ) : filtered.length === 0 ? (
          <V2EmptyState
            title="Ничего не нашли"
            description="Попробуйте другой запрос или фильтр."
            actionLabel="Показать все"
            onAction={() => {
              setSearch("");
              setFilter("all");
            }}
          />
        ) : (
          <ul className="overflow-hidden rounded-card border border-pa-border bg-pa-surface">
            {filtered.map((item, idx) => (
              <PantryRowV2
                key={item.id}
                item={item}
                divider={idx > 0}
                onClick={() => setSelected(item)}
              />
            ))}
          </ul>
        )}

        <div className="mt-5 space-y-2">
          <V2Button variant="primary" size="wide" onClick={() => setAddOpen(true)}>
            Добавить продукт
          </V2Button>
          <V2Button
            variant="secondary"
            size="wide"
            onClick={() => router.push(PLANAM_ROUTES.homeLeftovers)}
          >
            Приготовить из того, что есть
          </V2Button>
        </div>
      </div>

      <V2BottomSheet
        open={selected != null}
        title={selected ? normalizeProductName(selected.name) : ""}
        onClose={() => setSelected(null)}
      >
        {selected ? (
          <div className="space-y-3 pb-2">
            <div className="rounded-card border border-pa-border bg-pa-surface px-4 py-3">
              <InfoRow
                label="Количество"
                value={
                  formatProductQuantity({
                    quantity: selected.quantity,
                    unit: selected.unit,
                    name: selected.name,
                  }) || "—"
                }
              />
              <InfoRow
                label="Срок"
                value={
                  selected.expires_at
                    ? selected.is_expired
                      ? "Просрочено"
                      : `${selected.days_until_expiry} дн.`
                    : "Не указан"
                }
              />
              <InfoRow
                label="Категория"
                value={
                  categoryMeta(
                    detectProductCategory(selected.name, selected.category),
                    categories,
                  ).label
                }
              />
            </div>
            <V2Button
              variant="secondary"
              size="wide"
              onClick={() => {
                setSelected(null);
                router.push(PLANAM_ROUTES.homeLeftovers);
              }}
            >
              Найти рецепт
            </V2Button>
            <V2Button
              variant="danger"
              size="wide"
              loading={busy}
              onClick={() => void handleDelete(selected)}
            >
              Удалить из запасов
            </V2Button>
          </div>
        ) : null}
      </V2BottomSheet>

      <V2BottomSheet
        open={addOpen}
        title="Добавить продукт"
        onClose={() => setAddOpen(false)}
        footer={
          <V2Button
            variant="primary"
            size="wide"
            loading={busy}
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
              onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
              placeholder="Например: творог"
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
            <span className="pa26-micro font-semibold text-pa-muted">
              Срок годности (необязательно)
            </span>
            <input
              type="date"
              value={draft.expires_at}
              onChange={(e) => setDraft((d) => ({ ...d, expires_at: e.target.value }))}
              className="mt-1 w-full rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
            />
          </label>
        </div>
      </V2BottomSheet>
    </div>
  );
}

function PantryRowV2({
  item,
  divider,
  onClick,
}: {
  item: PantryItem;
  divider: boolean;
  onClick: () => void;
}) {
  const qty = formatProductQuantity({
    quantity: item.quantity,
    unit: item.unit,
    name: item.name,
  });
  const trailing = item.expires_at
    ? item.is_expired
      ? "Просрочено"
      : `${item.days_until_expiry} дн.`
    : qty;

  return (
    <li className={cn(divider && "border-t border-pa-border/70")}>
      <button
        type="button"
        onClick={onClick}
        className="flex w-full min-h-[52px] items-center gap-3 px-4 py-3 text-left transition hover:bg-sage-50/60 dark:hover:bg-pa-elevated/30"
      >
        <span className="pa26-body min-w-0 flex-1 truncate">
          {normalizeProductName(item.name)}
        </span>
        <span
          className={cn(
            "pa26-caption shrink-0 tabular-nums",
            item.is_expired ? "font-semibold text-pa-error" : "text-pa-muted",
          )}
        >
          {trailing}
        </span>
      </button>
    </li>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1">
      <span className="pa26-micro text-pa-muted">{label}</span>
      <span className="pa26-caption font-medium text-pa-foreground">{value}</span>
    </div>
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
