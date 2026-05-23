import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";
import type { MenuVariant } from "@/lib/menu/types";
import type {
  RecipeEvaluation,
  RecipeFamilyFit,
  RecipeImproveSuggestion,
} from "@/lib/menu/overview-types";

async function requireGet<T>(
  initData: string,
  mode: AppMode,
  path: string,
): Promise<T> {
  const data = await apiGet<T>(initData, mode, path);
  if (data == null) {
    throw new Error("Пустой ответ сервера");
  }
  return data;
}

export async function evaluateRecipe(
  initData: string,
  mode: AppMode,
  recipeId: number,
): Promise<RecipeEvaluation> {
  return requireGet(initData, mode, `/recipes/${recipeId}/evaluate`);
}

export async function fetchRecipeFamilyFit(
  initData: string,
  mode: AppMode,
  recipeId: number,
): Promise<RecipeFamilyFit> {
  return requireGet(initData, mode, `/recipes/${recipeId}/family-compatibility`);
}

export async function fetchRecipeImproveSuggestions(
  initData: string,
  mode: AppMode,
  recipeId: number,
): Promise<{ suggestions: RecipeImproveSuggestion[] }> {
  return requireGet(initData, mode, `/recipes/${recipeId}/improve`);
}

export async function addRecipeToMenu(
  initData: string,
  mode: AppMode,
  recipeId: number,
  payload: { meal_type?: string; replace_meal_index?: number },
): Promise<MenuVariant> {
  const data = await apiFetch<MenuVariant>(
    initData,
    mode,
    `/recipes/${recipeId}/add-to-menu`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
  if (!data) throw new Error("Не удалось добавить в меню");
  return data;
}
