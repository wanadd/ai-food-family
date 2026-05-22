"use client";

import {
  expiryLabel,
  formatAddedDate,
  sourceLabel,
} from "@/lib/pantry/labels";
import type { PantryItem } from "@/lib/pantry/types";

type PantryItemRowProps = {
  item: PantryItem;
  onEdit: () => void;
  onDelete: () => void;
};

export function PantryItemRow({ item, onEdit, onDelete }: PantryItemRowProps) {
  const qty =
    item.unit && !item.quantity.includes(item.unit)
      ? `${item.quantity} ${item.unit}`.trim()
      : item.quantity;

  return (
    <div
      className={`flex items-start gap-2 rounded-lg border px-3 py-2 ${
        item.is_expired
          ? "border-stone-100 bg-stone-50/80 opacity-75"
          : "border-stone-100 bg-white"
      }`}
    >
      <div className="min-w-0 flex-1">
        <p
          className={`text-sm font-medium ${
            item.is_expired ? "text-stone-400 line-through" : "text-stone-900"
          }`}
        >
          {item.name}
          {qty ? (
            <span className="text-stone-500"> — {qty}</span>
          ) : null}
        </p>
        <p className="mt-0.5 text-[11px] text-stone-400">
          {sourceLabel(item.source)} · {formatAddedDate(item.created_at)}
        </p>
        {item.expires_at && !item.is_expired ? (
          <p className="mt-0.5 text-[11px] text-amber-700">
            {expiryLabel(item.days_until_expiry, item.is_expired)}
          </p>
        ) : null}
        {item.is_expired ? (
          <p className="mt-0.5 text-[11px] text-red-600">
            {expiryLabel(item.days_until_expiry, true)}
          </p>
        ) : null}
      </div>
      <div className="flex shrink-0 gap-1">
        <button
          type="button"
          onClick={onEdit}
          className="rounded px-1.5 py-1 text-[11px] font-semibold text-stone-500 hover:bg-stone-100"
        >
          ✎
        </button>
        <button
          type="button"
          onClick={onDelete}
          className="rounded px-1.5 py-1 text-[11px] font-semibold text-red-600 hover:bg-red-50"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
