"use client";

import type { ShoppingListItem } from "@/lib/shopping/types";

type ShoppingItemRowProps = {
  item: ShoppingListItem;
  toggling: boolean;
  onToggle: (checked: boolean) => void;
};

export function ShoppingItemRow({
  item,
  toggling,
  onToggle,
}: ShoppingItemRowProps) {
  return (
    <label
      className={`flex cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 transition ${
        item.checked
          ? "border-stone-200 bg-stone-50/80"
          : "border-stone-100 bg-white hover:border-emerald-200"
      } ${toggling ? "opacity-60" : ""}`}
    >
      <input
        type="checkbox"
        checked={item.checked}
        disabled={toggling}
        onChange={(event) => onToggle(event.target.checked)}
        className="mt-1 h-5 w-5 shrink-0 rounded border-stone-300 text-emerald-600 focus:ring-emerald-500"
      />
      <span className="min-w-0 flex-1">
        <span
          className={`block font-medium ${
            item.checked ? "text-stone-400 line-through" : "text-stone-900"
          }`}
        >
          {item.name}
        </span>
        <span
          className={`mt-0.5 block text-sm ${
            item.checked ? "text-stone-300" : "text-stone-500"
          }`}
        >
          {item.amount}
        </span>
        {item.checked && item.checked_by_name ? (
          <span className="mt-1 block text-xs text-emerald-700">
            Купил(а): {item.checked_by_name}
          </span>
        ) : null}
      </span>
    </label>
  );
}
