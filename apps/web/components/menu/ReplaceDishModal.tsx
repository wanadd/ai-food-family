"use client";

import { MEAL_LABELS } from "@/lib/menu/labels";
import type { MenuVariant } from "@/lib/menu/types";

type ReplaceDishModalProps = {
  menu: MenuVariant;
  onClose: () => void;
  onSelectMeal: (mealIndex: number) => void;
  loading: boolean;
};

export function ReplaceDishModal({
  menu,
  onClose,
  onSelectMeal,
  loading,
}: ReplaceDishModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/50 p-4 sm:items-center">
      <div
        className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="replace-dish-title"
      >
        <h3
          id="replace-dish-title"
          className="text-lg font-bold text-stone-900"
        >
          Заменить блюдо
        </h3>
        <p className="mt-1 text-sm text-stone-500">
          Выберите приём пищи — ПланАм предложит альтернативу с учётом
          ваших ограничений. На следующем шаге покажем стоимость.
        </p>

        <ul className="mt-4 max-h-64 space-y-2 overflow-y-auto">
          {menu.meals.map((meal, index) => (
            <li key={`${meal.meal_type}-${index}`}>
              <button
                type="button"
                disabled={loading}
                onClick={() => onSelectMeal(index)}
                className="w-full rounded-xl border border-stone-200 px-4 py-3 text-left transition hover:border-emerald-300 hover:bg-emerald-50 disabled:opacity-50"
              >
                <span className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                  {MEAL_LABELS[meal.meal_type]}
                </span>
                <p className="mt-1 font-medium text-stone-900">{meal.name}</p>
                <p className="text-xs text-stone-500">{meal.description}</p>
              </button>
            </li>
          ))}
        </ul>

        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="mt-4 w-full rounded-xl border border-stone-200 py-3 text-sm font-semibold text-stone-600"
        >
          Отмена
        </button>
      </div>
    </div>
  );
}
