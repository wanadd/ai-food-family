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
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-graphite-900/50 p-4 sm:items-center">
      <div
        className="w-full max-w-md rounded-card bg-cream-surface p-5 shadow-lift"
        role="dialog"
        aria-modal="true"
        aria-labelledby="replace-dish-title"
      >
        <h3
          id="replace-dish-title"
          className="text-lg font-bold text-graphite-900"
        >
          Заменить блюдо
        </h3>
        <p className="mt-1 text-sm text-graphite-500">
          Выберите приём пищи для замены — ПланАм подберёт новое блюдо
          с учётом ваших ограничений. На следующем шаге покажем стоимость.
        </p>
        <p className="mt-1 text-xs text-graphite-400">
          Список ниже — текущие блюда в плане. Альтернатива появится после
          подтверждения.
        </p>

        <ul className="mt-4 max-h-64 space-y-2 overflow-y-auto">
          {menu.meals.map((meal, index) => (
            <li key={`${meal.meal_type}-${index}`}>
              <button
                type="button"
                disabled={loading}
                onClick={() => onSelectMeal(index)}
                className="w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-left transition hover:border-sage-300 hover:bg-sage-50 disabled:opacity-50"
              >
                <span className="text-xs font-semibold uppercase tracking-wide text-sage-700">
                  {MEAL_LABELS[meal.meal_type]}
                </span>
                <p className="mt-1 font-medium text-graphite-900">{meal.name}</p>
                <p className="text-xs text-graphite-500">{meal.description}</p>
              </button>
            </li>
          ))}
        </ul>

        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="pa-btn mt-4 w-full py-3 text-sm"
        >
          Отмена
        </button>
      </div>
    </div>
  );
}
