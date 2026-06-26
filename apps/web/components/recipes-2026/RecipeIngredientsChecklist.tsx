"use client";

import { useState } from "react";

import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { formatIngredientAmount } from "@/lib/recipes/ingredient-amount";
import type { RecipeIngredient } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";

type RecipeIngredientsChecklistProps = {
  ingredients: RecipeIngredient[];
  storageKey?: string;
};

export function RecipeIngredientsChecklist({
  ingredients,
  storageKey,
}: RecipeIngredientsChecklistProps) {
  const [checked, setChecked] = useState<Set<number>>(() => {
    if (!storageKey || typeof window === "undefined") {
      return new Set();
    }
    try {
      const raw = sessionStorage.getItem(storageKey);
      if (!raw) return new Set();
      return new Set(JSON.parse(raw) as number[]);
    } catch {
      return new Set();
    }
  });

  function toggle(index: number) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      if (storageKey && typeof window !== "undefined") {
        sessionStorage.setItem(storageKey, JSON.stringify(Array.from(next)));
      }
      return next;
    });
  }

  if (ingredients.length === 0) {
    return (
      <Card2026 padding="md">
        <p className="pa26-body text-pa-muted">Список ингредиентов появится позже.</p>
      </Card2026>
    );
  }

  return (
    <Card2026 padding="none" data-testid="recipe-ingredients-checklist">
      <ul className="divide-y divide-pa-border">
        {ingredients.map((ing, index) => {
          const done = checked.has(index);
          return (
            <li key={`${ing.name}-${index}`}>
              <label
                className={cn(
                  "flex cursor-pointer items-start gap-3 px-4 py-3 transition",
                  done && "bg-sage-50/50 dark:bg-sage-900/10",
                )}
              >
                <input
                  type="checkbox"
                  checked={done}
                  onChange={() => toggle(index)}
                  className="mt-1 size-4 rounded border-pa-border text-sage-600"
                />
                <span
                  className={cn(
                    "min-w-0 flex-1 pa26-body",
                    done && "text-pa-muted line-through",
                  )}
                >
                  {ing.name}
                </span>
                <span className="shrink-0 pa26-caption text-pa-muted">
                  {formatIngredientAmount(ing)}
                </span>
              </label>
            </li>
          );
        })}
      </ul>
    </Card2026>
  );
}
