import { compareCategoryOrder } from "@/lib/shopping/categories-v1";
import { normalizeCategorySlug } from "@/lib/shopping/category-suggest";
import { categoryMeta } from "@/lib/shopping/labels";
import type { ShoppingCategory } from "@/lib/shopping/types";
import type { PantryItem } from "@/lib/pantry/types";

export type PantryCategoryGroup = {
  category: string;
  label: string;
  emoji: string;
  items: PantryItem[];
};

export function groupPantryItems(
  items: PantryItem[],
  categories: ShoppingCategory[],
): PantryCategoryGroup[] {
  const buckets = new Map<string, PantryItem[]>();
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
