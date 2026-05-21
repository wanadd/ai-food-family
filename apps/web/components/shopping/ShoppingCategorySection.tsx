"use client";

import { ShoppingItemRow } from "@/components/shopping/ShoppingItemRow";
import { categoryEmoji, categoryLabel } from "@/lib/shopping/labels";
import type { ShoppingListItem } from "@/lib/shopping/types";

type ShoppingCategorySectionProps = {
  category: string;
  items: ShoppingListItem[];
  togglingId: string | null;
  onToggle: (itemId: string, checked: boolean) => void;
};

export function ShoppingCategorySection({
  category,
  items,
  togglingId,
  onToggle,
}: ShoppingCategorySectionProps) {
  const checkedInCategory = items.filter((item) => item.checked).length;

  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between px-1">
        <h3 className="flex items-center gap-2 text-sm font-bold text-stone-800">
          <span aria-hidden>{categoryEmoji(category)}</span>
          {categoryLabel(category)}
        </h3>
        <span className="text-xs font-medium text-stone-400">
          {checkedInCategory}/{items.length}
        </span>
      </div>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <ShoppingItemRow
              item={item}
              toggling={togglingId === item.id}
              onToggle={(checked) => onToggle(item.id, checked)}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
