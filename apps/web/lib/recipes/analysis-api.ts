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

/**
 * GET /recipes/{id}/evaluate.
 *
 * IMPORTANT: spends Amas when the OpenAI key is configured on the
 * server. Backend calls subscription_service.require_ai_action with
 * action ``recipe_analyze`` (see apps/api/app/services/recipe_analysis.py
 * and AMA_COSTS["recipe_analyze"] = 2 in subscription_catalog.py).
 *
 * Never invoke this from a useEffect on mount. Always require an
 * explicit user click that goes through AmaConfirmDialog.
 */
export async function evaluateRecipe(
  initData: string,
  mode: AppMode,
  recipeId: number,
): Promise<RecipeEvaluation> {
  return requireGet(initData, mode, `/recipes/${recipeId}/evaluate`);
}

/**
 * GET /recipes/{id}/family-compatibility.
 *
 * Safe to auto-load: backend handler is recipe_analysis.family_compatibility
 * which is a pure heuristic over the recipe text and family member
 * profiles. It does NOT call OpenAI and does NOT charge Amas.
 */
export async function fetchRecipeFamilyFit(
  initData: string,
  mode: AppMode,
  recipeId: number,
): Promise<RecipeFamilyFit> {
  return requireGet(initData, mode, `/recipes/${recipeId}/family-compatibility`);
}

/**
 * GET /recipes/{id}/improve.
 *
 * Does NOT charge Amas (the Ama charge lives on the POST companion
 * apply_improvements -> AMA_COSTS["recipe_improve"]). However, when
 * the OpenAI key is configured, the GET still calls ai_improve_recipe
 * and consumes server-side AI quota. Treat it like a paid action and
 * gate it behind an explicit user click + confirmation dialog rather
 * than auto-loading on mount.
 */
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
