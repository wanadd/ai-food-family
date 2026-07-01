"use client";

/**
 * PLANAM V2 — Из того, что есть дома (/home/leftovers).
 * AI-подбор рецептов из pantry + отдельная секция «После готовки».
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { AiProcessLoadingV2 } from "@/components/planam-v2/ai/AiProcessLoadingV2";
import { V2Button, V2EmptyState } from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
} from "@/lib/cache/session-cache";
import {
  deleteMealLeftover,
  fetchMealLeftovers,
  updateMealLeftover,
  type MealLeftover,
} from "@/lib/meal-leftovers/api";
import { leftoverStatusLabel } from "@/lib/meal-leftovers/status";
import {
  discardCookingBatch,
  fetchStocksOverview,
  formatPreparedLeftoverAmount,
  type PreparedDish,
} from "@/lib/plan/leftovers-api";
import { cn } from "@/lib/planam/cn";
import { PLANAM_ROUTES, recipeDetailPath } from "@/lib/planam/routes";
import type { PantryItem } from "@/lib/pantry/types";
import { fetchRecipesFromPantry } from "@/lib/recipes/api";
import type { FromPantryRecipe } from "@/lib/recipes/types";

function daysUntil(iso: string | null): number | null {
  if (!iso) {
    return null;
  }
  const end = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.round((end.getTime() - today.getTime()) / 86400000);
}

export function LeftoversV2() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [leftovers, setLeftovers] = useState<MealLeftover[]>([]);
  const [preparedDishes, setPreparedDishes] = useState<PreparedDish[]>([]);
  const [recipes, setRecipes] = useState<FromPantryRecipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const pantryCount =
    getCached<{ items: PantryItem[]; active_count: number }>(
      cacheKey.pantry(mode),
    )?.active_count ?? null;

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [lo, pantryRecipes] = await Promise.all([
        fetchMealLeftovers(initData, mode),
        fetchRecipesFromPantry(initData, mode).catch(() => ({ items: [] })),
      ]);
      const stocks = await fetchStocksOverview(initData, mode, {
        include_prepared: true,
      }).catch(() => null);
      const prepared = stocks?.prepared_dishes ?? [];
      const preparedNames = new Set(
        prepared
          .map((dish) => normalizeDishName(dish.recipe_title))
          .filter(Boolean),
      );
      setPreparedDishes(prepared);
      setLeftovers(
        lo.filter(
          (l) =>
            (l.leftover_status === "active" || l.leftover_status === "frozen") &&
            !preparedNames.has(normalizeDishName(l.dish_name)),
        ),
      );
      setRecipes(pantryRecipes.items ?? []);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  async function markConsumed(item: MealLeftover) {
    if (!initData) {
      return;
    }
    setBusyId(item.id);
    try {
      await updateMealLeftover(initData, mode, item.id, {
        leftover_status: "consumed",
        portions_remaining: 0,
      });
      invalidateCache("menu-overview");
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function remove(item: MealLeftover) {
    if (!initData) {
      return;
    }
    setBusyId(item.id);
    try {
      await deleteMealLeftover(initData, mode, item.id);
      invalidateCache("menu-overview");
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function removePrepared(item: PreparedDish) {
    if (!initData || !item.can_manage) {
      return;
    }
    setBusyId(item.id);
    try {
      await discardCookingBatch(initData, mode, item.id);
      invalidateCache("menu-overview");
      invalidateCache("pantry");
      await load();
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return (
      <div className="px-4 pb-8 pt-4">
        <AiProcessLoadingV2 variant="pantry" />
      </div>
    );
  }

  if (!initData) {
    return (
      <div className="px-4 py-8">
        <V2EmptyState
          icon={<span aria-hidden>🍽</span>}
          title="Из того, что есть дома"
          description="Откройте ПланАм в Telegram — подберём рецепты из запасов и покажем остатки после готовки."
          actionLabel="На главную"
          onAction={() => router.push("/")}
        />
      </div>
    );
  }

  const expiring = leftovers.filter((l) => {
    const d = daysUntil(l.valid_until);
    return d != null && d <= 2;
  });
  const rest = leftovers.filter((l) => !expiring.includes(l));
  const empty = preparedDishes.length === 0 && leftovers.length === 0 && recipes.length === 0;

  if (empty) {
    return (
      <div className="px-4 py-8">
        <V2EmptyState
          icon={<span aria-hidden>📦</span>}
          title="Пока нет готовой еды"
          description="Добавьте продукты в запасы или сохраните приготовленное блюдо — и PLANAM подберёт рецепты."
          actionLabel="Открыть запасы"
          onAction={() => router.push(PLANAM_ROUTES.pantry)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-5 px-4 pb-8 pt-[max(0.75rem,env(safe-area-inset-top))]">
      <header>
        <h1 className="pa26-page-title">Из того, что есть дома</h1>
        <p className="pa26-micro mt-0.5 text-pa-muted">
          Готовая еда, остатки и блюда из ваших запасов
        </p>
        {pantryCount != null && pantryCount > 0 ? (
          <p className="pa26-caption mt-2 inline-flex rounded-pill border border-pa-border bg-pa-surface px-3 py-1 text-pa-muted">
            📦 В запасах: {pantryCount} прод.
          </p>
        ) : null}
      </header>

      {recipes.length > 0 ? (
        <section>
          <h2 className="pa26-section-title">PLANAM может приготовить</h2>
          <ul className="mt-2 space-y-2">
            {recipes.slice(0, 5).map((r) => (
              <li key={r.recipe_id}>
                <Link
                  href={recipeDetailPath(r.recipe_id)}
                  className="block rounded-card border border-pa-border bg-pa-surface px-4 py-3 shadow-soft transition hover:bg-sage-50/60 dark:shadow-none dark:hover:bg-pa-elevated/30"
                >
                  <p className="pa26-card-title">{r.title}</p>
                  <p className="pa26-caption mt-0.5 text-pa-muted">
                    Есть {r.have} из {r.total} ингредиентов
                  </p>
                  <p className="pa26-micro mt-1 font-semibold text-sage-700 dark:text-sage-300">
                    Открыть рецепт →
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <V2EmptyState
          title="Рецепты из запасов не подобрались"
          description="Добавьте больше продуктов в запасы — и попробуем снова."
          actionLabel="Открыть запасы"
          onAction={() => router.push(PLANAM_ROUTES.pantry)}
        />
      )}

      {preparedDishes.length > 0 || leftovers.length > 0 ? (
        <section className="space-y-3">
          <div>
            <h2 className="pa26-section-title">Готовая еда и остатки</h2>
            <p className="pa26-micro mt-0.5 text-pa-muted">
              Основной учёт — готовые блюда в запасах
            </p>
          </div>
          {preparedDishes.length > 0 ? (
            <div>
              <h3 className="pa26-micro font-semibold text-pa-muted">Готовая еда</h3>
              <ul className="mt-2 space-y-2">
                {preparedDishes.map((item) => (
                  <PreparedDishRowV2
                    key={item.id}
                    item={item}
                    busy={busyId === item.id}
                    onRemove={() => void removePrepared(item)}
                  />
                ))}
              </ul>
            </div>
          ) : null}
          {expiring.length > 0 ? (
            <div>
              <h3 className="pa26-micro font-semibold text-warm">Старые сохранённые порции</h3>
              <ul className="mt-2 space-y-2">
                {expiring.map((item) => (
                  <LeftoverRowV2
                    key={item.id}
                    item={item}
                    urgent
                    busy={busyId === item.id}
                    onConsume={() => void markConsumed(item)}
                    onRemove={() => void remove(item)}
                  />
                ))}
              </ul>
            </div>
          ) : null}
          {rest.length > 0 ? (
            <div>
              <h3 className="pa26-micro font-semibold text-pa-muted">Старые остатки</h3>
              <ul className="mt-2 space-y-2">
                {rest.map((item) => (
                  <LeftoverRowV2
                    key={item.id}
                    item={item}
                    busy={busyId === item.id}
                    onConsume={() => void markConsumed(item)}
                    onRemove={() => void remove(item)}
                  />
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function normalizeDishName(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase().replace(/\s+/g, " ");
}

function PreparedDishRowV2({
  item,
  busy,
  onRemove,
}: {
  item: PreparedDish;
  busy: boolean;
  onRemove: () => void;
}) {
  return (
    <li className="rounded-card border border-pa-border bg-pa-surface px-4 py-3">
      <p className="pa26-card-title">{item.recipe_title ?? "Готовое блюдо"}</p>
      <p className="pa26-caption text-pa-muted">
        {formatPreparedLeftoverAmount(
          item.remaining_servings,
          item.total_servings,
          item.serving_unit,
          item,
        )}
      </p>
      {item.can_manage ? (
        <div className="mt-2 flex gap-2">
          <V2Button variant="ghost" loading={busy} onClick={onRemove}>
            Убрать
          </V2Button>
        </div>
      ) : null}
    </li>
  );
}

function LeftoverRowV2({
  item,
  urgent = false,
  busy,
  onConsume,
  onRemove,
}: {
  item: MealLeftover;
  urgent?: boolean;
  busy: boolean;
  onConsume: () => void;
  onRemove: () => void;
}) {
  const days = daysUntil(item.valid_until);
  return (
    <li
      className={cn(
        "rounded-card border px-4 py-3",
        urgent ? "border-warm/40 bg-warm/5" : "border-pa-border bg-pa-surface",
      )}
    >
      <p className="pa26-card-title">{item.dish_name}</p>
      <p className="pa26-caption text-pa-muted">
        {item.portions_remaining} порц. · {leftoverStatusLabel(item.leftover_status)}
        {days != null ? ` · ${days} дн.` : ""}
      </p>
      <div className="mt-2 flex gap-2">
        <V2Button variant="secondary" loading={busy} onClick={onConsume}>
          Съели
        </V2Button>
        <V2Button variant="ghost" loading={busy} onClick={onRemove}>
          Убрать
        </V2Button>
      </div>
    </li>
  );
}
