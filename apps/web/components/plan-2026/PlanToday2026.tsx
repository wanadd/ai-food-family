"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MealOutcomeSheet2026 } from "@/components/dom-2026/MealOutcomeSheet2026";
import { DayNutritionCard2026 } from "@/components/plan-2026/DayNutritionCard2026";
import { PlanTimelineSection2026 } from "@/components/plan-2026/PlanTimelineSection2026";
import { ReplaceDishSheet2026 } from "@/components/plan-2026/ReplaceDishSheet2026";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { EmptyState2026 } from "@/components/planam-2026/ui/EmptyState2026";
import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import { useToast } from "@/components/ui/ToastProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { fetchTodayMealCheckins } from "@/lib/meal-checkins/api";
import { deleteMenuItem, fetchSelectedMenu } from "@/lib/menu/api";
import { buildReplaceCatalogUrl } from "@/lib/menu/replace-slot";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import {
  defaultDayIndex,
  getMenuDays,
  menuHasMultipleDays,
} from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";
import {
  buildImageMapFromOverview,
  enrichMealsForDay,
  formatPlanDayLabel,
  groupByTimeline,
  plannedDateForDay,
} from "@/lib/plan/plan-today";
import { cn } from "@/lib/planam/cn";

type CachedSelected = { menu: MenuVariant | null; selected_at: string | null };

