"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { SkeletonCard, SkeletonList } from "@/components/ui/Skeleton";
import { ProtectedScreenFallback } from "@/components/auth/ProtectedScreenFallback";
import { useProtectedScreen } from "@/lib/use-protected-screen";
import {
  cacheKey,
  fetchOrCache,
  getCached,
  invalidate as invalidateCache,
} from "@/lib/cache/session-cache";
import {
  isNutritionProfileComplete,
} from "@/lib/profile/nutrition-summary";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { MenuVariant } from "@/lib/menu/types";
import { fetchPantry } from "@/lib/pantry/api";
import type { PantryList } from "@/lib/pantry/types";
import { NutritionistAdviceCard } from "@/components/nutritionist/NutritionistAdviceCard";
import { WaterIntakePanel } from "@/components/nutritionist/WaterIntakePanel";
import { buildAdviceWhy } from "@/lib/nutritionist/advice-why";
import {
  completeDeferredAdvice,
  dismissDeferredAdvicePermanently,
  listDeferredAdvice,
  listSuppressedAdviceTitles,
  migrateLocalDeferredAdvice,
  returnDeferredAdvice,
  type DeferredAdvice,
} from "@/lib/nutritionist/advice-deferred";
import { buildDailyStatus } from "@/lib/nutritionist/daily-status";
import { buildGoalProgressCard } from "@/lib/nutritionist/goal-progress";
import { pickMainAdvice } from "@/lib/nutritionist/main-advice";
import { withReturnTo } from "@/lib/navigation/return-to";
import { fetchProgressOverview } from "@/lib/progress/api";
import type { ProgressOverview } from "@/lib/progress/types";

const HEALTH_RETURN = "/health/today";

