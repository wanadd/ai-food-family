import type { ShoppingCategory } from "./types";

const FALLBACK_META: Record<string, { label: string; emoji: string }> = {
  продукты: { label: "Продукты", emoji: "🛒" },
  овощи: { label: "Овощи", emoji: "🥕" },
  фрукты: { label: "Фрукты", emoji: "🍎" },
  мясо: { label: "Мясо", emoji: "🥩" },
  рыба: { label: "Рыба", emoji: "🐟" },
  молочное: { label: "Молочное", emoji: "🥛" },
  яйца: { label: "Яйца", emoji: "🥚" },
  крупы: { label: "Крупы", emoji: "🌾" },
  бакалея: { label: "Бакалея", emoji: "🫙" },
  специи: { label: "Специи", emoji: "🧂" },
  зелень: { label: "Зелень", emoji: "🌿" },
  хлеб: { label: "Хлеб", emoji: "🍞" },
  напитки: { label: "Напитки", emoji: "🥤" },
  дом_и_химия: { label: "Дом и химия", emoji: "🧴" },
  аптека: { label: "Аптека", emoji: "💊" },
  ремонт: { label: "Ремонт", emoji: "🔧" },
  другое: { label: "Другое", emoji: "📦" },
};

export function categoryMeta(
  slug: string,
  categories: ShoppingCategory[],
): { label: string; emoji: string } {
  const found = categories.find((c) => c.slug === slug);
  if (found) {
    return {
      label: found.name,
      emoji: found.icon ?? FALLBACK_META[slug]?.emoji ?? "📦",
    };
  }
  return FALLBACK_META[slug] ?? { label: slug, emoji: "📦" };
}

export function sourceLabel(source: string): string {
  if (source === "menu") {
    return "из меню";
  }
  return "вручную";
}
