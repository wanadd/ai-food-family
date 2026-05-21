"use client";

import type { PantryItemDraft } from "@/lib/pantry/types";

type PantryItemFormProps = {
  draft: PantryItemDraft;
  onChange: (draft: PantryItemDraft) => void;
  onSubmit: () => void;
  onCancel?: () => void;
  submitLabel: string;
  loading?: boolean;
};

export function PantryItemForm({
  draft,
  onChange,
  onSubmit,
  onCancel,
  submitLabel,
  loading = false,
}: PantryItemFormProps) {
  return (
    <form
      className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label className="block">
        <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Продукт
        </span>
        <input
          value={draft.name}
          onChange={(event) =>
            onChange({ ...draft, name: event.target.value })
          }
          placeholder="Например: молоко"
          required
          className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
        />
      </label>

      <label className="block">
        <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Количество
        </span>
        <input
          value={draft.quantity}
          onChange={(event) =>
            onChange({ ...draft, quantity: event.target.value })
          }
          placeholder="500 мл, 2 шт, 300 г"
          required
          className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
        />
      </label>

      <label className="block">
        <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Срок годности
        </span>
        <input
          type="date"
          value={draft.expires_at}
          onChange={(event) =>
            onChange({ ...draft, expires_at: event.target.value })
          }
          required
          className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
        />
      </label>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={
            loading ||
            !draft.name.trim() ||
            !draft.quantity.trim() ||
            !draft.expires_at
          }
          className="flex-1 rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Сохранение…" : submitLabel}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-xl border border-stone-200 px-4 py-3 text-sm font-semibold text-stone-600"
          >
            Отмена
          </button>
        ) : null}
      </div>
    </form>
  );
}