export function PlanToday2026() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();
  const { showToast } = useToast();

  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dayIndex, setDayIndex] = useState(1);
  const [replaceOpen, setReplaceOpen] = useState(false);
  const [replaceMealIndex, setReplaceMealIndex] = useState<number | null>(null);
  const [outcomeOpen, setOutcomeOpen] = useState(false);
  const [outcomeMealIndex, setOutcomeMealIndex] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const [selected, overview] = await Promise.all([
        fetchSelectedMenu(initData, mode),
        fetchMenuOverview(initData, mode).catch(() => null),
      ]);
      const loaded = selected?.menu ?? null;
      setCached(cacheKey.selectedMenu(mode), {
        menu: loaded,
        selected_at: selected?.selected_at ?? null,
      });
      if (overview) {
        setCached(cacheKey.menuOverview(mode), overview);
      }
      setMenu(loaded);
      if (loaded) {
        const dayParam = searchParams.get("day");
        const parsed = dayParam ? Number(dayParam) : NaN;
        if (Number.isFinite(parsed) && parsed > 0) {
          setDayIndex(parsed);
        } else {
          setDayIndex(defaultDayIndex(loaded));
        }
      }
    } catch {
      setError("Не удалось загрузить план");
    } finally {
      setLoading(false);
    }
  }, [initData, mode, searchParams]);

  useEffect(() => {
    if (!modeLoading) {
      void load();
    }
  }, [load, modeLoading]);

  useEffect(() => {
    if (searchParams.get("replace") === "1" && menu) {
      setReplaceOpen(true);
      setReplaceMealIndex(null);
    }
    if (searchParams.get("outcome") === "1") {
      setOutcomeOpen(true);
    }
  }, [searchParams, menu]);

  const [checkins, setCheckins] = useState<Awaited<ReturnType<typeof fetchTodayMealCheckins>>>([]);

  const plannedDate = menu ? plannedDateForDay(menu, dayIndex) : "";

  const reloadCheckins = useCallback(async () => {
    if (!initData || !plannedDate) {
      return;
    }
    setCheckins(await fetchTodayMealCheckins(initData, mode, plannedDate));
  }, [initData, mode, plannedDate]);

  useEffect(() => {
    void reloadCheckins();
  }, [reloadCheckins]);

  const overviewCached = getCached<import("@/lib/menu/overview-types").MenuOverview>(
    cacheKey.menuOverview(mode),
  );

  const timeline = useMemo(() => {
    if (!menu) {
      return [];
    }
    const imageMap = buildImageMapFromOverview(overviewCached);
    const meals = enrichMealsForDay(menu, dayIndex, checkins, imageMap);
    return groupByTimeline(meals);
  }, [menu, dayIndex, checkins, overviewCached]);

  const multiDay = menu ? menuHasMultipleDays(menu) : false;
  const days = menu ? getMenuDays(menu) : [];

  if (loading) {
    return (
      <div className="space-y-4 px-4 pb-8 pt-2">
        <Skeleton2026 variant="text" className="max-w-[60%]" />
        <Skeleton2026 variant="rect" aspectRatio="16/9" />
        <Skeleton2026 variant="rect" aspectRatio="16/9" />
      </div>
    );
  }

  if (!menu) {
    return (
      <div className="px-4 py-8">
        <EmptyState2026
          icon={<span aria-hidden>📅</span>}
          title="Плана пока нет"
          description="Составьте меню на неделю — и здесь появятся блюда с фото на каждый приём пищи."
          actionLabel="Создать меню"
          onAction={() => router.push(PLAN_PATHS.generate)}
        />
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState2026
        title="Ошибка"
        description={error}
        actionLabel="Повторить"
        onAction={() => void load()}
      />
    );
  }

  const dateLabel = formatPlanDayLabel(menu, dayIndex);
  const justSaved = searchParams.get("saved") === "1";

  return (
    <div className="pb-28 bg-pa-canvas">
      <div className="px-4 pt-2">
        {justSaved ? (
          <div className="mb-3 rounded-card border border-sage-200 bg-sage-50 px-4 py-3 dark:border-sage-700/40 dark:bg-sage-700/20">
            <p className="pa26-caption font-semibold text-sage-800 dark:text-sage-300">
              План сохранён — отмечайте приёмы пищи ниже
            </p>
          </div>
        ) : null}
        <h1 className="pa26-page-title capitalize">{dateLabel}</h1>
        {menu.title ? (
          <p className="pa26-micro mt-1 text-pa-muted">{menu.title}</p>
        ) : null}

        {multiDay ? (
          <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
            {days.map((day) => (
              <button
                key={day.day_index}
                type="button"
                onClick={() => setDayIndex(day.day_index)}
                className={cn(
                  "shrink-0 rounded-pill px-3 py-1.5 pa26-micro font-semibold",
                  dayIndex === day.day_index
                    ? "bg-pa-brand text-white"
                    : "border border-pa-border bg-pa-elevated text-pa-muted",
                )}
              >
                {day.label}
              </button>
            ))}
          </div>
        ) : null}

        <div className="mt-3 flex gap-2">
          <Button2026
            variant="secondary"
            className="flex-1"
            onClick={() => {
              setReplaceMealIndex(null);
              setReplaceOpen(true);
            }}
          >
            Заменить блюдо
          </Button2026>
          <Button2026
            variant="ghost"
            onClick={() => setOutcomeOpen(true)}
          >
            Итог дня
          </Button2026>
        </div>

        {plannedDate ? <DayNutritionCard2026 plannedDate={plannedDate} /> : null}
      </div>

      <div className="mt-4 px-4">
        {timeline.length === 0 ? (
          <EmptyState2026
            title="На этот день нет блюд"
            description="Выберите другой день или пересоберите план."
            actionLabel="Неделя"
            onAction={() => router.push(PLAN_PATHS.week)}
          />
        ) : (
          <PlanTimelineSection2026
            groups={timeline}
            onCook={(index) => {
              setOutcomeMealIndex(index);
              setOutcomeOpen(true);
            }}
            onReplace={(slotId, recipeId) => {
              if (!slotId) {
                return;
              }
              router.push(
                buildReplaceCatalogUrl(
                  slotId,
                  recipeId ?? undefined,
                  "/plan/today",
                ),
              );
            }}
            onRemove={async (slotId) => {
              if (!initData) {
                return;
              }
              try {
                await deleteMenuItem(initData, mode, slotId);
                invalidateCache(cacheKey.menuOverview(mode));
                invalidateCache(cacheKey.selectedMenu(mode));
                showToast("Блюдо удалено из меню");
                await load();
              } catch {
                showToast("Не удалось удалить блюдо. Попробуйте ещё раз.");
              }
            }}
          />
        )}
      </div>

      <ReplaceDishSheet2026
        open={replaceOpen}
        menu={menu}
        dayIndex={dayIndex}
        preselectedMealIndex={replaceMealIndex}
        onClose={() => {
          setReplaceOpen(false);
          setReplaceMealIndex(null);
        }}
        onSuccess={() => {
          invalidateCache(cacheKey.menuOverview(mode));
          void load();
        }}
      />

      <MealOutcomeSheet2026
        open={outcomeOpen}
        dayIndex={dayIndex}
        plannedDate={plannedDate}
        preselectedMealIndex={outcomeMealIndex}
        onClose={() => {
          setOutcomeOpen(false);
          setOutcomeMealIndex(null);
        }}
        onSuccess={() => {
          invalidateCache(cacheKey.menuOverview(mode));
          void load();
          void reloadCheckins();
        }}
      />
    </div>
  );
}
