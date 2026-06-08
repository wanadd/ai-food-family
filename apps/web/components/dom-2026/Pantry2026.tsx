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
import { splitPantryBuckets } from "@/lib/dom/pantry-sections";
import { categoryMeta } from "@/lib/shopping/labels";
import { fetchShoppingCategories } from "@/lib/shopping/api";
import type { ShoppingCategory } from "@/lib/shopping/types";
import { formatProductQuantity } from "@/lib/planam/formatProductQuantity";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import { cn } from "@/lib/planam/cn";
import {
  deletePantryItem,
  fetchPantry,
} from "@/lib/pantry/api";
import type { PantryItem } from "@/lib/pantry/types";

export function Pantry2026() {
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

  const buckets = useMemo(() => splitPantryBuckets(items), [items]);

  async function handleDelete(item: PantryItem) {
    if (!initData) {
      return;
    }
    if (!window.confirm(`Удалить «${item.name}» из запасов?`)) {
      return;
    }
    try {
      await deletePantryItem(initData, mode, item.id);
      invalidateCache("pantry");
      invalidateCache("menu-overview");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить");
    }
  }

  if (!initData) {
    return (
      <div className="px-4 py-8">
        <EmptyState2026
          icon={<span aria-hidden>🫙</span>}
          title="Запасы дома"
          description="Откройте ПланАм в Telegram — здесь появятся продукты из списка покупок и остатки."
          actionLabel="К покупкам"
          onAction={() => router.push("/home/shopping")}
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
    <div className="pb-6 px-4 pt-4">
      {activeCount > 0 ? (
        <p className="pa26-caption mb-4 text-pa-muted">
          {activeCount}{" "}
          {activeCount === 1 ? "продукт" : activeCount < 5 ? "продукта" : "продуктов"}{" "}
          в запасах
        </p>
      ) : null}

      {error ? (
        <p className="mb-3 rounded-card border border-pa-error/30 bg-pa-error/5 px-3 py-2 pa26-caption text-pa-error">
          {error}
        </p>
      ) : null}

      {items.length === 0 ? (
        <EmptyState2026
          icon={<span aria-hidden>📦</span>}
          title="Запасов пока нет"
          description="Отметьте продукты купленными в списке покупок — они появятся здесь автоматически."
          actionLabel="К покупкам"
          onAction={() => router.push("/home/shopping")}
        />
      ) : (
        <div className="space-y-6">
          <PantryBlock
            title="Скоро заканчивается"
            hint="Используйте в ближайшие дни"
            items={buckets.expiringSoon}
            categories={categories}
            onDelete={(item) => void handleDelete(item)}
            urgent
          />
          <PantryBlock
            title="Избыток"
            hint="Много осталось — можно сократить покупки"
            items={buckets.excess}
            categories={categories}
            onDelete={(item) => void handleDelete(item)}
          />
          <PantryBlock
            title="В запасах"
            items={buckets.current}
            categories={categories}
            onDelete={(item) => void handleDelete(item)}
          />
          {buckets.current.length === 0 &&
          buckets.expiringSoon.length === 0 &&
          buckets.excess.length === 0 ? (
            <EmptyState2026
              title="Все позиции просрочены"
              description="Удалите устаревшие продукты или обновите срок годности."
              actionLabel="К покупкам"
              onAction={() => router.push("/home/shopping")}
            />
          ) : null}
        </div>
      )}

      <div className="mt-6 space-y-3">
        <Button2026
          variant="secondary"
          size="wide"
          onClick={() => router.push(PLANAM_ROUTES.homeLeftovers)}
        >
          Подобрать из запасов
        </Button2026>
        <p className="text-center">
          <button
            type="button"
            onClick={() => router.push("/home/shopping")}
            className="pa26-caption font-semibold text-sage-700 dark:text-sage-300"
          >
            ← Список покупок
          </button>
        </p>
      </div>
    </div>
  );
}

function PantryBlock({
  title,
  hint,
  items,
  categories,
  onDelete,
  urgent = false,
}: {
  title: string;
  hint?: string;
  items: PantryItem[];
  categories: ShoppingCategory[];
  onDelete: (item: PantryItem) => void;
  urgent?: boolean;
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section>
      <h2
        className={cn(
          "pa26-section-title",
          urgent && "text-warm dark:text-warm",
        )}
      >
        {title}
      </h2>
      {hint ? <p className="pa26-caption mt-0.5 text-pa-muted">{hint}</p> : null}
      <ul className="mt-2 space-y-2">
        {items.map((item) => {
          const meta = categoryMeta(item.category, categories);
          return (
            <li
              key={item.id}
              className="flex items-center justify-between gap-3 rounded-card border border-pa-border bg-pa-surface px-4 py-3 shadow-soft dark:shadow-none"
            >
              <div className="min-w-0">
                <p className="pa26-card-title truncate">{item.name}</p>
                <p className="pa26-caption text-pa-muted">
                  {formatProductQuantity({
                    quantity: item.quantity,
                    unit: item.unit,
                    name: item.name,
                  })}
                  {item.expires_at
                    ? ` · ${item.days_until_expiry} дн.`
                    : ""}
                </p>
                <p className="pa26-micro text-pa-muted">
                  {meta.emoji} {meta.label}
                </p>
              </div>
              <Button2026 variant="ghost" onClick={() => onDelete(item)}>
                Удалить
              </Button2026>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
