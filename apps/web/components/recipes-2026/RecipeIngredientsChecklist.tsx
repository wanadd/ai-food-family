"use client";

import { useState } from "react";

import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { formatIngredientAmount } from "@/lib/recipes/ingredient-amount";
import {
  buildPantryNameIndex,
  getIngredientPantryStatus,
  type IngredientPantryStatus,
} from "@/lib/pantry/pantry-ingredient-match";
import type { RecipeIngredient } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";

type RecipeIngredientsChecklistProps = {
  ingredients: RecipeIngredient[];
  storageKey?: string;
  pantryNames?: string[] | null;
};

const STATUS_LABEL: Record<Exclude<IngredientPantryStatus, "unknown">, string> = {
  home: "Есть дома",
  buy: "Купить",
};

function statusIcon(status: IngredientPantryStatus): string {
  if (status === "home") {
    return "✓";
  }
  if (status === "buy") {
    return "□";
  }
  return "·";
}

export function RecipeIngredientsChecklist({
  ingredients,
  storageKey,
  pantryNames = null,
}: RecipeIngredientsChecklistProps) {
  const pantryIndex =
    pantryNames === null ? null : buildPantryNameIndex(pantryNames);
  const showPantryStatus = pantryNames !== null;

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
      {showPantryStatus ? (
        <p className="border-b border-pa-border px-4 py-2 pa26-micro text-pa-muted">
          ✓ Есть дома · □ Купить
        </p>
      ) : null}
      <ul className="divide-y divide-pa-border">
        {ingredients.map((ing, index) => {
          const done = checked.has(index);
          const pantryStatus = getIngredientPantryStatus(ing.name, pantryIndex);
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
                {showPantryStatus && pantryStatus !== "unknown" ? (
                  <span
                    className={cn(
                      "shrink-0 pa26-micro font-semibold",
                      pantryStatus === "home"
                        ? "text-sage-700 dark:text-sage-300"
                        : "text-warm",
                    )}
                    data-testid={`recipe-ingredient-pantry-${pantryStatus}`}
                  >
                    {statusIcon(pantryStatus)} {STATUS_LABEL[pantryStatus]}
                  </span>
                ) : null}
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
