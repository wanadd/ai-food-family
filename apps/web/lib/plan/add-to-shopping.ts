import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import type { AppMode } from "@/lib/app-mode/types";
import { addRecipeToShopping } from "@/lib/recipes/api";
import type { MenuMeal } from "@/lib/menu/types";

export async function addMealIngredientsToShopping(
  initData: string,
  mode: AppMode,
  meal: MenuMeal,
): Promise<{ ok: boolean; message: string }> {
  if (!meal.recipe_id) {
    return {
      ok: false,
      message: "У этого блюда нет рецепта — обновите список из меню или выберите другое блюдо.",
    };
  }
  await addRecipeToShopping(initData, meal.recipe_id);
  invalidateCache("shopping-list");
  invalidateCache("menu-overview");
  return { ok: true, message: `«${meal.name}» добавлено в покупки` };
}
