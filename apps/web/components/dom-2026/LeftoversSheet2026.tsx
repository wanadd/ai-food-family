"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
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

type LeftoversSheet2026Props = {
  open: boolean;
  onClose: () => void;
};

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

export function LeftoversSheet2026({ open, onClose }: LeftoversSheet2026Props) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [leftovers, setLeftovers] = useState<MealLeftover[]>([]);
  const [recipes, setRecipes] = useState<FromPantryRecipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      return;
    }
    setLoading(true);
    try {
      const [lo, pantryRecipes] = await Promise.all([
        fetchMealLeftovers(initData, mode),
        fetchRecipesFromPantry(initData, mode).catch(() => ({ items: [] })),
      ]);
      setLeftovers(lo.filter((l) => l.leftover_status === "active" || l.leftover_status === "frozen"));
      setRecipes(pantryRecipes.items ?? []);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (open) {
      void load();
    }
  }, [open, load]);

  const expiring = leftovers.filter((l) => {
    const d = daysUntil(l.valid_until);
    return d != null && d <= 2;
  });
  const rest = leftovers.filter((l) => !expiring.includes(l));

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

  const empty = !loading && leftovers.length === 0 && recipes.length === 0;

  return (
    <BottomSheet2026 open={open} title="Остатки дома" onClose={onClose}>
      {loading ? (
        <p className="pa26-body text-pa-muted">Загружаем…</p>
      ) : empty ? (
        <EmptyState2026
          title="Остатков нет"
          description="После готовки отметьте, сколько порций осталось — они появятся здесь."
          actionLabel="Закрыть"
          onAction={onClose}
        />
      ) : (
        <div className="space-y-5 pb-2">
          {expiring.length > 0 ? (
            <section>
              <h3 className="pa26-caption font-semibold text-warm">Скоро испортится</h3>
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
              <h3 className="pa26-caption font-semibold text-pa-muted">Что осталось</h3>
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
              <h3 className="pa26-caption font-semibold text-pa-muted">
                Что приготовить из запасов
              </h3>
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
                      onClick={onClose}
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
      )}
    </BottomSheet2026>
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
