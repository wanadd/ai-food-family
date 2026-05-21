"use client";

import {
  categoryLabel,
  dietLabel,
  difficultyLabel,
  mealLabel,
} from "@/lib/recipes/labels";
import type { RecipeDetail } from "@/lib/recipes/types";

type RecipeDetailModalProps = {
  recipe: RecipeDetail;
  onClose: () => void;
  onToggleFavorite: () => void;
  togglingFavorite: boolean;
};

export function RecipeDetailModal({
  recipe,
  onClose,
  onToggleFavorite,
  togglingFavorite,
}: RecipeDetailModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/50 p-4 sm:items-center">
      <div
        className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl bg-white shadow-xl"
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
            <span className="text-stone-400">·</span>
            <span>{recipe.servings} порц.</span>
            <span className="text-stone-400">·</span>
            <span>{difficultyLabel(recipe.difficulty)}</span>
          </div>
          {recipe.diets.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1">
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

        <div className="overflow-y-auto px-5 py-4">
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
        </div>

        <div className="border-t border-stone-100 p-4">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-xl bg-stone-900 py-3 text-sm font-semibold text-white"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
