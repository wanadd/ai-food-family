"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { suggestCategorySlug } from "@/lib/shopping/category-suggest";

import { BotQuickInputHint } from "@/components/bot/BotQuickInputHint";
import { ProtectedScreenFallback } from "@/components/auth/ProtectedScreenFallback";
import { useProtectedScreen } from "@/lib/use-protected-screen";
import { ModeBanner } from "@/components/app-mode/ModeBanner";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { PageLoading } from "@/components/ui/PageLoading";
import { PantryCategorySection } from "@/components/pantry/PantryCategorySection";
import { PantryItemForm } from "@/components/pantry/PantryItemForm";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import {
  addPantryItem,
  deletePantryItem,
  fetchPantry,
  updatePantryItem,
} from "@/lib/pantry/api";
import { fetchShoppingCategories } from "@/lib/shopping/api";
import type { ShoppingCategory } from "@/lib/shopping/types";
import { categoryMeta } from "@/lib/shopping/labels";
import {
  EMPTY_PANTRY_DRAFT,
  type PantryFilter,
  type PantryItem,
  type PantryItemDraft,
} from "@/lib/pantry/types";

const FILTERS: { id: PantryFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "low", label: "Скоро заканчивается" },
  { id: "recent", label: "Недавно добавлено" },
  { id: "shopping", label: "Из покупок" },
  { id: "manual", label: "Вручную" },
];

const RECENT_DAYS = 7;

