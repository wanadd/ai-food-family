export const CATEGORY_META: Record<
  string,
  { label: string; emoji: string }
> = {
  продукты: { label: "Продукты", emoji: "🛒" },
  овощи: { label: "Овощи", emoji: "🥕" },
  фрукты: { label: "Фрукты", emoji: "🍎" },
  мясо: { label: "Мясо", emoji: "🥩" },
  рыба: { label: "Рыба", emoji: "🐟" },
  молочное: { label: "Молочное", emoji: "🥛" },
  яйца: { label: "Яйца", emoji: "🥚" },
  крупы: { label: "Крупы", emoji: "🌾" },
  бобовые: { label: "Бобовые", emoji: "🫘" },
  напитки: { label: "Напитки", emoji: "🥤" },
  алкоголь: { label: "Алкоголь", emoji: "🍷" },
  хлеб: { label: "Хлеб", emoji: "🍞" },
  заморозка: { label: "Заморозка", emoji: "🧊" },
  другое_продуктовое: { label: "Другое продуктовое", emoji: "🥫" },
  соусы: { label: "Соусы", emoji: "🫙" },
  прочее: { label: "Прочее", emoji: "📦" },
  дом_и_химия: { label: "Дом и химия", emoji: "🧴" },
  хозтовары: { label: "Хозтовары", emoji: "🧹" },
  ребенку: { label: "Ребёнку", emoji: "🧸" },
  подарки: { label: "Подарки", emoji: "🎁" },
  одежда_и_обувь: { label: "Одежда и обувь", emoji: "👕" },
  аптека: { label: "Аптека", emoji: "💊" },
  ремонт: { label: "Ремонт", emoji: "🔧" },
  питомцы: { label: "Питомцы", emoji: "🐾" },
  другое: { label: "Другое", emoji: "📦" },
};

export const CATEGORY_ORDER = [
  "продукты",
  "овощи",
  "фрукты",
  "мясо",
  "рыба",
  "молочное",
  "яйца",
  "крупы",
  "бобовые",
  "напитки",
  "алкоголь",
  "хлеб",
  "заморозка",
  "другое_продуктовое",
  "соусы",
  "прочее",
  "дом_и_химия",
  "хозтовары",
  "ребенку",
  "подарки",
  "одежда_и_обувь",
  "аптека",
  "ремонт",
  "питомцы",
  "другое",
];

export function categoryLabel(category: string): string {
  return CATEGORY_META[category]?.label ?? category;
}

export function categoryEmoji(category: string): string {
  return CATEGORY_META[category]?.emoji ?? "🛒";
}
