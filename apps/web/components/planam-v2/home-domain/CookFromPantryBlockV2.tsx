"use client";

import Link from "next/link";

import { recipeDetailPath, PLANAM_ROUTES } from "@/lib/planam/routes";
import { withReturnTo } from "@/lib/navigation/return-to";
import type { FromPantryRecipe } from "@/lib/recipes/types";

type CookFromPantryBlockV2Props = {
  recipes: FromPantryRecipe[];
  loading?: boolean;
  error?: string | null;
  returnTo?: string;
};

export function CookFromPantryBlockV2({
  recipes,
  loading = false,
  error = null,
  returnTo = PLANAM_ROUTES.pantry,
}: CookFromPantryBlockV2Props) {
  const preview = recipes.slice(0, 3);
  const leftoversHref = withReturnTo(PLANAM_ROUTES.homeLeftovers, returnTo);

  if (loading) {
    return (
      <section
        className="rounded-card border border-pa-border bg-pa-surface px-4 py-3"
        data-testid="cook-from-pantry-block"
      >
        <p className="pa26-caption text-pa-muted">Подбираем рецепты из запасов…</p>
      </section>
    );
  }

  if (error) {
    return null;
  }

  if (preview.length === 0) {
    return (
      <section
        className="rounded-card border border-pa-border bg-pa-surface px-4 py-3"
        data-testid="cook-from-pantry-block"
      >
        <h2 className="pa26-section-title">Что приготовить из запасов</h2>
        <p className="pa26-caption mt-1 text-pa-muted">
          Добавьте продукты в запасы, и PLANAM покажет подходящие рецепты.
        </p>
      </section>
    );
  }

  return (
    <section data-testid="cook-from-pantry-block">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="pa26-section-title">Что приготовить из запасов</h2>
        <span className="pa26-micro font-semibold text-sage-700 dark:text-sage-300">
          {recipes.length} {recipes.length === 1 ? "рецепт" : recipes.length < 5 ? "рецепта" : "рецептов"}
        </span>
      </div>
      <ul className="mt-2 space-y-2">
        {preview.map((r) => (
          <li key={r.recipe_id}>
            <Link
              href={recipeDetailPath(r.recipe_id)}
              className="block rounded-card border border-pa-border bg-pa-surface px-4 py-3 shadow-soft transition hover:bg-sage-50/60 dark:shadow-none dark:hover:bg-pa-elevated/30"
            >
              <p className="pa26-card-title">{r.title}</p>
              <p
                className="pa26-caption mt-0.5 text-pa-muted"
                data-testid="cook-from-pantry-match"
              >
                Есть {r.have} из {r.total} ингредиентов
              </p>
            </Link>
          </li>
        ))}
      </ul>
      <Link
        href={leftoversHref}
        className="mt-3 flex w-full items-center justify-center rounded-control border border-pa-border bg-pa-surface px-4 py-3 pa26-caption font-semibold text-pa-foreground transition hover:bg-sage-50/60 dark:hover:bg-pa-elevated/30"
        data-testid="cook-from-pantry-show-all"
      >
        Показать рецепты
      </Link>
    </section>
  );
}
