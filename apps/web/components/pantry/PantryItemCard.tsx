"use client";

import { expiryLabel, expiryTone } from "@/lib/pantry/labels";
import type { PantryItem } from "@/lib/pantry/types";

const TONE_STYLES = {
  danger: "border-red-200 bg-red-50 text-red-800",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  ok: "border-emerald-200 bg-emerald-50 text-emerald-900",
};

type PantryItemCardProps = {
  item: PantryItem;
  onEdit: () => void;
  onDelete: () => void;
};

export function PantryItemCard({ item, onEdit, onDelete }: PantryItemCardProps) {
  const tone = expiryTone(item.days_until_expiry, item.is_expired);

  return (
    <article
      className={`rounded-2xl border p-4 ${
        item.is_expired
          ? "border-stone-200 bg-stone-50/90 opacity-80"
          : "border-stone-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3
            className={`font-semibold ${
              item.is_expired ? "text-stone-500 line-through" : "text-stone-900"
            }`}
          >
            {item.name}
          </h3>
          <p className="mt-1 text-sm text-stone-600">{item.quantity}</p>
          <span
            className={`mt-3 inline-block rounded-full border px-2.5 py-1 text-xs font-semibold ${TONE_STYLES[tone]}`}
          >
            {expiryLabel(item.days_until_expiry, item.is_expired)} · до{" "}
            {item.expires_at}
          </span>
          {item.added_by_name ? (
            <p className="mt-2 text-xs text-stone-400">
              Добавил(а): {item.added_by_name}
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col gap-2">
          <button
            type="button"
            onClick={onEdit}
            className="rounded-lg border border-stone-200 px-3 py-1.5 text-xs font-semibold text-stone-600 hover:bg-stone-50"
          >
            Изменить
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
          >
            Удалить
          </button>
        </div>
      </div>
    </article>
  );
}
