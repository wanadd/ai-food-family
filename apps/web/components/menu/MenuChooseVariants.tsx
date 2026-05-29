"use client";

import { VARIANT_LABELS } from "@/lib/menu/labels";
import { getMealRows } from "@/lib/home/plan-summary";
import type { MenuVariant, MenuVariantType } from "@/lib/menu/types";

type MenuChooseVariantsProps = {
  menus: MenuVariant[];
  selecting: boolean;
  onSelect: (menu: MenuVariant) => void;
  onPreview: (menu: MenuVariant) => void;
};

export function MenuChooseVariants({
  menus,
  selecting,
  onSelect,
  onPreview,
}: MenuChooseVariantsProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-graphite-600">
        Выберите один вариант — он станет активным, список покупок обновится
        автоматически.
      </p>
      {menus.map((menu) => {
        const meta = VARIANT_LABELS[menu.variant as MenuVariantType];
        const rows = getMealRows(menu);
        return (
          <article key={menu.variant} className="pa-card p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl" aria-hidden>
                {meta?.emoji ?? "🍽"}
              </span>
              <div className="min-w-0 flex-1">
                <h3 className="font-bold text-graphite-900">{menu.title}</h3>
                <p className="mt-0.5 text-sm text-graphite-500">{menu.tagline}</p>
                <ul className="mt-2 space-y-1">
                  {rows.map((row) => (
                    <li
                      key={row.label}
                      className="flex justify-between gap-2 text-sm"
                    >
                      <span className="text-graphite-500">{row.label}</span>
                      <span className="truncate font-medium text-graphite-800">
                        {row.name}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={() => onSelect(menu)}
                disabled={selecting}
                className="pa-btn-primary min-h-[40px] flex-1 py-2.5 text-sm disabled:opacity-50"
              >
                {selecting ? "Сохранение…" : "Выбрать"}
              </button>
              <button
                type="button"
                onClick={() => onPreview(menu)}
                className="pa-btn px-3 py-2.5 text-sm"
              >
                Подробнее
              </button>
            </div>
          </article>
        );
      })}
    </div>
  );
}
