"use client";

/**
 * PLANAM V2 — Здоровье (/wellness).
 * Reference order: Header → Metrics (progress bars) → AI tip →
 * Recommendations → Chat CTA. Вода — быстрый трекер под метриками.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { AiNutritionChatSheet } from "@/components/planam-v2/wellness/AiNutritionChatSheet";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import {
  V2AiTip,
  V2Button,
  V2Card,
  V2EmptyState,
  V2ProgressBar,
} from "@/components/planam-v2/ui/V2Primitives";
import { WaterIntake2026 } from "@/components/wellness-2026/WaterIntake2026";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { buildActiveMenuDayState, sumMealNutrition } from "@/lib/household/active-menu-day";
import { fetchTodayMealCheckins } from "@/lib/meal-checkins/api";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import type { MenuOverview } from "@/lib/menu/overview-types";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { PLANAM_ROUTES, recipeDetailPath } from "@/lib/planam/routes";
import { fetchProgressOverview } from "@/lib/progress/api";
import type { ProgressOverview } from "@/lib/progress/types";
import { isNutritionProfileComplete } from "@/lib/profile/nutrition-summary";
import { fetchWaterToday, type WaterToday } from "@/lib/water-intake/api";
import { buildWellnessInsight } from "@/lib/wellness/wellness-insight";
import { countCompletedMeals } from "@/lib/wellness/wellness-status";

type LoadState = "loading" | "ready" | "error";

type MetricRow = {
  label: string;
  current: number;
  target: number | null;
  format: (current: number, target: number | null) => string;
};

export function WellnessV2() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [overview, setOverview] = useState<MenuOverview | null>(null);
  const [progress, setProgress] = useState<ProgressOverview | null>(null);
  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [water, setWater] = useState<WaterToday | null>(null);
  const [aiOpen, setAiOpen] = useState(false);
  const [checkins, setCheckins] = useState<
    Awaited<ReturnType<typeof fetchTodayMealCheckins>>
  >([]);

  const reload = useCallback(
    async (force = false) => {
      if (!initData) {
        return;
      }
      const progKey = cacheKey.progressOverview(mode);
      const overKey = cacheKey.menuOverview(mode);
      if (!force) {
        const cachedOver = getCached<MenuOverview>(overKey);
        const cachedProg = getCached<ProgressOverview>(progKey);
        if (cachedOver && cachedProg) {
          setOverview(cachedOver);
          setProgress(cachedProg);
        }
      }
      setLoadState("loading");
      setErrorMessage(null);
      try {
        const [overviewData, progressData, profileData, waterData, checkinData] =
          await Promise.all([
            fetchMenuOverview(initData, mode),
            fetchProgressOverview(initData, mode),
            fetchNutritionProfile(initData).catch(() => null),
            fetchWaterToday(initData, mode).catch(() => ({
              total_ml: 0,
              target_ml: null,
            })),
            fetchTodayMealCheckins(initData, mode).catch(() => []),
          ]);
        setCached(overKey, overviewData);
        if (progressData) {
          setCached(progKey, progressData);
        }
        setOverview(overviewData);
        setProgress(progressData);
        setProfile(profileData);
        setWater(waterData);
        setCheckins(checkinData);
        setLoadState("ready");
      } catch (err) {
        setLoadState("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Не удалось загрузить данные",
        );
      }
    },
    [initData, mode],
  );

  useEffect(() => {
    if (modeLoading) {
      return;
    }
    if (!initData) {
      setLoadState("ready");
      return;
    }
    void reload();
  }, [reload, initData, modeLoading]);

  const profileComplete = isNutritionProfileComplete(profile);
  const mealsCompleted = countCompletedMeals(checkins);

  const insight = useMemo(
    () =>
      buildWellnessInsight({
        overview,
        progress,
        water,
        profileComplete,
        mealsCompleted,
      }),
    [overview, progress, water, profileComplete, mealsCompleted],
  );

  const plannedNutrition = useMemo(() => {
    if (!overview?.selected_menu?.menu) return null;
    const state = buildActiveMenuDayState(overview);
    return sumMealNutrition(state.activeMeals);
  }, [overview]);

  const metrics = useMemo<MetricRow[]>(() => {
    const targets = progress?.targets;
    const actual = progress?.daily_actual;
    const planned = plannedNutrition;
    const usePlanned =
      (actual?.calories_consumed ?? 0) === 0 &&
      planned != null &&
      planned.calories > 0 &&
      overview?.plan_summary.has_selected_menu;

    const waterTotal = water?.total_ml ?? actual?.water_consumed_ml ?? 0;
    const waterTarget = water?.target_ml ?? targets?.water_target_ml ?? null;
    const kcal = (c: number, t: number | null) =>
      t != null ? `${Math.round(c)} / ${Math.round(t)} ккал` : `${Math.round(c)} ккал`;
    const grams = (c: number, t: number | null) =>
      t != null ? `${Math.round(c)} / ${Math.round(t)} г` : `${Math.round(c)} г`;
    const liters = (c: number, t: number | null) =>
      t != null
        ? `${(c / 1000).toFixed(1)} / ${(t / 1000).toFixed(1)} л`
        : `${(c / 1000).toFixed(1)} л`;

    return [
      {
        label: "Калории",
        current: usePlanned ? planned!.calories : (actual?.calories_consumed ?? 0),
        target: targets?.calories_target ?? null,
        format: kcal,
      },
      {
        label: "Белки",
        current: usePlanned ? planned!.protein_g : (actual?.protein_consumed_g ?? 0),
        target: targets?.protein_target_g ?? null,
        format: grams,
      },
      {
        label: "Жиры",
        current: usePlanned ? planned!.fat_g : (actual?.fat_consumed_g ?? 0),
        target: targets?.fat_target_g ?? null,
        format: grams,
      },
      {
        label: "Углеводы",
        current: usePlanned ? planned!.carbs_g : (actual?.carbs_consumed_g ?? 0),
        target: targets?.carbs_target_g ?? null,
        format: grams,
      },
      {
        label: "Вода",
        current: waterTotal,
        target: waterTarget,
        format: liters,
      },
    ];
  }, [progress, water, plannedNutrition, overview?.plan_summary.has_selected_menu]);

  const recommendations = useMemo(() => {
    const meals = overview?.today_meals ?? [];
    return meals
      .filter((m) => m.name?.trim() && m.recipe_id != null)
      .slice(0, 3);
  }, [overview]);

  const handleWaterUpdated = useCallback(() => {
    invalidateCache(cacheKey.progressOverview(mode));
    invalidateCache(cacheKey.menuOverview(mode));
    void reload(true);
  }, [mode, reload]);

  const loading = modeLoading || (Boolean(initData) && loadState === "loading");

  if (loadState === "error") {
    return (
      <div className="px-4 pb-8 pt-2">
        <V2EmptyState
          icon={<span aria-hidden>💚</span>}
          title="Не удалось загрузить данные"
          description={errorMessage ?? "Проверьте сеть и попробуйте снова."}
          actionLabel="Обновить"
          onAction={() => void reload(true)}
        />
      </div>
    );
  }

  const hasAnyData =
    profileComplete ||
    (progress?.daily_actual?.meals_logged ?? 0) > 0 ||
    (water?.total_ml ?? 0) > 0 ||
    (overview?.plan_summary.has_selected_menu &&
      (plannedNutrition?.calories ?? 0) > 0);

  return (
    <div className="space-y-3 px-4 pb-2 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <header>
        <h1 className="pa26-page-title">Здоровье</h1>
        <p className="pa26-micro mt-0.5 text-pa-muted">Ваш баланс на сегодня</p>
      </header>

      {loading ? (
        <>
          <Skeleton2026 variant="rect" className="h-48 w-full" />
          <Skeleton2026 variant="rect" className="h-20 w-full" />
          <Skeleton2026 variant="rect" className="h-24 w-full" />
        </>
      ) : !hasAnyData ? (
        <V2EmptyState
          icon={<span aria-hidden>🌿</span>}
          title="Расскажите о себе — покажем баланс"
          description="PLANAM посчитает калории и даст рекомендации под ваши цели."
          actionLabel="Настроить питание"
          onAction={() =>
            router.push(`${PLANAM_ROUTES.accountNutrition}?returnTo=/wellness`)
          }
        />
      ) : (
        <>
          <V2Card>
            <h2 className="pa26-section-title">Сегодня</h2>
            <div className="mt-3 space-y-3">
              {metrics.map((row) => {
                const pct =
                  row.target != null && row.target > 0
                    ? (row.current / row.target) * 100
                    : 0;
                return (
                  <div key={row.label}>
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="pa26-micro font-medium text-pa-foreground">
                        {row.label}
                      </span>
                      <span className="pa26-micro tabular-nums text-pa-muted">
                        {row.format(row.current, row.target)}
                      </span>
                    </div>
                    <V2ProgressBar
                      percent={pct}
                      tone={row.label === "Вода" ? "water" : "brand"}
                      className="mt-1.5"
                    />
                  </div>
                );
              })}
              <div className="flex items-baseline justify-between gap-2 pt-0.5">
                <span className="pa26-micro font-medium text-pa-foreground">
                  Активность
                </span>
                <span className="pa26-micro tabular-nums text-pa-muted">
                  {progress?.trainings_this_week
                    ? `${progress.trainings_this_week} трен.${
                        progress.training_minutes_week
                          ? ` · ${progress.training_minutes_week} мин`
                          : ""
                      }`
                    : "Не отмечена на неделе"}
                </span>
              </div>
            </div>
          </V2Card>

          <WaterIntake2026 compact onUpdated={handleWaterUpdated} />

          {insight ? <V2AiTip text={insight} /> : null}

          <V2AiTip
            tone="ai"
            title="AI-нутрициолог"
            text="Можно написать: пропустил обед, съел другое, хочу добрать белок. PRO: расширенный разбор рациона."
            onClick={() => setAiOpen(true)}
          />

          {recommendations.length > 0 ? (
            <section>
              <h2 className="pa26-section-title">Рекомендации для вас</h2>
              <div className="-mx-4 mt-2 flex gap-2 overflow-x-auto px-4 pb-1">
                {recommendations.map((meal) => (
                  <Link
                    key={`${meal.meal_type}-${meal.recipe_id}`}
                    href={recipeDetailPath(meal.recipe_id!)}
                    className="w-44 shrink-0 rounded-card border border-pa-border bg-pa-surface px-3 py-3 shadow-soft transition hover:bg-sage-50/60 dark:shadow-none dark:hover:bg-pa-elevated/30"
                  >
                    <p className="pa26-card-title line-clamp-2 leading-snug">
                      {meal.name}
                    </p>
                    <p className="pa26-micro mt-1 text-pa-muted">
                      Из меню на сегодня
                    </p>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}

          <V2Button
            variant="primary"
            size="wide"
            onClick={() => setAiOpen(true)}
          >
            Спросить AI-нутрициолога
          </V2Button>
        </>
      )}

      <AiNutritionChatSheet open={aiOpen} onClose={() => setAiOpen(false)} />
    </div>
  );
}
