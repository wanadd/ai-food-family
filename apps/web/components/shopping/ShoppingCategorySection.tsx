"use client";

import { useState } from "react";

import { ShoppingItemRow } from "@/components/shopping/ShoppingItemRow";
import { categoryMeta } from "@/lib/shopping/labels";
import type { ShoppingCategory, ShoppingListItem } from "@/lib/shopping/types";

const VISIBLE_LIMIT = 5;

type ShoppingCategorySectionProps = {
  category: string;
  items: ShoppingListItem[];
  categories: ShoppingCategory[];
  expanded: boolean;
  togglingId: string | null;
  onToggleExpand: () => void;
  onToggleItem: (itemId: string, checked: boolean) => void;
  onEditItem: (item: ShoppingListItem) => void;
  onDeleteItem: (item: ShoppingListItem) => void;
};

export function ShoppingCategorySection({
  category,
  items,
  categories,
  expanded,
  togglingId,
  onToggleExpand,
  onToggleItem,
  onEditItem,
  onDeleteItem,
}: ShoppingCategorySectionProps) {
  const [showAll, setShowAll] = useState(false);
  const meta = categoryMeta(category, categories);
  const checkedCount = items.filter((item) => item.checked).length;
  const visibleItems = showAll ? items : items.slice(0, VISIBLE_LIMIT);
  const hiddenCount = items.length - VISIBLE_LIMIT;

  return (
    <section className="rounded-xl border border-stone-100 bg-white">
      <button
        type="button"
        onClick={onToggleExpand}
        className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left"
      >
        <span className="flex min-w-0 items-center gap-2 text-sm font-semibold text-stone-800">
          <span aria-hidden>{meta.emoji}</span>
          <span className="truncate">{meta.label}</span>
        </span>
        <span className="shrink-0 text-xs font-medium text-stone-400">
          {checkedCount}/{items.length}
        </span>
      </button>

      {expanded ? (
        <div className="space-y-1.5 border-t border-stone-50 px-2 pb-2 pt-1">
          {visibleItems.map((item) => (
            <ShoppingItemRow
              key={item.id}
              item={item}
              toggling={togglingId === item.id}
              onToggle={(checked) => onToggleItem(item.id, checked)}
              onEdit={() => onEditItem(item)}
              onDelete={() => onDeleteItem(item)}
            />
          ))}
          {!showAll && hiddenCount > 0 ? (
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="w-full py-1.5 text-center text-xs font-semibold text-emerald-700"
            >
              Показать ещё {hiddenCount}
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
