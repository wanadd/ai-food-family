"use client";

import { itemAmountLabel } from "@/lib/shopping/display";
import { sourceLabel } from "@/lib/shopping/labels";
import type { ShoppingListItem } from "@/lib/shopping/types";

type ShoppingItemRowProps = {
  item: ShoppingListItem;
  toggling: boolean;
  onToggle: (checked: boolean) => void;
  onEdit: () => void;
  onDelete: () => void;
};

export function ShoppingItemRow({
  item,
  toggling,
  onToggle,
  onEdit,
  onDelete,
}: ShoppingItemRowProps) {
  const amount = itemAmountLabel(item);

  return (
    <div
      className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 ${
        item.checked
          ? "border-stone-100 bg-stone-50/60"
          : "border-stone-100 bg-white"
      } ${toggling ? "opacity-60" : ""}`}
    >
      <input
        type="checkbox"
        checked={item.checked}
        disabled={toggling}
        onChange={(event) => onToggle(event.target.checked)}
        className="mt-0.5 h-4 w-4 shrink-0 rounded border-stone-300 text-emerald-600"
        aria-label={`Отметить ${item.name}`}
      />
      <div className="min-w-0 flex-1">
        <p
          className={`text-sm font-medium leading-snug ${
            item.checked ? "text-stone-400 line-through" : "text-stone-900"
          }`}
        >
          {item.name}
          {amount ? (
            <span
              className={
                item.checked ? "text-stone-300" : "text-stone-500"
              }
            >
              {" "}
              — {amount}
            </span>
          ) : null}
        </p>
        <p className="mt-0.5 text-[11px] text-stone-400">
          {sourceLabel(item.source)}
        </p>
        {item.added_to_pantry || item.linked_pantry_item_id ? (
          <p className="mt-0.5 text-[11px] font-medium text-teal-700">
            Добавлено в запасы
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
