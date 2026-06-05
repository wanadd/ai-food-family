"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import { invalidate as invalidateCache } from "@/lib/cache/session-cache";
import {
  deleteMealLeftover,
  fetchMealLeftovers,
  updateMealLeftover,
  type MealLeftover,
} from "@/lib/meal-leftovers/api";
import { leftoverStatusLabel } from "@/lib/meal-leftovers/status";
import { fetchRecipesFromPantry } from "@/lib/recipes/api";
import type { FromPantryRecipe } from "@/lib/recipes/types";
import { cn } from "@/lib/planam/cn";

function daysUntil(iso: string | null): number | null {
  if (!iso) {
    return null;
  }
  const end = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.round((end.getTime() - today.getTime()) / (86400000));
}

export function Leftovers2026() {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [leftovers, setLeftovers] = useState<MealLeftover[]>([]);
  const [recipes, setRecipes] = useState<FromPantryRecipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

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
      setLeftovers(
        lo.filter(
          (l) => l.leftover_status === "active" || l.leftover_status === "frozen",
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

  if (loading) {
    return (
      <div className="space-y-3 px-4 pb-8 pt-4">
        <Skeleton2026 variant="rect" className="h-24 w-full" />
        <Skeleton2026 variant="rect" className="h-24 w-full" />
      </div>
    );
  }

  if (!initData) {
    return (
      <div className="px-4 py-8">
        <EmptyState2026
          icon={<span aria-hidden>🍽</span>}
          title="Остатки дома"
          description="Откройте ПланАм в Telegram — здесь появятся блюда, которые остались после готовки."
          actionLabel="На главную"
          onAction={() => {
            if (typeof window !== "undefined") {
              window.location.href = "/";
            }
          }}
        />
      </div>
    );
  }

  const expiring = leftovers.filter((l) => {
    const d = daysUntil(l.valid_until);
    return d != null && d <= 2;
  });
  const rest = leftovers.filter((l) => !expiring.includes(l));
  const empty = leftovers.length === 0 && recipes.length === 0;

  if (empty) {
    return (
      <div className="px-4 py-8">
        <EmptyState2026
          icon={<span aria-hidden>🍽</span>}
          title="Остатков нет"
          description="После готовки отметьте, сколько порций осталось — они появятся здесь."
          actionLabel="К плану на сегодня"
          onAction={() => {
            if (typeof window !== "undefined") {
              window.location.href = "/plan/today";
            }
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-5 px-4 pb-8 pt-2">
      {expiring.length > 0 ? (
        <section>
          <h2 className="pa26-section-title text-warm">Скоро испортится</h2>
          <ul className="mt-2 space-y-2">
            {expiring.map((item) => (
              <LeftoverRow
                key={item.id}
                item={item}
                urgent
                busy={busyId === item.id}
                onConsume={() => void markConsumed(item)}
                onRemove={() => void remove(item)}
              />
            ))}
          </ul>
        </section>
      ) : null}

      {rest.length > 0 ? (
        <section>
          <h2 className="pa26-section-title">Что осталось</h2>
          <ul className="mt-2 space-y-2">
            {rest.map((item) => (
              <LeftoverRow
                key={item.id}
                item={item}
                busy={busyId === item.id}
                onConsume={() => void markConsumed(item)}
                onRemove={() => void remove(item)}
              />
            ))}
          </ul>
        </section>
      ) : null}

      {recipes.length > 0 ? (
        <section>
          <h2 className="pa26-section-title">Что приготовить из запасов</h2>
          <ul className="mt-2 space-y-2">
            {recipes.slice(0, 5).map((r) => (
              <li
                key={r.recipe_id}
                className="rounded-card border border-pa-border bg-pa-surface px-4 py-3"
              >
                <p className="pa26-card-title">{r.title}</p>
                <p className="pa26-caption text-pa-muted">
                  Есть {r.have} из {r.total} ингредиентов
                </p>
                <Link
                  href={`/plan/recipes/${r.recipe_id}`}
                  className="mt-2 inline-block pa26-micro font-semibold text-sage-700 dark:text-sage-300"
                >
                  Открыть рецепт →
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function LeftoverRow({
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
        urgent
          ? "border-warm/40 bg-warm/5"
          : "border-pa-border bg-pa-surface",
      )}
    >
      <p className="pa26-card-title">{item.dish_name}</p>
      <p className="pa26-caption text-pa-muted">
        {item.portions_remaining} порц. · {leftoverStatusLabel(item.leftover_status)}
        {days != null ? ` · ${days} дн.` : ""}
      </p>
      <div className="mt-2 flex gap-2">
        <Button2026 variant="secondary" loading={busy} onClick={onConsume}>
          Съели
        </Button2026>
        <Button2026 variant="ghost" loading={busy} onClick={onRemove}>
          Убрать
        </Button2026>
      </div>
    </li>
  );
}
