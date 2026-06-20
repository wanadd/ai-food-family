/**
 * PlanAm V1 shopping categories — single source of truth.
 * @see docs/PLANAM_COLOR_SYSTEM_V1.md
 */

export type ShoppingCategoryV1 = {
  slug: string;
  label: string;
  emoji: string;
};

/** Canonical V1 categories in display order. «Продукты» is forbidden. */
export const SHOPPING_CATEGORIES_V1: readonly ShoppingCategoryV1[] = [
  { slug: "овощи_зелень", label: "Овощи и зелень", emoji: "🥬" },
  { slug: "фрукты_ягоды", label: "Фрукты и ягоды", emoji: "🍓" },
  { slug: "мясо_птица", label: "Мясо и птица", emoji: "🥩" },
  { slug: "рыба_морепродукты", label: "Рыба и морепродукты", emoji: "🐟" },
  { slug: "молочные", label: "Молочные продукты", emoji: "🥛" },
  { slug: "яйца", label: "Яйца", emoji: "🥚" },
  { slug: "хлеб_выпечка", label: "Хлеб и выпечка", emoji: "🍞" },
  { slug: "крупы_макароны", label: "Крупы и макароны", emoji: "🌾" },
  { slug: "бакалея", label: "Бакалея", emoji: "🫙" },
  { slug: "специи_соусы", label: "Специи и соусы", emoji: "🧂" },
  { slug: "напитки", label: "Напитки", emoji: "🥤" },
  { slug: "быт_уборка", label: "Быт и уборка", emoji: "🧴" },
  { slug: "детские_товары", label: "Детские товары", emoji: "🧸" },
  { slug: "для_питомцев", label: "Для питомцев", emoji: "🐾" },
  { slug: "другое", label: "Другое", emoji: "📦" },
] as const;

export const FORBIDDEN_CATEGORY_SLUG = "продукты";
export const DEFAULT_CATEGORY_SLUG = "другое";

const CANONICAL_SLUGS = new Set(
  SHOPPING_CATEGORIES_V1.map((c) => c.slug),
);

export const LEGACY_SLUG_MAP: Record<string, string> = {
  продукты: DEFAULT_CATEGORY_SLUG,
  овощи: "овощи_зелень",
  зелень: "овощи_зелень",
  фрукты: "фрукты_ягоды",
  мясо: "мясо_птица",
  рыба: "рыба_морепродукты",
  молочное: "молочные",
  крупы: "крупы_макароны",
  специи: "специи_соусы",
  хлеб: "хлеб_выпечка",
  дом_и_химия: "быт_уборка",
  бытовые: "быт_уборка",
  животные: "для_питомцев",
  заморозка: "бакалея",
  сладости: "бакалея",
  аптека: "другое",
  ремонт: "другое",
};

const CATEGORY_ORDER = new Map(
  SHOPPING_CATEGORIES_V1.map((c, i) => [c.slug, i]),
);

export function isCanonicalCategorySlug(slug: string): boolean {
  return CANONICAL_SLUGS.has(slug);
}

export function categoryV1Meta(slug: string): ShoppingCategoryV1 {
  const found = SHOPPING_CATEGORIES_V1.find((c) => c.slug === slug);
  if (found) {
    return found;
  }
  return SHOPPING_CATEGORIES_V1[SHOPPING_CATEGORIES_V1.length - 1]!;
}

export function mapLegacyCategorySlug(slug: string): string | null {
  const raw = slug.trim().toLowerCase();
  if (!raw || raw === FORBIDDEN_CATEGORY_SLUG) {
    return null;
  }
  if (CANONICAL_SLUGS.has(raw)) {
    return raw;
  }
  return LEGACY_SLUG_MAP[raw] ?? null;
}

export function compareCategoryOrder(a: string, b: string): number {
  const ia = CATEGORY_ORDER.get(a) ?? 999;
  const ib = CATEGORY_ORDER.get(b) ?? 999;
  if (ia !== ib) {
    return ia - ib;
  }
  return categoryV1Meta(a).label.localeCompare(categoryV1Meta(b).label, "ru");
}
