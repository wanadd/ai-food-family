"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ModeBanner } from "@/components/app-mode/ModeBanner";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { PantryItemCard } from "@/components/pantry/PantryItemCard";
import { PantryItemForm } from "@/components/pantry/PantryItemForm";
import {
  addPantryItem,
  deletePantryItem,
  fetchPantry,
  updatePantryItem,
} from "@/lib/pantry/api";
import { defaultExpiryDate } from "@/lib/pantry/labels";
import {
  EMPTY_PANTRY_DRAFT,
  type PantryItem,
  type PantryItemDraft,
} from "@/lib/pantry/types";
import { getTelegramInitData } from "@/lib/telegram-webapp";

export function PantryDashboard() {
  const { mode } = useAppMode();
  const [initData, setInitData] = useState("");
  const [items, setItems] = useState<PantryItem[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<PantryItem | null>(null);
  const [draft, setDraft] = useState<PantryItemDraft>({
    ...EMPTY_PANTRY_DRAFT,
    expires_at: defaultExpiryDate(),
  });

  const loadPantry = useCallback(async (telegramInitData: string, appMode: typeof mode) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPantry(telegramInitData, appMode);
      setItems(data.items);
      setActiveCount(data.active_count);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить остатки",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const data = getTelegramInitData();
    setInitData(data);
    if (data) {
      loadPantry(data, mode);
    } else {
      setLoading(false);
    }
  }, [loadPantry, mode]);

  const { activeItems, expiredItems } = useMemo(() => {
    const active = items.filter((item) => !item.is_expired);
    const expired = items.filter((item) => item.is_expired);
    return { activeItems: active, expiredItems: expired };
  }, [items]);

  function resetDraft() {
    setDraft({ ...EMPTY_PANTRY_DRAFT, expires_at: defaultExpiryDate() });
  }

  async function handleAdd() {
    if (!initData) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await addPantryItem(initData, mode, {
        name: draft.name.trim(),
        quantity: draft.quantity.trim(),
        expires_at: draft.expires_at,
      });
      resetDraft();
      setShowForm(false);
      await loadPantry(initData, mode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось добавить");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate() {
    if (!initData || !editingItem) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updatePantryItem(initData, mode, editingItem.id, {
        name: draft.name.trim(),
        quantity: draft.quantity.trim(),
        expires_at: draft.expires_at,
      });
      setEditingItem(null);
      resetDraft();
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
    if (!window.confirm(`Удалить «${item.name}» из остатков?`)) {
      return;
    }
    setError(null);
    try {
      await deletePantryItem(initData, mode, item.id);
      await loadPantry(initData, mode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить");
    }
  }

  function startEdit(item: PantryItem) {
    setEditingItem(item);
    setShowForm(false);
    setDraft({
      name: item.name,
      quantity: item.quantity,
      expires_at: item.expires_at,
    });
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">
          Остатки доступны в Telegram Mini App после авторизации.
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
      <p className="py-20 text-center text-sm text-stone-500">Загрузка…</p>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-stone-100 bg-white px-5 py-6">
        <h1 className="text-2xl font-bold text-stone-900">Склад</h1>
        <p className="mt-1 text-sm text-stone-500">
          Учитывается при генерации AI меню
        </p>
        <Link
          href="/menu"
          className="mt-3 inline-flex text-xs font-semibold text-violet-700"
        >
          Сгенерировать меню →
        </Link>
      </header>

      <main className="mx-auto max-w-lg space-y-6 px-5 py-8">
        <ModeBanner />
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <section className="rounded-2xl border border-teal-200 bg-teal-50 p-5">
          <p className="text-xs font-bold uppercase tracking-wide text-teal-800">
            Для AI меню
          </p>
          <p className="mt-2 text-sm leading-relaxed text-teal-950">
            Активных остатков: <b>{activeCount}</b>. При генерации меню AI
            старается использовать их в блюдах и сократить список покупок.
            Сначала расходуются продукты с ближайшим сроком годности.
          </p>
        </section>

        {!showForm && !editingItem ? (
          <button
            type="button"
            onClick={() => {
              resetDraft();
              setShowForm(true);
            }}
            className="w-full rounded-xl bg-gradient-to-r from-teal-500 to-emerald-600 py-3.5 text-sm font-semibold text-white shadow-md"
          >
            + Добавить продукт
          </button>
        ) : null}

        {showForm ? (
          <PantryItemForm
            draft={draft}
            onChange={setDraft}
            submitLabel="Добавить"
            onSubmit={handleAdd}
            onCancel={() => {
              setShowForm(false);
              resetDraft();
            }}
            loading={saving}
          />
        ) : null}

        {editingItem ? (
          <PantryItemForm
            draft={draft}
            onChange={setDraft}
            submitLabel="Сохранить"
            onSubmit={handleUpdate}
            onCancel={() => {
              setEditingItem(null);
              resetDraft();
            }}
            loading={saving}
          />
        ) : null}

        {activeItems.length > 0 ? (
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">
              В наличии
            </h2>
            {activeItems.map((item) => (
              <PantryItemCard
                key={item.id}
                item={item}
                onEdit={() => startEdit(item)}
                onDelete={() => handleDelete(item)}
              />
            ))}
          </section>
        ) : (
          <p className="text-center text-sm text-stone-400">
            Добавьте продукты, которые есть дома
          </p>
        )}

        {expiredItems.length > 0 ? (
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-400">
              Просрочено ({expiredItems.length})
            </h2>
            {expiredItems.map((item) => (
              <PantryItemCard
                key={item.id}
                item={item}
                onEdit={() => startEdit(item)}
                onDelete={() => handleDelete(item)}
              />
            ))}
          </section>
        ) : null}
      </main>

      <BottomBackButton className="pb-4 pt-2" />
    </div>
  );
}