export function PantryDashboard() {
  const { mode } = useAppMode();
  const { initData, state: authState } = useProtectedScreen();
  const cachedPantry = initData
    ? getCached<{ items: PantryItem[]; active_count: number }>(
        cacheKey.pantry(mode),
      )
    : null;
  const [items, setItems] = useState<PantryItem[]>(cachedPantry?.items ?? []);
  const [activeCount, setActiveCount] = useState(
    cachedPantry?.active_count ?? 0,
  );
  const [loading, setLoading] = useState(cachedPantry == null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<PantryFilter>("all");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<PantryItem | null>(null);
  const [draft, setDraft] = useState<PantryItemDraft>(EMPTY_PANTRY_DRAFT);
  const [categories, setCategories] = useState<ShoppingCategory[]>([]);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const loadPantry = useCallback(
    async (telegramInitData: string, appMode: typeof mode) => {
      const cached = getCached<{ items: PantryItem[]; active_count: number }>(
        cacheKey.pantry(appMode),
      );
      if (cached) {
        setItems(cached.items);
        setActiveCount(cached.active_count);
        setLoading(false);
      } else {
        setLoading(true);
      }
      setError(null);
      try {
        const [data, cats] = await Promise.all([
          fetchPantry(telegramInitData, appMode),
          fetchShoppingCategories(telegramInitData, appMode).catch(() => []),
        ]);
        setCached(cacheKey.pantry(appMode), {
          items: data.items,
          active_count: data.active_count,
        });
        setItems(data.items);
        setActiveCount(data.active_count);
        setCategories(cats);
        console.info("[PlanAm] Pantry loaded");
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Не удалось загрузить запасы",
        );
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (authState === "ready" && initData) {
      void loadPantry(initData, mode);
    }
  }, [initData, loadPantry, mode, authState]);

  const filteredItems = useMemo(() => {
    const now = Date.now();
    return items.filter((item) => {
      switch (filter) {
        case "low":
          return !item.is_expired && item.days_until_expiry <= 3;
        case "recent": {
          const created = new Date(item.created_at).getTime();
          const days = (now - created) / (1000 * 60 * 60 * 24);
          return days <= RECENT_DAYS;
        }
        case "shopping":
          return item.source === "shopping_list";
        case "manual":
          return item.source === "manual";
        default:
          return true;
      }
    });
  }, [items, filter]);

  const grouped = useMemo(() => {
    const buckets = new Map<string, PantryItem[]>();
    for (const item of filteredItems) {
      const cat = item.category || "продукты";
      const existing = buckets.get(cat) ?? [];
      existing.push(item);
      buckets.set(cat, existing);
    }
    return Array.from(buckets.entries()).sort(([a], [b]) =>
      categoryMeta(a, categories).label.localeCompare(
        categoryMeta(b, categories).label,
        "ru",
      ),
    );
  }, [filteredItems, categories]);

  function openAdd() {
    setEditingItem(null);
    setDraft({ ...EMPTY_PANTRY_DRAFT });
    setSaveSuccess(null);
    setFormOpen(true);
  }

  function openEdit(item: PantryItem) {
    setEditingItem(item);
    setDraft({
      name: item.name,
      category: item.category || "продукты",
      quantity: item.quantity,
      unit: item.unit || "шт",
      expires_at: item.expires_at ?? "",
      note: item.note ?? "",
    });
    setFormOpen(true);
  }

  async function handleSave() {
    if (!initData) {
      return;
    }
    setSaving(true);
    setError(null);
    setSaveSuccess(null);
    const name = draft.name.trim();
    const payload: PantryItemDraft = {
      ...draft,
      name,
      category: draft.category?.trim() || suggestCategorySlug(name) || "продукты",
      quantity: draft.quantity?.trim() || "1",
      unit: draft.unit?.trim() || "шт",
    };
    try {
      if (editingItem) {
        await updatePantryItem(initData, mode, editingItem.id, payload);
        setFormOpen(false);
        setEditingItem(null);
        setDraft({ ...EMPTY_PANTRY_DRAFT });
      } else {
        await addPantryItem(initData, mode, payload);
        setDraft((prev) => ({
          ...prev,
          name: "",
          category: payload.category,
          quantity: payload.quantity,
          unit: payload.unit,
        }));
        setSaveSuccess("✓ Добавлено в запасы");
        window.setTimeout(
          () => document.getElementById("pantry-item-name")?.focus(),
          80,
        );
      }
      invalidateCache("pantry");
      invalidateCache("shopping-list");
      await loadPantry(initData, mode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(item: PantryItem) {
    if (!initData) {
      return;
    }
    if (!window.confirm(`Удалить «${item.name}» из запасов?`)) {
      return;
    }
    setError(null);
    try {
      await deletePantryItem(initData, mode, item.id);
      invalidateCache("pantry");
      invalidateCache("shopping-list");
      await loadPantry(initData, mode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить");
    }
  }

  function toggleCategory(slug: string) {
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

  if (authState !== "ready") {
    return (
      <ProtectedScreenFallback
        loadingMessage="Загружаем запасы..."
        telegramMessage="Запасы доступны в Telegram Mini App после авторизации."
      />
    );
  }

  if (loading) {
    return <PageLoading message="Загружаем запасы..." />;
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="sticky top-0 z-10 border-b border-stone-100 bg-white/95 px-4 py-4 backdrop-blur-sm">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-stone-900">Запасы дома</h1>
            <p className="mt-0.5 text-xs text-stone-500">
              ПланАм учитывает их при составлении меню
            </p>
            <p className="mt-1 text-xs font-medium text-teal-700">
              {activeCount} {activeCount === 1 ? "товар" : "товаров"} в запасах
            </p>
          </div>
          <button
            type="button"
            onClick={openAdd}
            className="shrink-0 rounded-lg bg-teal-600 px-3 py-2 text-xs font-semibold text-white"
          >
            + Добавить
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-3 px-4 py-4">
        <BotQuickInputHint />
        <ModeBanner />

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <div className="flex gap-1.5 overflow-x-auto pb-1">
          {FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setFilter(item.id)}
              className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
                filter === item.id
                  ? "border-teal-200 bg-teal-50 text-teal-800"
                  : "border-stone-200 bg-white text-stone-600"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-teal-200 bg-teal-50/50 px-5 py-10 text-center">
            <p className="text-base font-semibold text-stone-800">
              Запасов пока нет
            </p>
            <p className="mt-2 text-sm leading-relaxed text-stone-600">
              Отмечайте продукты купленными — они появятся здесь автоматически
            </p>
            <Link
              href="/shopping"
              className="mt-4 inline-block text-sm font-semibold text-emerald-700"
            >
              Перейти к покупкам →
            </Link>
          </div>
        ) : null}

        {items.length > 0 && filteredItems.length === 0 ? (
          <p className="py-8 text-center text-sm text-stone-400">
            Нет товаров по выбранному фильтру
          </p>
        ) : null}

        <div className="space-y-2">
          {grouped.map(([category, categoryItems]) => (
            <PantryCategorySection
              key={category}
              category={category}
              categories={categories}
              items={categoryItems}
              expanded={expanded.has(category)}
              onToggleExpand={() => toggleCategory(category)}
              onEdit={openEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      </main>

      <PantryItemForm
        open={formOpen}
        title={editingItem ? "Редактировать" : "Добавить в запасы"}
        draft={draft}
        categories={categories}
        onChange={setDraft}
        onClose={() => {
          setFormOpen(false);
          setEditingItem(null);
          setSaveSuccess(null);
        }}
        onSubmit={handleSave}
        loading={saving}
        successMessage={saveSuccess}
        nameInputId="pantry-item-name"
      />
    </div>
  );
}
