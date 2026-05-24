"use client";

import { Sheet } from "@/components/ui/Sheet";
import { CategoryPicker } from "@/components/shopping/CategoryPicker";
import type { ShoppingCategory } from "@/lib/shopping/types";
import { UNIT_OPTIONS } from "@/lib/shopping/units";
import type { PantryItemDraft } from "@/lib/pantry/types";

type PantryItemFormProps = {
  open: boolean;
  title: string;
  draft: PantryItemDraft;
  categories: ShoppingCategory[];
  onChange: (draft: PantryItemDraft) => void;
  onSubmit: () => void;
  onClose: () => void;
  loading?: boolean;
};

export function PantryItemForm({
  open,
  title,
  draft,
  categories,
  onChange,
  onSubmit,
  onClose,
  loading = false,
}: PantryItemFormProps) {
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
            value={draft.name}
            onChange={(event) =>
              onChange({ ...draft, name: event.target.value })
            }
            required
            placeholder="Творог"
            className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
          />
        </label>

        <CategoryPicker
          value={draft.category || "продукты"}
          categories={categories}
          onChange={(slug) => onChange({ ...draft, category: slug })}
          allowCreate
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
              required
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
            Срок годности (необязательно)
          </span>
          <input
            type="date"
            value={draft.expires_at}
            onChange={(event) =>
              onChange({ ...draft, expires_at: event.target.value })
            }
            className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
          />
        </label>

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
          disabled={loading || !draft.name.trim() || !draft.quantity.trim()}
          className="w-full rounded-xl bg-teal-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Сохранение…" : "Сохранить"}
        </button>
      </form>
    </Sheet>
  );
}
