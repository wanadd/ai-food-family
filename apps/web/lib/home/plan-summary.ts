import type { AppContext, AppMode } from "@/lib/app-mode/types";
import type { MenuMeal, MenuVariant } from "@/lib/menu/types";
import type { PantryItem } from "@/lib/pantry/types";
import type { ShoppingList } from "@/lib/shopping/types";

const MEAL_ORDER: Array<MenuMeal["meal_type"]> = [
  "breakfast",
  "lunch",
  "dinner",
];

const MEAL_LABELS: Record<MenuMeal["meal_type"], string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
};

export function getMealRows(menu: MenuVariant): { label: string; name: string }[] {
  const rows: { label: string; name: string }[] = [];
  for (const type of MEAL_ORDER) {
    const meal = menu.meals.find((m) => m.meal_type === type);
    if (meal) {
      rows.push({
        label: MEAL_LABELS[type],
        name: truncateMealName(meal.name),
      });
    }
  }
  if (!rows.length) {
    return menu.meals.slice(0, 3).map((meal) => ({
      label: MEAL_LABELS[meal.meal_type] ?? "Блюдо",
      name: truncateMealName(meal.name),
    }));
  }
  return rows;
}

function truncateMealName(name: string, max = 42): string {
  const trimmed = name.trim();
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, max - 1)}…`;
}

function normalizeName(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

export function countPantryMatches(
  menu: MenuVariant | null,
  pantryItems: PantryItem[],
): number {
  if (!menu?.ingredients?.length || !pantryItems.length) return 0;
  const pantryNames = new Set(
    pantryItems.map((item) => normalizeName(item.name)),
  );
  let matched = 0;
  for (const ingredient of menu.ingredients) {
    const key = normalizeName(ingredient.name);
    if (pantryNames.has(key)) {
      matched += 1;
      continue;
    }
    for (const pantryName of Array.from(pantryNames)) {
      if (pantryName.includes(key) || key.includes(pantryName)) {
        matched += 1;
        break;
      }
    }
  }
  return matched;
}

export function countExpiringSoon(items: PantryItem[]): number {
  return items.filter(
    (item) =>
      !item.is_expired &&
      item.days_until_expiry >= 0 &&
      item.days_until_expiry <= 3,
  ).length;
}

export function countToBuy(shopping: ShoppingList | null): number {
  if (!shopping) return 0;
  return shopping.items.filter((item) => !item.checked).length;
}

export function getPersonsCount(
  mode: AppMode,
  context: AppContext | null,
): number {
  if (mode === "family" && context?.family) {
    return context.family.members_count ?? context.family.members.length;
  }
  return 1;
}

export function formatPersonsLabel(count: number): string {
  const n = Math.abs(count);
  if (n === 1) return "Для 1 человека";
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `Для ${n} человек`;
  }
  return `Для ${n} человек`;
}

export function formatGoodsCount(count: number): string {
  const n = Math.abs(count);
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return `${n} товар`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `${n} товара`;
  }
  return `${n} товаров`;
}

export function formatProductsCount(count: number): string {
  const n = Math.abs(count);
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return `${n} продукт`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `${n} продукта`;
  }
  return `${n} продуктов`;
}
