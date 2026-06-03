import { selectMenu } from "@/lib/menu/api";
import { getMenuDays } from "@/lib/menu/menu-days";
import type { AppMode } from "@/lib/app-mode/types";
import type { MenuMeal, MenuVariant } from "@/lib/menu/types";
import type { RecipeDetail, RecipeSummary } from "@/lib/recipes/types";
import { addRecipeToMenu } from "@/lib/recipes/analysis-api";

export function recipeToMenuMeal(recipe: RecipeSummary | RecipeDetail): MenuMeal {
  return {
    meal_type: (recipe.meal_type as MenuMeal["meal_type"]) || "lunch",
    name: recipe.title,
    description: (recipe.description || "").slice(0, 500),
    prep_time_minutes: recipe.prep_time_minutes ?? 30,
    calories_estimate: recipe.calories_per_serving ?? null,
    recipe_id: recipe.id,
  };
}

/** Put recipe into a day/slot and persist via selectMenu (no new backend rules). */
export async function assignRecipeToMenuSlot(
  initData: string,
  mode: AppMode,
  recipe: RecipeSummary | RecipeDetail,
  menu: MenuVariant,
  dayIndex: number,
  mealIndex: number,
): Promise<MenuVariant> {
  const meal = recipeToMenuMeal(recipe);
  const days = getMenuDays(menu);

  if (days.length <= 1 && !menu.days?.length) {
    const updated = await addRecipeToMenu(initData, mode, recipe.id, {
      meal_type: meal.meal_type,
      replace_meal_index: mealIndex,
    });
    await selectMenu(initData, mode, updated);
    return updated;
  }

  const nextDays = days.map((day) => {
    if (day.day_index !== dayIndex) {
      return day;
    }
    const meals = [...day.meals];
    if (mealIndex >= 0 && mealIndex < meals.length) {
      meals[mealIndex] = meal;
    } else {
      meals.push(meal);
    }
    return { ...day, meals };
  });

  const updated: MenuVariant = {
    ...menu,
    days: nextDays,
    meals: nextDays[0]?.meals ?? menu.meals,
  };

  await selectMenu(initData, mode, updated);
  return updated;
}
