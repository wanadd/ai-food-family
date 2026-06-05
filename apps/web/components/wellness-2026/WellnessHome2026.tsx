"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { WaterIntake2026 } from "@/components/wellness-2026/WaterIntake2026";
import { WellnessDayRing2026 } from "@/components/wellness-2026/WellnessDayRing2026";
import { WellnessGoalCard2026 } from "@/components/wellness-2026/WellnessGoalCard2026";
import { WellnessInsight2026 } from "@/components/wellness-2026/WellnessInsight2026";
import { WellnessTodayCard2026 } from "@/components/wellness-2026/WellnessTodayCard2026";
import { WellnessWeekStrip2026 } from "@/components/wellness-2026/WellnessWeekStrip2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { fetchTodayMealCheckins } from "@/lib/meal-checkins/api";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import type { MenuOverview } from "@/lib/menu/overview-types";
import { buildGoalProgressCard } from "@/lib/nutritionist/goal-progress";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";
import {
  fetchProgressHistory,
  fetchProgressOverview,
} from "@/lib/progress/api";
import type { ProgressOverview } from "@/lib/progress/types";
import { isNutritionProfileComplete } from "@/lib/profile/nutrition-summary";
import { wellnessGoalLabel } from "@/lib/wellness/goal-labels";
import { buildWeekStrip } from "@/lib/wellness/week-strip";
import {
  buildWellnessDayProgress,
  buildWellnessTodayMetrics,
  countCompletedMeals,
} from "@/lib/wellness/wellness-status";
import { buildWellnessInsight } from "@/lib/wellness/wellness-insight";
import { fetchWaterToday } from "@/lib/water-intake/api";
import type { WaterToday } from "@/lib/water-intake/api";

type LoadState = "loading" | "ready" | "error";

export function WellnessHome2026() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [overview, setOverview] = useState<MenuOverview | null>(null);
  const [progress, setProgress] = useState<ProgressOverview | null>(null);
  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [water, setWater] = useState<WaterToday | null>(null);
  const [checkins, setCheckins] = useState<Awaited<
    ReturnType<typeof fetchTodayMealCheckins>
  > | null>(null);
  const [history, setHistory] = useState<Awaited<
    ReturnType<typeof fetchProgressHistory>
  > | null>(null);

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
        const [
          overviewData,
          progressData,
          profileData,
          waterData,
          checkinData,
          historyData,
        ] = await Promise.all([
          fetchMenuOverview(initData, mode),
          fetchProgressOverview(initData, mode),
          fetchNutritionProfile(initData).catch(() => null),
          fetchWaterToday(initData, mode).catch(() => ({
            total_ml: 0,
            target_ml: null,
          })),
          fetchTodayMealCheckins(initData, mode).catch(() => []),
          fetchProgressHistory(initData, mode).catch(() => []),
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
        setHistory(historyData);
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
  const mealsCompleted = countCompletedMeals(checkins ?? []);
  const goalLabel = wellnessGoalLabel(
    progress?.goal_type ?? profile?.nutrition_goal,
    overview?.plan_summary.goal_label ?? progress?.goal_label,
  );
  const goalCard = buildGoalProgressCard(profile, progress);

  const dayProgress = useMemo(
    () =>
      buildWellnessDayProgress({
        progress,
        water,
        checkins: checkins ?? [],
        overview,
      }),
    [progress, water, checkins, overview],
  );

  const todayMetrics = useMemo(
    () =>
      buildWellnessTodayMetrics({
        progress,
        water,
        checkins: checkins ?? [],
        overview,
      }),
    [progress, water, checkins, overview],
  );

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

  const weekDays = useMemo(
    () => buildWeekStrip(history ?? [], progress, dayProgress.percent),
    [history, progress, dayProgress.percent],
  );

  const handleWaterUpdated = useCallback(() => {
    invalidateCache(cacheKey.progressOverview(mode));
    invalidateCache(cacheKey.menuOverview(mode));
    void reload(true);
  }, [mode, reload]);

  const loading =
    modeLoading || (Boolean(initData) && loadState === "loading");

  if (loadState === "error") {
    return (
      <div className="px-4 pb-8 pt-2">
        <EmptyState2026
          icon={<span aria-hidden>💚</span>}
          title="Не удалось загрузить Заботу"
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
    overview?.plan_summary.has_selected_menu;

  return (
    <div className="space-y-3 px-4 pb-2 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <header className="pb-1">
        <h1 className="pa26-page-title">Здоровье</h1>
        <p className="pa26-caption text-pa-muted">Калории, цели и ограничения</p>
      </header>
      {loading ? (
        <>
          <Skeleton2026 variant="rect" className="h-28 w-full" />
          <Skeleton2026 variant="rect" className="h-36 w-full" />
          <Skeleton2026 variant="rect" className="h-24 w-full" />
        </>
      ) : !hasAnyData ? (
        <EmptyState2026
          icon={<span aria-hidden>🌿</span>}
          title="Забота пока не настроена"
          description="Добавьте цель, ограничения и предпочтения — ПланАм будет подсказывать меню мягче и точнее."
          actionLabel="Настроить заботу"
          onAction={() => router.push("/profile/nutrition")}
        />
      ) : (
        <>
          <WellnessDayRing2026 progress={dayProgress} />
          <WellnessTodayCard2026 metrics={todayMetrics} />
          <WaterIntake2026 onUpdated={handleWaterUpdated} />
          <WellnessInsight2026 text={insight} />
          <WellnessGoalCard2026
            goalLabel={goalLabel}
            goalCard={goalCard}
            profileComplete={profileComplete}
          />
          <WellnessWeekStrip2026 days={weekDays} />
        </>
      )}

      {!loading ? (
        <div className="space-y-3 pt-2">
          <Button2026
            size="wide"
            variant="primary"
            onClick={() => router.push("/wellness/chat")}
          >
            Спросить ПланАм
          </Button2026>
          <Button2026
            size="wide"
            variant="secondary"
            onClick={() => router.push(`${PLAN_PATHS.today}?outcome=1`)}
          >
            Отметить приём пищи
          </Button2026>
        </div>
      ) : null}
    </div>
  );
}
