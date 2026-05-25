"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { CareTelegramLinkCard } from "@/components/care/CareTelegramLinkCard";
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
import { getPersonsCount } from "@/lib/home/plan-summary";
import {
  getNutritionGoalLabel,
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
import { buildFamilyMemberInsights } from "@/lib/nutritionist/family-insights";
import { buildGoalProgressCard } from "@/lib/nutritionist/goal-progress";
import { pickMainAdvice } from "@/lib/nutritionist/main-advice";
import { withReturnTo } from "@/lib/navigation/return-to";
import { fetchProgressOverview } from "@/lib/progress/api";
import type { ProgressOverview } from "@/lib/progress/types";

const NUTRI_RETURN = "/nutritionist";

const QUICK_ACTIONS = [
  {
    href: withReturnTo("/progress?focus=weight", NUTRI_RETURN),
    label: "Добавить вес",
    emoji: "⚖️",
  },
  {
    href: withReturnTo("/progress?focus=training", NUTRI_RETURN),
    label: "Добавить тренировку",
    emoji: "🏃",
  },
  {
    href: withReturnTo("/profile/nutrition", NUTRI_RETURN),
    label: "Изменить цель",
    emoji: "🎯",
  },
] as const;

export function NutritionistDashboard() {
  const { initData, state: authState } = useProtectedScreen();
  const { mode, context, loading: modeLoading } = useAppMode();

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
  const [familySummaryOpen, setFamilySummaryOpen] = useState(false);
  const [familyProgressOpen, setFamilyProgressOpen] = useState(false);
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
    if (!initData) {
      return;
    }
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
      console.info("[PlanAm] Nutritionist dashboard loaded");
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

  const personsCount = getPersonsCount(mode, context);
  const goalLabel = getNutritionGoalLabel(profile);
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

  const familyInsights = useMemo(() => {
    if (mode !== "family" || !context?.family) return [];
    return buildFamilyMemberInsights(context.family);
  }, [mode, context?.family]);

  const familyProgress = progress?.family_progress ?? [];

  if (authState !== "ready") {
    return (
      <ProtectedScreenFallback
        loadingMessage="Загрузка…"
        telegramMessage="Нутрициолог доступен в Telegram Mini App."
      />
    );
  }

  if (loading || modeLoading) {
    return (
      <ScreenLayout title="Нутрициолог" contentClassName="space-y-3 pb-24">
        <SkeletonCard titleWidth="w-1/2" lines={3} withButton />
        <SkeletonList count={2} />
      </ScreenLayout>
    );
  }

  return (
    <ScreenLayout
      title="Нутрициолог"
      subtitle="Семейный AI-помощник по питанию"
      contentClassName="space-y-3"
    >
      {!profileComplete ? (
        <section className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
          <p className="font-semibold text-stone-900">Дозаполнить профиль</p>
          <p className="mt-1 text-sm text-stone-600">
            Чем точнее данные — тем точнее советы ПланАм. Заполнить можно
            в любой момент.
          </p>
          <Link
            href={withReturnTo("/profile/nutrition", NUTRI_RETURN)}
            className="mt-3 inline-flex min-h-[44px] items-center rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white"
          >
            Открыть профиль
          </Link>
        </section>
      ) : null}

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm space-y-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-stone-500">
            {daily.planTitle}
          </p>
          <ul className="mt-2 space-y-1 text-sm text-stone-700">
            <li>{daily.plan.calories}</li>
            <li>{daily.plan.protein}</li>
            <li>{daily.plan.fat}</li>
            <li>{daily.plan.carbs}</li>
            <li>{daily.plan.water}</li>
          </ul>
        </div>
        <div className="border-t border-stone-100 pt-3">
          <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">
            {daily.actualTitle}
          </p>
          <ul className="mt-2 space-y-1 text-sm text-stone-700">
            <li>{daily.actual.calories}</li>
            <li>{daily.actual.protein}</li>
            <li>{daily.actual.fat}</li>
            <li>{daily.actual.carbs}</li>
            <li>{daily.actual.water}</li>
          </ul>
        </div>
        <p className="text-xs text-stone-500">{daily.trainingLine}</p>
        <p className="text-xs text-stone-500">{daily.menuLine}</p>
        {initData ? (
          <WaterIntakePanel
            onUpdated={() => {
              // Water intake changes progress totals → drop progress
              // cache so the dashboard pulls fresh data on next load.
              invalidateCache("progress-overview");
              void load();
            }}
          />
        ) : null}
        {menu ? (
          <Link
            href="/menu/current"
            className="inline-block text-xs font-semibold text-emerald-700"
          >
            Отметить, где поели →
          </Link>
        ) : null}
        {daily.todoLine ? (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm font-medium text-amber-950">
            Осталось: {daily.todoLine}
          </p>
        ) : null}
      </section>

      <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
          Прогресс к цели
        </p>
        <p className="mt-1 text-lg font-bold text-stone-900">
          {goalLabel ?? "Цель не задана"}
        </p>
        <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
          <div>
            <dt className="text-stone-500">Старт</dt>
            <dd className="font-semibold text-stone-900">{goalCard.startWeight}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Сейчас</dt>
            <dd className="font-semibold text-stone-900">{goalCard.currentWeight}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Цель</dt>
            <dd className="font-semibold text-stone-900">{goalCard.targetWeight}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Осталось</dt>
            <dd className="font-semibold text-emerald-800">
              {goalCard.remaining ?? "—"}
            </dd>
          </div>
        </dl>
        {goalCard.percent != null ? (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-stone-600">
              <span>Выполнение</span>
              <span className="font-bold text-emerald-800">{goalCard.percent}%</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-stone-100">
              <div
                className="h-full rounded-full bg-emerald-500"
                style={{ width: `${goalCard.percent}%` }}
              />
            </div>
          </div>
        ) : null}
        <dl className="mt-3 grid grid-cols-2 gap-2 border-t border-emerald-100 pt-3 text-sm">
          <div>
            <dt className="text-stone-500">Начато</dt>
            <dd className="font-semibold text-stone-900">
              {goalCard.startedAt ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-stone-500">Прошло</dt>
            <dd className="font-semibold text-stone-900">
              {goalCard.daysElapsed != null
                ? `${goalCard.daysElapsed} дн.`
                : "—"}
            </dd>
          </div>
        </dl>
        {goalCard.paceLine ? (
          <p className="mt-2 text-sm text-stone-600">{goalCard.paceLine}</p>
        ) : null}
        {goalCard.forecastLine ? (
          <p className="mt-1 text-sm text-stone-600">{goalCard.forecastLine}</p>
        ) : null}
        <Link
          href={withReturnTo("/progress", NUTRI_RETURN)}
          className="mt-3 inline-block text-xs font-semibold text-emerald-700"
        >
          Подробнее в прогрессе →
        </Link>
      </section>

      {profileComplete ? (
        <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wide text-stone-500">
            Почему ПланАм рекомендует это?
          </p>
          <ul className="mt-2 space-y-1 text-sm text-stone-700">
            {adviceWhy.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {initData && !adviceHiddenByDefer ? (
        <NutritionistAdviceCard
          advice={advice}
          initData={initData}
          mode={mode}
          onDeferred={refreshDeferred}
        />
      ) : null}

      {deferredAdvice.length > 0 ? (
        <section className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
          <p className="text-sm font-bold text-stone-900">Отложенные рекомендации</p>
          <ul className="mt-3 space-y-3">
            {deferredAdvice.map((item) => (
              <li
                key={item.id}
                className="rounded-xl border border-stone-200 bg-white p-3"
              >
                <p className="font-semibold text-stone-900">{item.title}</p>
                <p className="mt-1 text-xs text-stone-600">{item.body}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      if (!initData) return;
                      void completeDeferredAdvice(initData, mode, item.id).then(
                        refreshDeferred,
                      );
                    }}
                    className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white"
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
                    className="rounded-lg border border-stone-200 px-3 py-1.5 text-xs font-semibold text-stone-700"
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
                    className="rounded-lg px-3 py-1.5 text-xs font-semibold text-red-600"
                  >
                    Удалить
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section>
        <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-stone-500">
          Быстрые действия
        </p>
        <div className="grid grid-cols-2 gap-2">
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="flex min-h-[72px] flex-col items-start justify-center rounded-2xl border border-stone-100 bg-white px-3 py-3 shadow-sm transition active:scale-[0.98]"
            >
              <span className="text-lg" aria-hidden>
                {action.emoji}
              </span>
              <span className="mt-1 text-sm font-semibold leading-tight text-stone-900">
                {action.label}
              </span>
            </Link>
          ))}
        </div>
      </section>

      {familyInsights.length > 0 ? (
        <section className="rounded-2xl border border-stone-100 bg-white shadow-sm">
          <button
            type="button"
            onClick={() => setFamilySummaryOpen((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3.5 text-left"
          >
            <span className="font-semibold text-stone-900">Семейная сводка</span>
            <span className="text-stone-400" aria-hidden>
              {familySummaryOpen ? "▲" : "▼"}
            </span>
          </button>
          {familySummaryOpen ? (
            <ul className="space-y-2 border-t border-stone-100 px-4 py-3">
              {familyInsights.map((row) => (
                <li key={row.name} className="text-sm text-stone-700">
                  <span className="font-semibold text-stone-900">{row.name}:</span>{" "}
                  {row.line}
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {familyProgress.length > 0 ? (
        <section className="rounded-2xl border border-stone-100 bg-white shadow-sm">
          <button
            type="button"
            onClick={() => setFamilyProgressOpen((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3.5 text-left"
          >
            <span className="font-semibold text-stone-900">Прогресс семьи</span>
            <span className="text-stone-400" aria-hidden>
              {familyProgressOpen ? "▲" : "▼"}
            </span>
          </button>
          {familyProgressOpen ? (
            <ul className="space-y-2 border-t border-stone-100 px-4 py-3">
              {familyProgress.map((row) => (
                <li key={row.member_id} className="text-sm text-stone-700">
                  <span className="font-semibold text-stone-900">{row.name}</span>
                  <br />
                  <span>{row.progress_summary}</span>
                </li>
              ))}
              <li>
                <Link
                  href="/progress"
                  className="text-sm font-semibold text-emerald-700"
                >
                  Подробнее в прогрессе →
                </Link>
              </li>
            </ul>
          ) : null}
        </section>
      ) : null}

      <CareTelegramLinkCard />

      <Link
        href="/nutritionist/chat"
        className="flex min-h-[52px] items-center justify-center rounded-2xl bg-stone-900 px-4 py-3.5 text-center text-sm font-semibold text-white shadow-md active:scale-[0.99]"
      >
        Открыть чат нутрициолога
      </Link>
    </ScreenLayout>
  );
}
