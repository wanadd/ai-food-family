import { compareCategoryOrder } from "@/lib/shopping/categories-v1";
import { normalizeCategorySlug } from "@/lib/shopping/category-suggest";
import { categoryMeta } from "@/lib/shopping/labels";
import type { ShoppingCategory, ShoppingListItem } from "@/lib/shopping/types";

export type ShoppingCategoryGroup = {
  category: string;
  label: string;
  emoji: string;
  items: ShoppingListItem[];
};

export function groupShoppingItems(
  items: ShoppingListItem[],
  categories: ShoppingCategory[],
): ShoppingCategoryGroup[] {
  const buckets = new Map<string, ShoppingListItem[]>();
  for (const item of items) {
    const cat = normalizeCategorySlug(item.category, item.name);
    const list = buckets.get(cat) ?? [];
    list.push({ ...item, category: cat });
    buckets.set(cat, list);
  }
  return Array.from(buckets.entries())
    .map(([category, groupItems]) => {
      const meta = categoryMeta(category, categories);
      return {
        category,
        label: meta.label,
        emoji: meta.emoji,
        items: groupItems,
      };
    })
    .sort((a, b) => compareCategoryOrder(a.category, b.category));
}

export function shoppingProgress(
  total: number,
  checked: number,
): { percent: number; label: string } {
  if (total <= 0) {
    return { percent: 0, label: "Список пуст" };
  }
  const percent = Math.round((checked / total) * 100);
  return {
    percent,
    label: `${checked} из ${total} · ${percent}%`,
  };
}