export function HealthTodayView() {
  const { initData, state: authState } = useProtectedScreen();
  const { mode, loading: modeLoading } = useAppMode();

  const cachedProfile = initData
    ? getCached<NutritionProfileData>(cacheKey.nutritionProfile())
    : null;
  const cachedSelected = initData
    ? getCached<{ menu: MenuVariant | null }>(cacheKey.selectedMenu(mode))
    : null;
  const cachedPantry = initData
    ? getCached<PantryList>(cacheKey.pantry(mode))
    : null;
  const cachedProgress = initData
    ? getCached<ProgressOverview>(cacheKey.progressOverview(mode))
    : null;
  const cacheReady =
    cachedProfile != null &&
    cachedSelected != null &&
    cachedPantry != null &&
    cachedProgress != null;

  const [loading, setLoading] = useState(!cacheReady);
  const [profile, setProfile] = useState<NutritionProfileData | null>(
    cachedProfile,
  );
  const [menu, setMenu] = useState<MenuVariant | null>(
    cachedSelected?.menu ?? null,
  );
  const [pantry, setPantry] = useState<PantryList | null>(cachedPantry);
  const [progress, setProgress] = useState<ProgressOverview | null>(
    cachedProgress,
  );
  const [deferredAdvice, setDeferredAdvice] = useState<DeferredAdvice[]>([]);
  const [suppressedTitles, setSuppressedTitles] = useState<string[]>([]);

  const refreshDeferred = useCallback(async () => {
    if (!initData) return;
    const [items, suppressed] = await Promise.all([
      listDeferredAdvice(initData, mode),
      listSuppressedAdviceTitles(initData, mode),
    ]);
    setDeferredAdvice(items);
    setSuppressedTitles(suppressed);
  }, [initData, mode]);

  const load = useCallback(async () => {
    if (!initData) return;
    const hasAny =
      getCached(cacheKey.nutritionProfile()) != null ||
      getCached(cacheKey.selectedMenu(mode)) != null ||
      getCached(cacheKey.pantry(mode)) != null ||
      getCached(cacheKey.progressOverview(mode)) != null;
    if (!hasAny) setLoading(true);
    try {
      const [nutrition, selected, pantryList, progressData] = await Promise.all([
        fetchOrCache(cacheKey.nutritionProfile(), () =>
          fetchNutritionProfile(initData),
        ).catch(() => null),
        fetchOrCache(cacheKey.selectedMenu(mode), () =>
          fetchSelectedMenu(initData, mode),
        ).catch(() => null),
        fetchOrCache(cacheKey.pantry(mode), () =>
          fetchPantry(initData, mode),
        ).catch(() => null),
        fetchOrCache(cacheKey.progressOverview(mode), () =>
          fetchProgressOverview(initData, mode),
        ).catch(() => null),
      ]);
      setProfile(nutrition);
      setMenu(selected?.menu ?? null);
      setPantry(pantryList);
      setProgress(progressData);
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading || authState !== "ready") return;
    void load();
  }, [load, modeLoading, authState]);

  useEffect(() => {
    if (!initData || authState !== "ready") return;
    void (async () => {
      await migrateLocalDeferredAdvice(initData, mode);
      await refreshDeferred();
    })();
  }, [initData, mode, authState, refreshDeferred]);

  const profileComplete = isNutritionProfileComplete(profile);
  const daily = buildDailyStatus({ progress, menu, mode });
  const goalCard = buildGoalProgressCard(profile, progress);
  const advice = pickMainAdvice({
    profile,
    menu,
    pantry,
    pantryActiveCount: pantry?.active_count ?? 0,
  });
  const adviceWhy = buildAdviceWhy(profile);
  const adviceHiddenByDefer =
    deferredAdvice.some((d) => d.title === advice.title) ||
    suppressedTitles.includes(advice.title);

  const hasMoreContent =
    goalCard.percent != null ||
    (initData && !adviceHiddenByDefer) ||
    (profileComplete && adviceWhy.length > 0) ||
    deferredAdvice.length > 0;

  if (authState !== "ready") {
    return (
      <ProtectedScreenFallback
        loadingMessage="Загрузка…"
        telegramMessage="Здоровье доступно в Telegram Mini App."
      />
    );
  }

  if (loading || modeLoading) {
    return (
      <ScreenLayout
        title="Сегодня"
        back={{ label: "Здоровье", href: "/health" }}
        contentClassName="space-y-3 pb-24"
      >
        <SkeletonCard titleWidth="w-1/2" lines={3} withButton />
        <SkeletonList count={1} />
      </ScreenLayout>
    );
  }

  return (
    <ScreenLayout
      title="Сегодня"
      subtitle="Питание и самочувствие"
      back={{ label: "Здоровье", href: "/health" }}
      contentClassName="space-y-3"
    >
      {!profileComplete ? (
        <Link
          href={withReturnTo("/profile/nutrition", HEALTH_RETURN)}
          className="block text-sm text-sage-700"
        >
          Дополнить профиль питания →
        </Link>
      ) : null}

      <section className="pa-card border-sage-200 bg-sage-50/30 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
          Сегодня
        </p>
        {daily.todoLine ? (
          <p className="mt-2 text-lg font-bold text-graphite-900">
            Осталось: {daily.todoLine}
          </p>
        ) : (
          <p className="mt-2 text-lg font-bold text-graphite-900">
            На сегодня всё учтено
          </p>
        )}
        <p className="mt-2 text-sm text-graphite-600">{daily.actual.calories}</p>
        <p className="text-sm text-graphite-500">{daily.plan.calories}</p>

        {initData ? (
          <div className="mt-4">
            <WaterIntakePanel
              onUpdated={() => {
                invalidateCache("progress-overview");
                void load();
              }}
            />
          </div>
        ) : null}

        <details className="mt-4 text-sm text-graphite-600">
          <summary className="cursor-pointer text-xs font-semibold text-sage-700">
            КБЖУ подробнее
          </summary>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs font-semibold uppercase text-graphite-500">
                {daily.planTitle}
              </p>
              <ul className="mt-1 space-y-0.5 text-sm">
                <li>{daily.plan.protein}</li>
                <li>{daily.plan.fat}</li>
                <li>{daily.plan.carbs}</li>
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-sage-800">
                {daily.actualTitle}
              </p>
              <ul className="mt-1 space-y-0.5 text-sm">
                <li>{daily.actual.protein}</li>
                <li>{daily.actual.fat}</li>
                <li>{daily.actual.carbs}</li>
                <li>{daily.actual.water}</li>
              </ul>
            </div>
          </div>
          {menu ? (
            <Link
              href="/menu/current"
              className="mt-2 inline-block text-xs font-semibold text-sage-700"
            >
              Отметить, где поели →
            </Link>
          ) : null}
        </details>

        <Link
          href="/health/chat"
          className="pa-btn-primary mt-4 flex min-h-[48px] w-full items-center justify-center py-3 text-sm"
        >
          Спросить ПланАм
        </Link>
      </section>

      {hasMoreContent ? (
        <details className="pa-card p-4">
          <summary className="cursor-pointer text-sm font-semibold text-graphite-900">
            Ещё — цель, советы, отложенное
          </summary>
          <div className="mt-4 space-y-4">
            {goalCard.percent != null ? (
              <div>
                <p className="text-xs font-semibold uppercase text-graphite-400">
                  Цель
                </p>
                <div className="mt-2 flex justify-between text-xs text-graphite-600">
                  <span>
                    {goalCard.currentWeight} → {goalCard.targetWeight}
                  </span>
                  <span className="font-bold text-sage-800">{goalCard.percent}%</span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-pill bg-cream-deep">
                  <div
                    className="h-full rounded-pill bg-sage-500"
                    style={{ width: `${goalCard.percent}%` }}
                  />
                </div>
                <Link
                  href={withReturnTo("/progress", HEALTH_RETURN)}
                  className="mt-2 inline-block text-xs font-semibold text-sage-700"
                >
                  Подробнее в прогрессе →
                </Link>
              </div>
            ) : null}

            {initData && !adviceHiddenByDefer ? (
              <NutritionistAdviceCard
                advice={advice}
                initData={initData}
                mode={mode}
                onDeferred={refreshDeferred}
              />
            ) : null}

            {profileComplete && adviceWhy.length > 0 ? (
              <div>
                <p className="text-xs font-semibold uppercase text-graphite-500">
                  Почему ПланАм советует это
                </p>
                <ul className="mt-2 space-y-1 text-sm text-graphite-700">
                  {adviceWhy.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {deferredAdvice.length > 0 ? (
              <div>
                <p className="text-sm font-bold text-graphite-900">
                  Отложенные рекомендации
                </p>
                <ul className="mt-3 space-y-3">
                  {deferredAdvice.map((item) => (
                    <li key={item.id} className="rounded-control bg-cream-deep/40 p-3">
                      <p className="font-semibold text-graphite-900">{item.title}</p>
                      <p className="mt-1 text-xs text-graphite-600">{item.body}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            if (!initData) return;
                            void completeDeferredAdvice(initData, mode, item.id).then(
                              refreshDeferred,
                            );
                          }}
                          className="pa-btn-primary px-3 py-1.5 text-xs"
                        >
                          Выполнить
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (!initData) return;
                            void returnDeferredAdvice(initData, mode, item.id).then(
                              refreshDeferred,
                            );
                          }}
                          className="pa-btn px-3 py-1.5 text-xs"
                        >
                          Вернуть
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (!initData) return;
                            void dismissDeferredAdvicePermanently(
                              initData,
                              mode,
                              item.id,
                            ).then(refreshDeferred);
                          }}
                          className="text-xs font-semibold text-red-600"
                        >
                          Удалить
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </details>
      ) : null}
    </ScreenLayout>
  );
}
