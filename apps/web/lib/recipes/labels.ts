export const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
  dessert: "Десерт",
  drink: "Напитки",
  drinks: "Напитки",
  cocktail: "Коктейли",
};

/** Quick filters shown on the recipes catalog (no long dropdown lists). */
export const CATALOG_MEAL_FILTERS: { value: string; label: string }[] = [
  { value: "breakfast", label: "Завтрак" },
  { value: "lunch", label: "Обед" },
  { value: "dinner", label: "Ужин" },
  { value: "snack", label: "Перекус" },
  { value: "dessert", label: "Десерт" },
  { value: "drink", label: "Напитки" },
];

export const CATEGORY_LABELS: Record<string, string> = {
  soup: "Суп",
  main: "Основное",
  side: "Гарнир",
  salad: "Салат",
  snack: "Перекус",
  breakfast: "Завтрак",
  dessert: "Десерт",
  quick: "Быстрое",
  kids: "Детское",
};

export const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Легко",
  medium: "Средне",
  hard: "Сложно",
};

export const DIET_LABELS: Record<string, string> = {
  vegetarian: "Вегетарианское",
  vegan: "Веганское",
  kids_friendly: "Для детей",
  budget: "Эконом",
  low_sugar: "Без сахара",
  low_salt: "Мало соли",
  pescatarian: "С рыбой",
};

/** User-facing label or empty string — never expose raw slugs in UI. */
export function mealLabel(value: string | null | undefined): string {
  if (!value) return "";
  return MEAL_TYPE_LABELS[value] ?? "";
}

export function categoryLabel(value: string | null | undefined): string {
  if (!value) return "";
  return CATEGORY_LABELS[value] ?? "";
}

export function difficultyLabel(value: string): string {
  return DIFFICULTY_LABELS[value] ?? value;
}

export function dietLabel(value: string): string {
  return DIET_LABELS[value] ?? value;
}

export function hasMealLabel(value: string | null | undefined): boolean {
  return Boolean(mealLabel(value));
}

export function hasCategoryLabel(value: string | null | undefined): boolean {
  return Boolean(categoryLabel(value));
}
