"use client";

import { useMemo, useState } from "react";

import { Sheet } from "@/components/ui/Sheet";
import { categoryMeta } from "@/lib/shopping/labels";
import type { ShoppingCategory, ShoppingItemDraft } from "@/lib/shopping/types";
import { UNIT_OPTIONS } from "@/lib/shopping/units";

type ShoppingItemSheetProps = {
  open: boolean;
  title: string;
  draft: ShoppingItemDraft;
  categories: ShoppingCategory[];
  categorySlugsFromItems: string[];
  onChange: (draft: ShoppingItemDraft) => void;
  onClose: () => void;
  onSubmit: () => void;
  loading?: boolean;
};

export function ShoppingItemSheet({
  open,
  title,
  draft,
  categories,
  categorySlugsFromItems,
  onChange,
  onClose,
  onSubmit,
  loading = false,
}: ShoppingItemSheetProps) {
  const [categoryInput, setCategoryInput] = useState(draft.category);

  const knownSlugs = useMemo(() => {
    const set = new Set<string>();
    for (const cat of categories) {
      set.add(cat.slug);
    }
    for (const slug of categorySlugsFromItems) {
      set.add(slug);
    }
    return Array.from(set);
  }, [categories, categorySlugsFromItems]);

  const normalizedInput = categoryInput.trim().toLowerCase();
  const matchesKnown = knownSlugs.some(
    (slug) =>
      slug === normalizedInput ||
      categoryMeta(slug, categories).label.toLowerCase() ===
        normalizedInput,
  );
  const showCreateCategory =
    normalizedInput.length > 0 && !matchesKnown;

  return (
    <Sheet open={open} title={title} onClose={onClose}>
      <form
        className="space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          onChange({ ...draft, category: categoryInput.trim() || draft.category });
          onSubmit();
        }}
      >
        <label className="block">
          <span className="text-xs font-semibold text-stone-500">Название</span>
          <input
            value={draft.name}
            onChange={(event) =>
              onChange({ ...draft, name: event.target.value })
            }
            required
            placeholder="Помидоры"
            className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
          />
        </label>

        <label className="block">
          <span className="text-xs font-semibold text-stone-500">Категория</span>
          <input
            value={categoryInput}
            onChange={(event) => {
              setCategoryInput(event.target.value);
              onChange({ ...draft, category: event.target.value });
            }}
            list="shopping-categories"
            placeholder="Продукты"
            className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
          />
          <datalist id="shopping-categories">
            {knownSlugs.map((slug) => (
              <option
                key={slug}
                value={categoryMeta(slug, categories).label}
              />
            ))}
          </datalist>
        </label>

        {showCreateCategory ? (
          <div className="rounded-lg border border-emerald-100 bg-emerald-50/80 px-3 py-2">
            <p className="text-xs font-semibold text-emerald-800">
              Создать категорию: {categoryInput.trim()}
            </p>
            <label className="mt-2 flex items-center gap-2 text-xs text-stone-700">
              <input
                type="checkbox"
                checked={draft.is_food}
                onChange={(event) =>
                  onChange({ ...draft, is_food: event.target.checked })
                }
                className="h-4 w-4 rounded border-stone-300 text-emerald-600"
              />
              Это продукты? (попадут в запасы при покупке)
            </label>
          </div>
        ) : null}

        <div className="grid grid-cols-2 gap-2">
          <label className="block">
            <span className="text-xs font-semibold text-stone-500">
              Количество
            </span>
            <input
              value={draft.quantity}
              onChange={(event) =>
                onChange({ ...draft, quantity: event.target.value })
              }
              className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold text-stone-500">Единица</span>
            <select
              value={draft.unit}
              onChange={(event) =>
                onChange({ ...draft, unit: event.target.value })
              }
              className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
            >
              {UNIT_OPTIONS.map((unit) => (
                <option key={unit} value={unit}>
                  {unit}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block">
          <span className="text-xs font-semibold text-stone-500">
            Комментарий (необязательно)
          </span>
          <input
            value={draft.note}
            onChange={(event) =>
              onChange({ ...draft, note: event.target.value })
            }
            className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
          />
        </label>

        <button
          type="submit"
          disabled={loading || !draft.name.trim()}
          className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Сохранение…" : "Сохранить"}
        </button>
      </form>
    </Sheet>
  );
}
