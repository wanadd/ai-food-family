export const CATEGORY_META: Record<
  string,
  { label: string; emoji: string }
> = {
  овощи: { label: "Овощи", emoji: "🥕" },
  фрукты: { label: "Фрукты", emoji: "🍎" },
  мясо: { label: "Мясо", emoji: "🥩" },
  рыба: { label: "Рыба", emoji: "🐟" },
  молочное: { label: "Молочное", emoji: "🥛" },
  яйца: { label: "Яйца", emoji: "🥚" },
  крупы: { label: "Крупы", emoji: "🌾" },
  бобовые: { label: "Бобовые", emoji: "🫘" },
  соусы: { label: "Соусы", emoji: "🫙" },
  прочее: { label: "Прочее", emoji: "🛒" },
};

export const CATEGORY_ORDER = [
  "овощи",
  "фрукты",
  "мясо",
  "рыба",
  "молочное",
  "яйца",
  "крупы",
  "бобовые",
  "соусы",
  "прочее",
];

export function categoryLabel(category: string): string {
  return CATEGORY_META[category]?.label ?? category;
}

export function categoryEmoji(category: string): string {
  return CATEGORY_META[category]?.emoji ?? "🛒";
}
