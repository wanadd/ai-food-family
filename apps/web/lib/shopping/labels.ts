import {
  categoryV1Meta,
  SHOPPING_CATEGORIES_V1,
} from "@/lib/shopping/categories-v1";
import type { ShoppingCategory } from "./types";

const FALLBACK_META = Object.fromEntries(
  SHOPPING_CATEGORIES_V1.map((c) => [c.slug, { label: c.label, emoji: c.emoji }]),
) as Record<string, { label: string; emoji: string }>;

export function categoryMeta(
  slug: string,
  categories: ShoppingCategory[],
): { label: string; emoji: string } {
  const found = categories.find((c) => c.slug === slug);
  if (found) {
    return {
      label: found.name,
      emoji: found.icon ?? FALLBACK_META[slug]?.emoji ?? categoryV1Meta(slug).emoji,
    };
  }
  const v1 = FALLBACK_META[slug];
  if (v1) {
    return v1;
  }
  const meta = categoryV1Meta(slug);
  return { label: meta.label, emoji: meta.emoji };
}

export function sourceLabel(source: string): string {
  if (source === "menu") {
    return "из меню";
  }
  return "вручную";
}
