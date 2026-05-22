"use client";

import { PantryItemRow } from "@/components/pantry/PantryItemRow";
import { categoryMeta } from "@/lib/shopping/labels";
import type { PantryItem } from "@/lib/pantry/types";

type PantryCategorySectionProps = {
  category: string;
  items: PantryItem[];
  expanded: boolean;
  onToggleExpand: () => void;
  onEdit: (item: PantryItem) => void;
  onDelete: (item: PantryItem) => void;
};

export function PantryCategorySection({
  category,
  items,
  expanded,
  onToggleExpand,
  onEdit,
  onDelete,
}: PantryCategorySectionProps) {
  const meta = categoryMeta(category, []);

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
          {items.length}
        </span>
      </button>
      {expanded ? (
        <div className="space-y-1 border-t border-stone-50 px-2 pb-2 pt-1">
          {items.map((item) => (
            <PantryItemRow
              key={item.id}
              item={item}
              onEdit={() => onEdit(item)}
              onDelete={() => onDelete(item)}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}
