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
      className={`overflow-hidden rounded-2xl border bg-white shadow-sm transition ${
        selected
          ? "border-emerald-400 ring-2 ring-emerald-200"
          : "border-stone-200"
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
            <span className="shrink-0 rounded-full bg-white/25 px-3 py-1 text-xs font-bold">
              Выбрано
            </span>
          ) : null}
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium">
          <span className="rounded-full bg-white/20 px-2.5 py-1">
            {menu.total_prep_minutes} мин готовки
          </span>
          {menu.estimated_daily_cost ? (
            <span className="rounded-full bg-white/20 px-2.5 py-1">
              {menu.estimated_daily_cost}
            </span>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 p-5">
        <section className="rounded-xl bg-emerald-50/80 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">
            Почему подходит
          </p>
          <p className="mt-2 text-sm leading-relaxed text-emerald-950">
            {menu.explanation}
          </p>
        </section>

        <section>
          <p className="text-xs font-bold uppercase tracking-wide text-stone-500">
            Блюда на день
          </p>
          <ul className="mt-3 space-y-3">
            {menu.meals.map((meal, index) => (
              <li
                key={`${meal.meal_type}-${index}`}
                className="flex gap-3 rounded-xl border border-stone-100 bg-stone-50/80 p-3"
              >
                <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-lg bg-white text-[10px] font-bold leading-tight text-emerald-700 shadow-sm">
                  <span>{meal.prep_time_minutes}</span>
                  <span>мин</span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-emerald-700">
                    {MEAL_LABELS[meal.meal_type]}
                  </p>
                  <p className="font-semibold text-stone-900">{meal.name}</p>
                  <p className="text-sm text-stone-500">{meal.description}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <button
            type="button"
            onClick={() => setShowIngredients((value) => !value)}
            className="flex w-full items-center justify-between text-sm font-semibold text-stone-700"
          >
            <span>Список ингредиентов ({menu.ingredients.length})</span>
            <span className="text-emerald-600">{showIngredients ? "▲" : "▼"}</span>
          </button>
          {showIngredients ? (
            <ul className="mt-3 divide-y divide-stone-100 rounded-xl border border-stone-100">
              {menu.ingredients.map((item) => (
                <li
                  key={`${item.name}-${item.amount}`}
                  className="flex items-center justify-between gap-2 px-3 py-2.5 text-sm"
                >
                  <span className="font-medium text-stone-800">{item.name}</span>
                  <span className="shrink-0 text-stone-500">{item.amount}</span>
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
            className="flex-1 rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50"
          >
            {selected ? "Выбрано" : selecting ? "Сохранение…" : "Выбрать"}
          </button>
          <button
            type="button"
            onClick={onReplace}
            disabled={selecting}
            className="rounded-xl border border-stone-200 px-4 py-3 text-sm font-semibold text-stone-700 transition hover:bg-stone-50 disabled:opacity-50"
          >
            Заменить блюдо
          </button>
        </div>
      </div>
    </article>
  );
}
