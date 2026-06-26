"use client";

/**
 * PLANAM V2 — Здоровье (/wellness).
 * Компактный центр дня: статус, сводка, действия, приёмы пищи, вода, совет, AI, Pro.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MealEatenSheetV2 } from "@/components/planam-v2/menu/MealEatenSheetV2";
import { AiNutritionChatSheet } from "@/components/planam-v2/wellness/AiNutritionChatSheet";
import { WellnessMealsSection } from "@/components/planam-v2/wellness/WellnessMealsSection";
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
import { buildWellnessAdviceCard } from "@/lib/wellness/wellness-advice";
import {
  buildWellnessDayStatus,
  formatWellnessDate,
} from "@/lib/wellness/wellness-day-status";
import { buildWellnessMealSlots } from "@/lib/wellness/wellness-meals";
import {
  buildWellnessRecommendations,
  wellnessRecommendationsEmptyMessage,
} from "@/lib/wellness/wellness-recommendations";
import { buildWellnessSummaryPhrase } from "@/lib/wellness/wellness-summary";

type LoadState = "loading" | "ready" | "error";

type MealSheetState = {
  open: boolean;
  mealType?: string | null;
  mealName?: string | null;
  recipeId?: number | null;
  initialStep?: "actions" | "other";
  autoOutcome?: "ate_home" | "cooked" | "skipped" | null;
};

const CLOSED_SHEET: MealSheetState = { open: false };

export function WellnessV2() {
  const router = useRouter();
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();
  const waterRef = useRef<HTMLDivElement>(null);

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [overview, setOverview] = useState<MenuOverview | null>(null);
  const [progress, setProgress] = useState<ProgressOverview | null>(null);
  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [water, setWater] = useState<WaterToday | null>(null);
  const [aiOpen, setAiOpen] = useState(false);
  const [mealSheet, setMealSheet] = useState<MealSheetState>(CLOSED_SHEET);
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
  const isPro = Boolean(overview?.is_pro || progress?.is_pro);
  const trainingEnabled = Boolean(profile?.pro?.workouts_enabled);

  const dayStatus = useMemo(
    () => buildWellnessDayStatus({ overview, progress, checkins }),
    [overview, progress, checkins],
  );

  const summaryPhrase = useMemo(
    () => buildWellnessSummaryPhrase(progress),
    [progress],
  );

  const advice = useMemo(
    () =>
      buildWellnessAdviceCard({
        overview,
        progress,
        water,
        checkins,
        profileComplete,
      }),
    [overview, progress, water, checkins, profileComplete],
  );

  const mealSlots = useMemo(
    () => buildWellnessMealSlots({ overview, checkins }),
    [overview, checkins],
  );

  const recommendations = useMemo(
    () => buildWellnessRecommendations({ overview, progress }),
    [overview, progress],
  );

  const metrics = useMemo(() => {
    const targets = progress?.targets;
    const actual = progress?.daily_actual;
    const waterTotal = water?.total_ml ?? actual?.water_consumed_ml ?? 0;
    const waterTarget = water?.target_ml ?? targets?.water_target_ml ?? null;

    return {
      calories: {
        current: actual?.calories_consumed ?? 0,
        target: targets?.calories_target ?? null,
      },
      protein: {
        current: actual?.protein_consumed_g ?? 0,
        target: targets?.protein_target_g ?? null,
      },
      fat: {
        current: actual?.fat_consumed_g ?? 0,
        target: targets?.fat_target_g ?? null,
      },
      carbs: {
        current: actual?.carbs_consumed_g ?? 0,
        target: targets?.carbs_target_g ?? null,
      },
      water: { current: waterTotal, target: waterTarget },
    };
  }, [progress, water]);

  const handleWaterUpdated = useCallback(() => {
    invalidateCache(cacheKey.progressOverview(mode));
    invalidateCache(cacheKey.menuOverview(mode));
    void reload(true);
  }, [mode, reload]);

  const openMealSheet = useCallback((partial: Omit<MealSheetState, "open">) => {
    setMealSheet({ open: true, ...partial });
  }, []);

  const handleAdviceAction = useCallback(() => {
    if (!advice?.action) return;
    switch (advice.action) {
      case "add_water":
        waterRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
        break;
      case "open_meal_sheet":
        openMealSheet({ initialStep: "actions" });
        break;
      case "open_snack_sheet":
        openMealSheet({ mealType: "snack", initialStep: "actions" });
        break;
      case "open_ai":
        setAiOpen(true);
        break;
      case "show_recipes":
        router.push(PLANAM_ROUTES.planToday);
        break;
      case "setup_nutrition":
        router.push(`${PLANAM_ROUTES.accountNutrition}?returnTo=/wellness`);
        break;
      default:
        break;
    }
  }, [advice, openMealSheet, router]);

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
    (overview?.plan_summary.has_selected_menu ?? false);

  const statusTone =
    dayStatus.id === "deviations"
      ? "text-orange-700 dark:text-orange-300"
      : dayStatus.id === "needs_checkin"
        ? "text-blue-800 dark:text-blue-200"
        : "text-sage-700 dark:text-sage-300";

  return (
    <div className="space-y-3 px-4 pb-2 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <header data-testid="wellness-header">
        <h1 className="pa26-page-title">Здоровье</h1>
        <p className="pa26-micro mt-0.5 capitalize text-pa-muted">
          {formatWellnessDate()}
        </p>
        {!loading && hasAnyData ? (
          <p className={`pa26-caption mt-1 font-semibold ${statusTone}`}>
            {dayStatus.label}
          </p>
        ) : null}
      </header>

      {loading ? (
        <>
          <Skeleton2026 variant="rect" className="h-40 w-full" />
          <Skeleton2026 variant="rect" className="h-24 w-full" />
          <Skeleton2026 variant="rect" className="h-32 w-full" />
        </>
      ) : !hasAnyData ? (
        <div className="space-y-3">
          <V2EmptyState
            icon={<span aria-hidden>🌿</span>}
            title="Расскажите о себе — покажем баланс"
            description="PLANAM посчитает калории и даст рекомендации под ваши цели."
            actionLabel="Настроить питание"
            onAction={() =>
              router.push(`${PLANAM_ROUTES.accountNutrition}?returnTo=/wellness`)
            }
          />
          <V2Button
            variant="primary"
            size="wide"
            data-testid="wellness-ai-open"
            onClick={() => setAiOpen(true)}
          >
            Спросить AI-нутрициолога
          </V2Button>
        </div>
      ) : (
        <>
          <V2Card data-testid="wellness-summary">
            <h2 className="pa26-section-title">Сводка дня</h2>
            {summaryPhrase ? (
              <p className="pa26-caption mt-1 text-pa-muted">{summaryPhrase}</p>
            ) : null}
            <div className="mt-3 space-y-2.5">
              <MetricBar
                label="Ккал"
                current={metrics.calories.current}
                target={metrics.calories.target}
                format={(c, t) =>
                  t != null
                    ? `${Math.round(c)} / ${Math.round(t)}`
                    : `${Math.round(c)}`
                }
              />
              <div className="grid grid-cols-3 gap-2">
                <MacroMini
                  label="Б"
                  current={metrics.protein.current}
                  target={metrics.protein.target}
                />
                <MacroMini
                  label="Ж"
                  current={metrics.fat.current}
                  target={metrics.fat.target}
                />
                <MacroMini
                  label="У"
                  current={metrics.carbs.current}
                  target={metrics.carbs.target}
                />
              </div>
              <MetricBar
                label="Вода"
                current={metrics.water.current}
                target={metrics.water.target}
                tone="water"
                format={(c, t) =>
                  t != null
                    ? `${(c / 1000).toFixed(1)} / ${(t / 1000).toFixed(1)} л`
                    : `${(c / 1000).toFixed(1)} л`
                }
              />
            </div>
          </V2Card>

          <section data-testid="wellness-quick-actions">
            <h2 className="pa26-section-title">Что сделать сейчас</h2>
            <div className="mt-2 grid grid-cols-2 gap-2">
              <QuickAction
                label="Отметить еду"
                onClick={() => openMealSheet({ initialStep: "actions" })}
              />
              <QuickAction
                label="Добавить воду"
                onClick={() =>
                  waterRef.current?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                  })
                }
              />
              <QuickAction
                label="Ел вне дома"
                onClick={() => openMealSheet({ initialStep: "other" })}
              />
              <QuickAction
                label="Пропустил приём"
                onClick={() => openMealSheet({ initialStep: "actions" })}
              />
              <QuickAction
                label="Спросить AI"
                className="col-span-2 border-ai/30 bg-ai-soft/40 dark:bg-ai/10"
                onClick={() => setAiOpen(true)}
              />
            </div>
          </section>

          <WellnessMealsSection
            slots={mealSlots}
            onAction={(slot, action) => {
              const base = {
                mealType: slot.mealType,
                mealName: slot.plannedName,
                recipeId: slot.recipeId,
              };
              if (action === "ate_plan") {
                openMealSheet({ ...base, autoOutcome: "ate_home" });
              } else if (action === "ate_other") {
                openMealSheet({ ...base, initialStep: "other" });
              } else if (action === "skipped") {
                openMealSheet({ ...base, autoOutcome: "skipped" });
              } else {
                openMealSheet({ ...base, autoOutcome: "cooked" });
              }
            }}
          />

          <div ref={waterRef}>
            <WaterIntake2026 compact onUpdated={handleWaterUpdated} />
          </div>

          {advice ? (
            <div data-testid="wellness-advice">
              {advice.action && advice.actionLabel ? (
                <div className="space-y-2">
                  <V2AiTip text={advice.text} />
                  <V2Button
                    variant="secondary"
                    size="wide"
                    onClick={handleAdviceAction}
                  >
                    {advice.actionLabel}
                  </V2Button>
                </div>
              ) : (
                <V2AiTip text={advice.text} />
              )}
            </div>
          ) : null}

          <V2AiTip
            tone="ai"
            title="AI-нутрициолог"
            text="Спросите про ужин, белок, пропущенный приём или еду вне плана."
            onClick={() => setAiOpen(true)}
          />

          <section data-testid="wellness-recommendations">
            <h2 className="pa26-section-title">Рекомендации</h2>
            {recommendations.length > 0 ? (
              <div className="-mx-4 mt-2 flex gap-2 overflow-x-auto px-4 pb-1">
                {recommendations.map((item) => (
                  <Link
                    key={item.id}
                    href={
                      item.recipeId != null
                        ? recipeDetailPath(item.recipeId)
                        : PLANAM_ROUTES.planToday
                    }
                    className="w-44 shrink-0 rounded-card border border-pa-border bg-pa-surface px-3 py-3 shadow-soft transition hover:bg-sage-50/60 dark:shadow-none dark:hover:bg-pa-elevated/30"
                  >
                    <p className="pa26-micro font-semibold text-sage-700 dark:text-sage-300">
                      {item.categoryLabel}
                    </p>
                    <p className="pa26-card-title mt-1 line-clamp-2 leading-snug">
                      {item.title}
                    </p>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="pa26-caption mt-2 text-pa-muted">
                {wellnessRecommendationsEmptyMessage(
                  Boolean(overview?.plan_summary.has_selected_menu),
                )}
              </p>
            )}
          </section>

          {isPro ? (
            <V2Card data-testid="wellness-pro-enabled">
              <h2 className="pa26-section-title">PRO</h2>
              <p className="pa26-caption mt-1 text-pa-muted">
                Расширенные цели и разбор дня
              </p>
              <dl className="mt-3 space-y-2 pa26-caption">
                {metrics.protein.target != null ? (
                  <div className="flex justify-between gap-2">
                    <dt className="text-pa-muted">Белок</dt>
                    <dd className="font-semibold tabular-nums">
                      {Math.round(metrics.protein.current)} /{" "}
                      {Math.round(metrics.protein.target)} г
                    </dd>
                  </div>
                ) : null}
                {metrics.calories.target != null ? (
                  <div className="flex justify-between gap-2">
                    <dt className="text-pa-muted">Калории</dt>
                    <dd className="font-semibold tabular-nums">
                      {Math.round(metrics.calories.current)} /{" "}
                      {Math.round(metrics.calories.target)} ккал
                    </dd>
                  </div>
                ) : null}
              </dl>
            </V2Card>
          ) : (
            <V2Card data-testid="wellness-pro-teaser">
              <h2 className="pa26-section-title">Pro для спорта и строгих целей</h2>
              <p className="pa26-caption mt-1 text-pa-muted">
                Белковые цели, тренировки, корректировки дня и AI-нутрициолог.
              </p>
              <Link
                href="/account/subscription"
                className="mt-3 inline-flex min-h-[40px] items-center rounded-control bg-sage-600 px-4 text-sm font-semibold text-white"
              >
                Подробнее
              </Link>
            </V2Card>
          )}

          {trainingEnabled ? (
            <V2Card data-testid="wellness-training-block">
              <h2 className="pa26-section-title">Тренировки подключены</h2>
              <p className="pa26-caption mt-1 text-pa-muted">
                {progress?.trainings_this_week
                  ? `Активность сегодня: ${progress.trainings_this_week} трен.${
                      progress.training_minutes_week
                        ? ` · ${progress.training_minutes_week} мин`
                        : ""
                    }`
                  : "Активность сегодня не отмечена"}
              </p>
              <p className="pa26-micro mt-2 text-pa-muted">
                Автокоррекция меню по тренировкам появится в следующем обновлении.
              </p>
            </V2Card>
          ) : null}

          <V2Button
            variant="primary"
            size="wide"
            data-testid="wellness-ai-open"
            onClick={() => setAiOpen(true)}
          >
            Спросить AI-нутрициолога
          </V2Button>
        </>
      )}

      <AiNutritionChatSheet open={aiOpen} onClose={() => setAiOpen(false)} />

      <MealEatenSheetV2
        open={mealSheet.open}
        onClose={() => setMealSheet(CLOSED_SHEET)}
        onSaved={() => void reload(true)}
        mealType={mealSheet.mealType}
        mealName={mealSheet.mealName}
        recipeId={mealSheet.recipeId}
        initialStep={mealSheet.initialStep}
        autoOutcome={mealSheet.autoOutcome}
      />
    </div>
  );
}

function MetricBar({
  label,
  current,
  target,
  format,
  tone = "brand",
}: {
  label: string;
  current: number;
  target: number | null;
  format: (c: number, t: number | null) => string;
  tone?: "brand" | "water";
}) {
  const pct =
    target != null && target > 0 ? Math.min(100, (current / target) * 100) : 0;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="pa26-micro font-medium">{label}</span>
        <span className="pa26-micro tabular-nums text-pa-muted">
          {format(current, target)}
        </span>
      </div>
      {target != null && target > 0 ? (
        <V2ProgressBar percent={pct} tone={tone} className="mt-1" />
      ) : null}
    </div>
  );
}

function MacroMini({
  label,
  current,
  target,
}: {
  label: string;
  current: number;
  target: number | null;
}) {
  return (
    <div className="rounded-control bg-cream-deep/50 px-2 py-1.5 text-center dark:bg-pa-elevated/40">
      <p className="pa26-micro text-pa-muted">{label}</p>
      <p className="pa26-micro font-semibold tabular-nums">
        {target != null
          ? `${Math.round(current)}/${Math.round(target)}`
          : Math.round(current)}
      </p>
    </div>
  );
}

function QuickAction({
  label,
  onClick,
  className,
}: {
  label: string;
  onClick: () => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`min-h-[48px] rounded-card border border-pa-border bg-pa-surface px-3 py-2.5 text-left pa26-micro font-semibold text-pa-foreground transition active:scale-[0.99] ${className ?? ""}`}
    >
      {label}
    </button>
  );
}
