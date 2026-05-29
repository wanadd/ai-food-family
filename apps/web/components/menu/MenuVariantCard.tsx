"use client";

import { useState } from "react";

import { MEAL_LABELS, VARIANT_LABELS } from "@/lib/menu/labels";
import type { MenuVariant } from "@/lib/menu/types";

type MenuVariantCardProps = {
  menu: MenuVariant;
  selected: boolean;
  onSelect: () => void;
  onReplace: () => void;
  selecting: boolean;
};

export function MenuVariantCard({
  menu,
  selected,
  onSelect,
  onReplace,
  selecting,
}: MenuVariantCardProps) {
  const [showIngredients, setShowIngredients] = useState(false);
  const meta = VARIANT_LABELS[menu.variant];

  return (
    <article
      className={`pa-card overflow-hidden transition ${
        selected
          ? "border-sage-400 ring-2 ring-sage-200"
          : "border-cream-border"
      }`}
    >
      <div className={`bg-gradient-to-r ${meta.accent} px-5 py-4 text-white`}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <span className="text-2xl" aria-hidden>
              {meta.emoji}
            </span>
            <h3 className="mt-1 text-xl font-bold">{menu.title}</h3>
            <p className="text-sm text-white/90">{menu.tagline}</p>
          </div>
          {selected ? (
            <span className="shrink-0 rounded-pill bg-white/25 px-3 py-1 text-xs font-bold">
              Выбрано
            </span>
          ) : null}
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium">
          <span className="rounded-pill bg-white/20 px-2.5 py-1">
            {menu.total_prep_minutes} мин готовки
          </span>
          {menu.estimated_daily_cost ? (
            <span className="rounded-pill bg-white/20 px-2.5 py-1">
              {menu.estimated_daily_cost}
            </span>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 p-5">
        <section className="rounded-control bg-sage-50/80 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-sage-800">
            Почему подходит
          </p>
          <p className="mt-2 text-sm leading-relaxed text-graphite-900">
            {menu.explanation}
          </p>
        </section>

        <section>
          <p className="text-xs font-bold uppercase tracking-wide text-graphite-500">
            Блюда на день
          </p>
          <ul className="mt-3 space-y-3">
            {menu.meals.map((meal, index) => (
              <li
                key={`${meal.meal_type}-${index}`}
                className="flex gap-3 rounded-control border border-cream-border bg-cream-deep/40 p-3"
              >
                <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-control bg-cream-surface text-[10px] font-bold leading-tight text-sage-700 shadow-soft">
                  <span>{meal.prep_time_minutes}</span>
                  <span>мин</span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-sage-700">
                    {MEAL_LABELS[meal.meal_type]}
                  </p>
                  <p className="font-semibold text-graphite-900">{meal.name}</p>
                  <p className="text-sm text-graphite-500">{meal.description}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <button
            type="button"
            onClick={() => setShowIngredients((value) => !value)}
            className="flex w-full items-center justify-between text-sm font-semibold text-graphite-700"
          >
            <span>Список ингредиентов ({menu.ingredients.length})</span>
            <span className="text-sage-600">{showIngredients ? "▲" : "▼"}</span>
          </button>
          {showIngredients ? (
            <ul className="mt-3 divide-y divide-cream-border rounded-control border border-cream-border">
              {menu.ingredients.map((item) => (
                <li
                  key={`${item.name}-${item.amount}`}
                  className="flex items-center justify-between gap-2 px-3 py-2.5 text-sm"
                >
                  <span className="font-medium text-graphite-800">{item.name}</span>
                  <span className="shrink-0 text-graphite-500">{item.amount}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={onSelect}
            disabled={selecting || selected}
            className="pa-btn-primary flex-1 py-3 text-sm disabled:opacity-50"
          >
            {selected ? "Выбрано" : selecting ? "Сохранение…" : "Выбрать"}
          </button>
          <button
            type="button"
            onClick={onReplace}
            disabled={selecting}
            className="pa-btn px-4 py-3 text-sm disabled:opacity-50"
          >
            Заменить блюдо
          </button>
        </div>
      </div>
    </article>
  );
}
