"use client";

import { useMemo, useState } from "react";

import { categoryMeta } from "@/lib/shopping/labels";
import type { ShoppingCategory } from "@/lib/shopping/types";

type CategoryPickerProps = {
  value: string;
  categories: ShoppingCategory[];
  extraSlugs?: string[];
  onChange: (slug: string) => void;
  allowCreate?: boolean;
  isFood?: boolean;
  onIsFoodChange?: (value: boolean) => void;
};

function slugify(name: string): string {
  return name.trim().toLowerCase().replace(/\s+/g, "_");
}

export function CategoryPicker({
  value,
  categories,
  extraSlugs = [],
  onChange,
  allowCreate = false,
  isFood = true,
  onIsFoodChange,
}: CategoryPickerProps) {
  const [open, setOpen] = useState(false);
  const [customName, setCustomName] = useState("");

  const options = useMemo(() => {
    const slugs = new Set<string>();
    for (const c of categories) slugs.add(c.slug);
    for (const s of extraSlugs) if (s) slugs.add(s);
    if (!slugs.size) slugs.add("продукты");
    return Array.from(slugs).map((slug) => ({
      slug,
      ...categoryMeta(slug, categories),
    }));
  }, [categories, extraSlugs]);

  const selectedLabel = value
    ? categoryMeta(value, categories).label
    : "Выберите категорию";

  const trimmedCustom = customName.trim();
  const customSlug = trimmedCustom ? slugify(trimmedCustom) : "";
  const customExists = options.some(
    (o) => o.slug === customSlug || o.label.toLowerCase() === trimmedCustom.toLowerCase(),
  );

  return (
    <div className="relative">
      <span className="text-xs font-semibold text-stone-500">Категория</span>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="mt-1 flex w-full items-center justify-between rounded-lg border border-stone-200 bg-white px-3 py-2.5 text-left text-sm text-stone-900"
      >
        <span>{selectedLabel}</span>
        <span className="text-stone-400" aria-hidden>
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ? (
        <div className="mt-2 max-h-48 overflow-y-auto rounded-xl border border-stone-200 bg-white shadow-lg">
          {options.map((opt) => (
            <button
              key={opt.slug}
              type="button"
              onClick={() => {
                onChange(opt.slug);
                setOpen(false);
              }}
              className={`flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm hover:bg-stone-50 ${
                value === opt.slug ? "bg-emerald-50 font-semibold text-emerald-900" : ""
              }`}
            >
              <span aria-hidden>{opt.emoji}</span>
              {opt.label}
            </button>
          ))}
          {allowCreate ? (
            <div className="border-t border-stone-100 p-3">
              <p className="text-xs font-semibold text-stone-600">Своя категория</p>
              <input
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="Подарки, хозтовары…"
                className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm"
              />
              {trimmedCustom && !customExists ? (
                <>
                  {onIsFoodChange ? (
                    <label className="mt-2 flex items-center gap-2 text-xs text-stone-700">
                      <input
                        type="checkbox"
                        checked={isFood}
                        onChange={(e) => onIsFoodChange(e.target.checked)}
                        className="h-4 w-4 rounded"
                      />
                      Это продукты (попадут в запасы)
                    </label>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => {
                      onChange(customSlug);
                      setOpen(false);
                      setCustomName("");
                    }}
                    className="mt-2 w-full rounded-lg bg-emerald-600 py-2 text-xs font-semibold text-white"
                  >
                    Использовать «{trimmedCustom}»
                  </button>
                </>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
