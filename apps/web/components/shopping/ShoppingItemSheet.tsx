"use client";

import { useEffect } from "react";

import { Sheet } from "@/components/ui/Sheet";
import { CategoryPicker } from "@/components/shopping/CategoryPicker";
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
  successMessage?: string | null;
  nameInputId?: string;
  onNameBlur?: (name: string) => void;
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
  successMessage = null,
  nameInputId = "shopping-item-name",
  onNameBlur,
}: ShoppingItemSheetProps) {
  useEffect(() => {
    if (open && !title.includes("Редакт")) {
      const t = window.setTimeout(
        () => document.getElementById(nameInputId)?.focus(),
        120,
      );
      return () => window.clearTimeout(t);
    }
  }, [open, title, nameInputId]);

  return (
    <Sheet open={open} title={title} onClose={onClose}>
      <form
        className="space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <label className="block">
          <span className="text-xs font-semibold text-stone-500">Название</span>
          <input
            id={nameInputId}
            value={draft.name}
            onChange={(event) =>
              onChange({ ...draft, name: event.target.value })
            }
            onBlur={(event) => onNameBlur?.(event.target.value)}
            required
            placeholder="Помидоры"
            className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
          />
        </label>

        <CategoryPicker
          value={draft.category || "продукты"}
          categories={categories}
          extraSlugs={categorySlugsFromItems}
          onChange={(slug) => onChange({ ...draft, category: slug })}
          allowCreate
          isFood={draft.is_food}
          onIsFoodChange={(is_food) => onChange({ ...draft, is_food })}
        />

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

        {successMessage ? (
          <p className="rounded-lg bg-emerald-50 px-3 py-2 text-center text-sm font-semibold text-emerald-800">
            {successMessage}
          </p>
        ) : null}

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
