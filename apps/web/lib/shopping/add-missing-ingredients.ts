import type { AppMode } from "@/lib/app-mode/types";
import {
  buildPantryNameIndex,
  isIngredientInPantry,
} from "@/lib/pantry/pantry-ingredient-match";
import type { RecipeIngredient } from "@/lib/recipes/types";
import { createShoppingItem } from "@/lib/shopping/api";
import { detectProductCategory } from "@/lib/planam/productTaxonomy";
import type { ShoppingItemDraft, ShoppingList } from "@/lib/shopping/types";

function draftFromIngredient(ing: RecipeIngredient): ShoppingItemDraft {
  const category = detectProductCategory(ing.name);
  return {
    name: ing.name,
    category,
    quantity: ing.quantity?.trim() || "1",
    unit: ing.unit?.trim() || "шт",
    note: "",
    is_food: true,
  };
}

export function filterMissingIngredients(
  ingredients: RecipeIngredient[],
  pantryNames: readonly string[],
): RecipeIngredient[] {
  const index = buildPantryNameIndex(pantryNames);
  return ingredients.filter((ing) => !isIngredientInPantry(ing.name, index));
}

export async function addMissingIngredientsToShopping(
  initData: string,
  mode: AppMode,
  ingredients: RecipeIngredient[],
  pantryNames: readonly string[],
): Promise<ShoppingList> {
  const missing = filterMissingIngredients(ingredients, pantryNames);
  if (missing.length === 0) {
    throw new Error("Все ингредиенты уже есть дома");
  }
  let list: ShoppingList | null = null;
  for (const ing of missing) {
    list = await createShoppingItem(initData, mode, draftFromIngredient(ing));
  }
  if (!list) {
    throw new Error("Не удалось добавить ингредиенты");
  }
  return list;
}
