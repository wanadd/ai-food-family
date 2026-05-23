"use client";

import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  categoryLabel,
  dietLabel,
  difficultyLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import type { RecipeDetail } from "@/lib/recipes/types";
import { addRecipeToShopping } from "@/lib/recipes/api";
import {
  addRecipeToMenu,
  evaluateRecipe,
  fetchRecipeFamilyFit,
  fetchRecipeImproveSuggestions,
} from "@/lib/recipes/analysis-api";
import type {
  RecipeEvaluation,
  RecipeFamilyFit,
  RecipeImproveSuggestion,
} from "@/lib/menu/overview-types";

type RecipeDetailModalProps = {
  recipe: RecipeDetail;
  onClose: () => void;
  onToggleFavorite: () => void;
  togglingFavorite: boolean;
  menuMode?: boolean;
  onAddedToMenu?: () => void;
};

const FIT_STYLES = {
  good: "border-emerald-200 bg-emerald-50 text-emerald-900",
  partial: "border-amber-200 bg-amber-50 text-amber-900",
  not_recommended: "border-red-200 bg-red-50 text-red-900",
};

export function RecipeDetailModal({
  recipe,
  onClose,
  onToggleFavorite,
  togglingFavorite,
  menuMode = false,
  onAddedToMenu,
}: RecipeDetailModalProps) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [evaluation, setEvaluation] = useState<RecipeEvaluation | null>(null);
  const [familyFit, setFamilyFit] = useState<RecipeFamilyFit | null>(null);
  const [suggestions, setSuggestions] = useState<RecipeImproveSuggestion[]>([]);
  const [adding, setAdding] = useState(false);
  const [addingShopping, setAddingShopping] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadAnalysis = useCallback(async () => {
    if (!initData) return;
    try {
      const [ev, fam, imp] = await Promise.all([
        evaluateRecipe(initData, mode, recipe.id),
        fetchRecipeFamilyFit(initData, mode, recipe.id),
        fetchRecipeImproveSuggestions(initData, mode, recipe.id),
      ]);
      setEvaluation(ev);
      setFamilyFit(fam);
      setSuggestions(imp.suggestions ?? []);
    } catch {
      setEvaluation(null);
    }
  }, [initData, mode, recipe.id]);

  useEffect(() => {
    void loadAnalysis();
  }, [loadAnalysis]);

  async function handleAddToShopping() {
    if (!initData) return;
    setAddingShopping(true);
    setMessage(null);
    try {
      await addRecipeToShopping(initData, recipe.id, recipe.servings);
      setMessage("Ингредиенты добавлены в список покупок.");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Не удалось добавить в покупки",
      );
    } finally {
      setAddingShopping(false);
    }
  }

  async function handleAddToMenu() {
    if (!initData) return;
    setAdding(true);
    setMessage(null);
    try {
      await addRecipeToMenu(initData, mode, recipe.id, {
        meal_type: recipe.meal_type,
      });
      setMessage("Блюдо добавлено в меню. Решение за вами — ПланАм только подсказал.");
      onAddedToMenu?.();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Сначала выберите или создайте меню",
      );
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/50 p-0 sm:items-center sm:p-4">
      <div
        className="flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl bg-white shadow-xl sm:rounded-2xl"
        role="dialog"
        aria-modal="true"
      >
        <div className="border-b border-stone-100 px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-stone-900">{recipe.title}</h2>
              <p className="mt-1 text-sm text-stone-500">{recipe.description}</p>
            </div>
            <button
              type="button"
              disabled={togglingFavorite}
              onClick={onToggleFavorite}
              className="text-2xl disabled:opacity-50"
            >
              {recipe.is_favorited ? "★" : "☆"}
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <span className="font-semibold text-violet-700">
              {mealLabel(recipe.meal_type)}
            </span>
            <span className="text-stone-400">·</span>
            <span>{categoryLabel(recipe.category)}</span>
            <span className="text-stone-400">·</span>
            <span>{recipe.prep_time_minutes} мин</span>
            {recipe.calories_per_serving ? (
              <>
                <span className="text-stone-400">·</span>
                <span>{Math.round(recipe.calories_per_serving)} ккал</span>
              </>
            ) : null}
            {recipe.protein_g ? (
              <>
                <span className="text-stone-400">·</span>
                <span>Б {Math.round(recipe.protein_g)} г</span>
              </>
            ) : null}
          </div>
          {recipe.is_drink ? (
            <p className="mt-2 text-xs text-stone-500">
              {recipe.is_alcoholic
                ? "Содержит алкоголь — ПланАм рекомендует ограничить при цели «здоровье/спорт»."
                : "Напиток"}
              {recipe.caffeine_mg ? ` · кофеин ~${recipe.caffeine_mg} мг` : ""}
            </p>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 pb-28">
          {evaluation ? (
            <section
              className={`mb-4 rounded-xl border p-3 ${FIT_STYLES[evaluation.fit_level]}`}
            >
              <p className="text-sm font-bold">{evaluation.title}</p>
              <ul className="mt-2 space-y-1 text-xs">
                {evaluation.reasons.map((r) => (
                  <li key={r.code}>· {r.label}</li>
                ))}
              </ul>
              <p className="mt-2 text-[11px] opacity-80">
                Это рекомендация, не запрет — выбор всегда за вами.
              </p>
            </section>
          ) : null}

          {familyFit && familyFit.members.length > 0 ? (
            <section className="mb-4 rounded-xl border border-stone-100 bg-stone-50 p-3">
              <p className="text-sm font-bold text-stone-900">Совместимость семьи</p>
              <ul className="mt-2 space-y-1.5 text-sm">
                {familyFit.members.map((m) => (
                  <li key={m.name} className="flex gap-2">
                    <span>{m.status === "ok" ? "✓" : "⚠"}</span>
                    <span>
                      <span className="font-medium">{m.name}</span>
                      <span className="text-stone-500"> — {m.note}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {suggestions.length > 0 ? (
            <section className="mb-4 rounded-xl border border-violet-100 bg-violet-50/40 p-3">
              <p className="text-sm font-bold text-stone-900">Улучшить рецепт</p>
              <ul className="mt-2 space-y-2 text-xs text-stone-600">
                {suggestions.slice(0, 4).map((s) => (
                  <li key={s.id}>
                    <span className="font-semibold text-stone-800">{s.label}:</span>{" "}
                    {s.description}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {message ? (
            <p className="mb-3 text-sm text-emerald-800">{message}</p>
          ) : null}

          <section>
            <h3 className="text-sm font-bold uppercase tracking-wide text-stone-500">
              Ингредиенты
            </h3>
            <ul className="mt-2 space-y-2">
              {recipe.ingredients.map((item) => (
                <li
                  key={`${item.name}-${item.amount}`}
                  className="flex justify-between gap-2 text-sm"
                >
                  <span className="font-medium text-stone-800">{item.name}</span>
                  <span className="text-stone-500">{item.amount}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-6">
            <h3 className="text-sm font-bold uppercase tracking-wide text-stone-500">
              Шаги
            </h3>
            <ol className="mt-2 list-decimal space-y-2 pl-5 text-sm text-stone-700">
              {recipe.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>

          {recipe.diets.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-1">
              {recipe.diets.map((diet) => (
                <span
                  key={diet}
                  className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800"
                >
                  {dietLabel(diet)}
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <div className="border-t border-stone-100 bg-white px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <button
            type="button"
            disabled={adding}
            onClick={() => void handleAddToMenu()}
            className="mb-2 w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
          >
            {adding ? "…" : "Добавить в меню"}
          </button>
          <button
            type="button"
            disabled={addingShopping}
            onClick={() => void handleAddToShopping()}
            className="mb-2 w-full rounded-xl border border-emerald-200 bg-emerald-50 py-3 text-sm font-semibold text-emerald-900 disabled:opacity-50"
          >
            {addingShopping ? "…" : "Добавить в покупки"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-xl border border-stone-200 py-3 text-sm font-semibold text-stone-800"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
