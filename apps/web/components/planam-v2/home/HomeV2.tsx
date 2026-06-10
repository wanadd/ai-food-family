"use client";

/**
 * PLANAM V2 — Home: «что мне сделать сейчас».
 * Greeting → Hero → 3 статуса → «Дальше сегодня» → контекст дня. Не больше.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MealOutcomeSheet2026 } from "@/components/dom-2026";
import { HomeHeroV2 } from "@/components/planam-v2/home/HomeHeroV2";
import { V2AiTip, V2EmptyState } from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import {
  enrichTodayMeals,
  type Home2026TodayMeal,
} from "@/lib/home/home-2026-data";
import {
  buildHomeDayContext,
  shouldShowAiTip,
} from "@/lib/home/home-day-context";
import {
  cleanMealTitle,
  formatPlanAmDate,
  formatPlanAmGreeting,
  menuStatusLabel,
  pantryStatusLabel,
  resolvePlanAmHeroState,
  shoppingStatusLabel,
} from "@/lib/home/planam-hero-2026";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import type { MenuOverview } from "@/lib/menu/overview-types";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import { cn } from "@/lib/planam/cn";

type LoadState = "loading" | "ready" | "error";

export function HomeV2() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData, user } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const cacheK = cacheKey.menuOverview(mode);
  const primed = initData ? getCached<MenuOverview>(cacheK) : null;

  const [overview, setOverview] = useState<MenuOverview | null>(primed);
  const [loadState, setLoadState] = useState<LoadState>(() =>
    primed ? "ready" : "loading",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [mealOutcomeOpen, setMealOutcomeOpen] = useState(false);

  const load = useCallback(
    async (force = false) => {
      if (!initData || modeLoading) {
        return;
      }
      const cached = getCached<MenuOverview>(cacheK);
      if (!force && cached) {
        setOverview(cached);
        setLoadState("ready");
        return;
      }
      setLoadState("loading");
      setErrorMessage(null);
      try {
        const data = await fetchMenuOverview(initData, mode);
        setCached(cacheK, data);
        setOverview(data);
        setLoadState("ready");
      } catch (err) {
        setLoadState("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Не удалось загрузить данные",
        );
      }
    },
    [initData, mode, modeLoading, cacheK],
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (searchParams.get("meal_outcome") === "1") {
      setMealOutcomeOpen(true);
      router.replace("/", { scroll: false });
    }
  }, [searchParams, router]);

  const hasMenu = Boolean(overview?.plan_summary.has_selected_menu);
  const meals = useMemo(
    () => (overview ? enrichTodayMeals(overview) : []),
    [overview],
  );
  const heroState = useMemo(
    () => resolvePlanAmHeroState(overview, meals, hasMenu),
    [overview, meals, hasMenu],
  );

  const loading = loadState === "loading" || modeLoading;
  const greeting = useMemo(
    () => formatPlanAmGreeting(user?.first_name),
    [user?.first_name],
  );
  const dateLabel = useMemo(() => formatPlanAmDate(), []);

  const showAiTip = shouldShowAiTip(overview);
  const aiTipText = overview?.nutritionist_advice.body?.trim() ?? "";
  const dayContext = useMemo(() => buildHomeDayContext(overview), [overview]);

  const nextMeals = useMemo(() => {
    if (heroState.variant !== "meal" || !heroState.meal) {
      return [];
    }
    const heroType = heroState.meal.meal_type;
    const order = ["breakfast", "lunch", "dinner", "snack"];
    return meals
      .filter((m) => m.meal_type !== heroType)
      .sort((a, b) => order.indexOf(a.meal_type) - order.indexOf(b.meal_type))
      .slice(0, 2);
  }, [heroState, meals]);

  if (loadState === "error") {
    return (
      <div className="pb-2">
        <Greeting greeting={greeting} dateLabel={dateLabel} />
        <V2EmptyState
          title="Не удалось обновить день"
          description={errorMessage ?? "Проверьте сеть и попробуйте снова."}
          actionLabel="Обновить"
          onAction={() => {
            invalidateCache(cacheK);
            void load(true);
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-0 pb-2">
      <Greeting greeting={greeting} dateLabel={dateLabel} />

      <HomeHeroV2
        loading={loading}
        state={heroState}
        onChanged={() => {
          invalidateCache(cacheK);
          void load(true);
        }}
      />

      <section className="px-4 pt-2" aria-label="Статусы дня">
        <ul className="grid grid-cols-3 gap-2">
          <StatusCard
            emoji="🛒"
            label="Купить"
            value={loading ? "…" : shoppingStatusLabel(overview?.shopping_unchecked_count ?? 0)}
            onClick={() => router.push(PLANAM_ROUTES.shopping)}
          />
          <StatusCard
            emoji="📦"
            label="Запасы"
            value={loading ? "…" : pantryStatusLabel(overview)}
            onClick={() => router.push(PLANAM_ROUTES.pantry)}
          />
          <StatusCard
            emoji="🍽"
            label="Меню"
            value={loading ? "…" : menuStatusLabel(overview)}
            onClick={() => router.push(PLANAM_ROUTES.planToday)}
          />
        </ul>
      </section>

      {!loading && nextMeals.length > 0 ? (
        <section className="px-4 pt-3" aria-label="Дальше сегодня">
          <h2 className="pa26-section-title">Дальше сегодня</h2>
          <div className="mt-2 space-y-2">
            {nextMeals.map((m) => (
              <NextMealRow
                key={m.meal_type}
                meal={m}
                onClick={() =>
                  router.push(
                    `${PLANAM_ROUTES.planToday}?meal=${encodeURIComponent(m.meal_type)}`,
                  )
                }
              />
            ))}
          </div>
        </section>
      ) : null}

      {!loading ? (
        <section className="px-4 pt-3" aria-label="Контекст дня">
          {showAiTip && aiTipText ? (
            <V2AiTip
              title="Совет PLANAM"
              tone="ai"
              text={aiTipText}
              onClick={() => router.push(PLANAM_ROUTES.wellness)}
            />
          ) : (
            <V2AiTip
              title={dayContext.title}
              text={dayContext.text}
              onClick={() => router.push(PLANAM_ROUTES.planToday)}
            />
          )}
        </section>
      ) : null}

      <MealOutcomeSheet2026
        open={mealOutcomeOpen}
        onClose={() => setMealOutcomeOpen(false)}
        onSuccess={() => {
          invalidateCache(cacheK);
          void load(true);
        }}
      />
    </div>
  );
}

function Greeting({ greeting, dateLabel }: { greeting: string; dateLabel: string }) {
  return (
    <header className="px-4 pb-0.5 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <h1 className="pa26-page-title truncate">{greeting}</h1>
      <p className="pa26-micro mt-0.5 capitalize text-pa-muted">{dateLabel}</p>
    </header>
  );
}

function NextMealRow({
  meal,
  onClick,
}: {
  meal: Home2026TodayMeal;
  onClick: () => void;
}) {
  const metaParts: string[] = [];
  if (meal.prep_time_minutes != null && meal.prep_time_minutes > 0) {
    metaParts.push(`${meal.prep_time_minutes} мин`);
  }
  if (meal.calories != null && meal.calories > 0) {
    metaParts.push(`${Math.round(meal.calories)} ккал`);
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full min-h-[52px] items-center gap-3 rounded-card border border-pa-border",
        "bg-pa-surface px-3.5 py-2.5 text-left shadow-soft transition active:scale-[0.99] dark:shadow-none",
      )}
    >
      <div className="min-w-0 flex-1">
        <p className="pa26-micro text-pa-muted">{meal.label}</p>
        <p className="pa26-card-title line-clamp-1">{cleanMealTitle(meal.name)}</p>
      </div>
      {metaParts.length ? (
        <span className="pa26-micro shrink-0 text-pa-muted">
          {metaParts.join(" · ")}
        </span>
      ) : null}
    </button>
  );
}

function StatusCard({
  emoji,
  label,
  value,
  onClick,
}: {
  emoji: string;
  label: string;
  value: string;
  onClick: () => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "flex h-full min-h-[72px] w-full flex-col items-start justify-between",
          "rounded-card border border-pa-border bg-pa-surface p-2.5 text-left shadow-soft",
          "transition active:scale-[0.99] dark:shadow-none dark:hover:bg-pa-elevated/30",
        )}
      >
        <span className="text-base" aria-hidden>
          {emoji}
        </span>
        <span className="min-w-0">
          <span className="pa26-micro block font-semibold text-pa-foreground">
            {label}
          </span>
          <span className="pa26-micro mt-0.5 block truncate text-pa-muted">
            {value}
          </span>
        </span>
      </button>
    </li>
  );
}
