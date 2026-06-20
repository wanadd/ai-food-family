"use client";

import { useEffect } from "react";

import { Sheet } from "@/components/ui/Sheet";
import { CategoryPicker } from "@/components/shopping/CategoryPicker";
import type { ShoppingCategory, ShoppingItemDraft } from "@/lib/shopping/types";
import { UNIT_OPTIONS } from "@/lib/shopping/units";

const INPUT_CLS =
  "mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2 text-sm text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200";

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
          <span className="text-xs font-semibold text-graphite-500">Название</span>
          <input
            id={nameInputId}
            value={draft.name}
            onChange={(event) =>
              onChange({ ...draft, name: event.target.value })
            }
            onBlur={(event) => onNameBlur?.(event.target.value)}
            required
            placeholder="Помидоры"
            className={INPUT_CLS}
          />
        </label>

        <CategoryPicker
          value={draft.category || "другое"}
          categories={categories}
          extraSlugs={categorySlugsFromItems}
          onChange={(slug) => onChange({ ...draft, category: slug })}
          allowCreate
          isFood={draft.is_food}
          onIsFoodChange={(is_food) => onChange({ ...draft, is_food })}
        />

        <div className="grid grid-cols-2 gap-2">
          <label className="block">
            <span className="text-xs font-semibold text-graphite-500">
              Количество
            </span>
            <input
              value={draft.quantity}
              onChange={(event) =>
                onChange({ ...draft, quantity: event.target.value })
              }
              className={INPUT_CLS}
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold text-graphite-500">Единица</span>
            <select
              value={draft.unit}
              onChange={(event) =>
                onChange({ ...draft, unit: event.target.value })
              }
              className={INPUT_CLS}
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
          <span className="text-xs font-semibold text-graphite-500">
            Комментарий (необязательно)
          </span>
          <input
            value={draft.note}
            onChange={(event) =>
              onChange({ ...draft, note: event.target.value })
            }
            className={INPUT_CLS}
          />
        </label>

        {successMessage ? (
          <p className="rounded-control bg-sage-50 px-3 py-2 text-center text-sm font-semibold text-sage-700">
            {successMessage}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={loading || !draft.name.trim()}
          className="pa-btn-primary w-full disabled:opacity-50"
        >
          {loading ? "Сохранение…" : "Сохранить"}
        </button>
      </form>
    </Sheet>
  );
}
