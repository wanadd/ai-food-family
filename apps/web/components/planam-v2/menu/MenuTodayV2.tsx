"use client";

/**
 * PLANAM V2 — экран «Меню» (/plan/today).
 * Главный food screen: date chips, блюда по приёмам пищи,
 * компактные rows c thumb и «+» quick actions (bottom sheet).
 */

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MealOutcomeSheet2026 } from "@/components/dom-2026/MealOutcomeSheet2026";
import { MealConsumptionSheetV2 } from "@/components/planam-v2/menu/MealConsumptionSheetV2";
import { MealEatenSheetV2 } from "@/components/planam-v2/menu/MealEatenSheetV2";
import { DayNutritionCard2026 } from "@/components/plan-2026/DayNutritionCard2026";
import { ReplaceDishSheet2026 } from "@/components/plan-2026/ReplaceDishSheet2026";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { AiProcessLoadingV2 } from "@/components/planam-v2/ai/AiProcessLoadingV2";
import {
  V2BottomSheet,
  V2Button,
  V2EmptyState,
} from "@/components/planam-v2/ui/V2Primitives";
import { RecipeImage2026 } from "@/components/recipes-2026/RecipeImage2026";
import { useToast } from "@/components/ui/ToastProvider";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import {
  createMealCheckin,
  fetchTodayMealCheckins,
} from "@/lib/meal-checkins/api";
import { deleteMenuItem, fetchSelectedMenu } from "@/lib/menu/api";
import { buildReplaceCatalogUrl } from "@/lib/menu/replace-slot";
import { fetchMenuOverview } from "@/lib/menu/overview-api";
import {
  getMenuDays,
  menuHasMultipleDays,
} from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { withReturnTo } from "@/lib/navigation/return-to";
import {
  restoreScrollPosition,
  saveScrollPosition,
} from "@/lib/navigation/scroll-restore";
import { PLAN_PATHS, recipeDetailPath } from "@/lib/plan/plan-paths";
import {
  buildPlanTodaySearchParams,
  planTodayReturnPath,
  planTodayScrollQuery,
  resolvePlanTodayDay,
  savePlanTodayDay,
} from "@/lib/plan/plan-today-nav";
import {
  buildImageMapFromOverview,
  enrichMealsForDay,
  formatPlanDayLabel,
  groupByTimeline,
  mealTypeLabel,
  plannedDateForDay,
  type PlanTodayMeal,
} from "@/lib/plan/plan-today";
import {
  MENU_TODAY_MARK_CONSUMPTION_BUTTON,
  MEAL_CONSUMPTION_SAVED_TOAST,
} from "@/lib/plan/meal-consumption-sheet";
import { menuMealHeading } from "@/lib/menu/meal-heading";
import { addRecipeToShopping } from "@/lib/recipes/api";
import { cn } from "@/lib/planam/cn";

type CachedSelected = { menu: MenuVariant | null; selected_at: string | null };

export function MenuTodayV2() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initData } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();
  const { showToast } = useToast();

  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [menuSelectionId, setMenuSelectionId] = useState<number | null>(null);
  const [menuFamilyId, setMenuFamilyId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dayIndex, setDayIndex] = useState(1);
  const [replaceOpen, setReplaceOpen] = useState(false);
  const [replaceMealIndex, setReplaceMealIndex] = useState<number | null>(null);
  const [consumptionOpen, setConsumptionOpen] = useState(false);
  const [nutritionRefreshKey, setNutritionRefreshKey] = useState(0);
  const [outcomeOpen, setOutcomeOpen] = useState(false);
  const [outcomeMealIndex, setOutcomeMealIndex] = useState<number | null>(null);
  const [actionMeal, setActionMeal] = useState<PlanTodayMeal | null>(null);
  const [shoppingBusy, setShoppingBusy] = useState(false);
  const [ateOtherMeal, setAteOtherMeal] = useState<PlanTodayMeal | null>(null);
  const [skipBusy, setSkipBusy] = useState(false);

  const mealQuery = searchParams.get("meal");
  const recipeIdQuery = searchParams.get("recipeId");
  const menuItemIdQuery = searchParams.get("menuItemId");
  const highlightedRecipeId = recipeIdQuery ? Number(recipeIdQuery) : null;
  const highlightedSlotId = menuItemIdQuery?.trim() || null;

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
      setMenuSelectionId(selected?.id ?? null);
      setMenuFamilyId(selected?.family_id ?? null);
      setCached<CachedSelected>(cacheKey.selectedMenu(mode), {
        menu: loaded,
        selected_at: selected?.selected_at ?? null,
      });
      if (overview) {
        setCached(cacheKey.menuOverview(mode), overview);
      }
      setMenu(loaded);
    } catch {
      setError("Не получилось загрузить меню");
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (!menu) {
      return;
    }
    const resolved = resolvePlanTodayDay(searchParams.get("day"), menu);
    setDayIndex(resolved);
    savePlanTodayDay(resolved);
  }, [menu, searchParams]);

  const returnToToday = useMemo(
    () => planTodayReturnPath(dayIndex, menu),
    [dayIndex, menu],
  );

  function selectDay(index: number) {
    setDayIndex(index);
    savePlanTodayDay(index);
    const next = buildPlanTodaySearchParams(searchParams, index);
    const qs = next.toString();
    router.replace(qs ? `${PLAN_PATHS.today}?${qs}` : PLAN_PATHS.today, {
      scroll: false,
    });
  }

  function openRecipe(recipeId: number) {
    saveScrollPosition(PLAN_PATHS.today, planTodayScrollQuery(dayIndex), window.scrollY);
    router.push(withReturnTo(recipeDetailPath(recipeId), returnToToday));
  }

  useEffect(() => {
    if (!loading && menu) {
      restoreScrollPosition(PLAN_PATHS.today, planTodayScrollQuery(dayIndex));
    }
  }, [loading, menu, dayIndex]);

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
    if (
      searchParams.get("outcome") === "1" ||
      searchParams.get("openMealConsumption") === "1"
    ) {
      setConsumptionOpen(true);
    }
  }, [searchParams, menu]);

  const [checkins, setCheckins] = useState<
    Awaited<ReturnType<typeof fetchTodayMealCheckins>>
  >([]);

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

  const flatMeals = useMemo(
    () => timeline.flatMap((group) => group.meals),
    [timeline],
  );

  useEffect(() => {
    if (loading || !menu || timeline.length === 0) {
      return;
    }
    const selector = highlightedSlotId
      ? `[data-slot-id="${highlightedSlotId}"]`
      : mealQuery
        ? `#meal-card-${mealQuery}`
        : highlightedRecipeId != null && Number.isFinite(highlightedRecipeId)
          ? `[data-recipe-id="${highlightedRecipeId}"]`
          : null;
    if (!selector) {
      return;
    }
    const el = document.querySelector<HTMLElement>(selector);
    if (!el) {
      return;
    }
    const timer = window.setTimeout(() => {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 120);
    return () => window.clearTimeout(timer);
  }, [loading, menu, mealQuery, highlightedRecipeId, highlightedSlotId, timeline]);

  const multiDay = menu ? menuHasMultipleDays(menu) : false;
  const days = menu ? getMenuDays(menu) : [];

  async function handleSkipMeal(meal: PlanTodayMeal) {
    if (!initData || skipBusy) {
      return;
    }
    setSkipBusy(true);
    try {
      await createMealCheckin(initData, mode, {
        meal_type: meal.meal.meal_type,
        actual_status: "skipped",
        planned_date: plannedDate || undefined,
        actual_description: menuMealHeading(meal.meal),
      });
      invalidateCache(cacheKey.menuOverview(mode));
      showToast("Приём пищи пропущен — КБЖУ не учитываем");
      setActionMeal(null);
      void reloadCheckins();
    } catch {
      showToast("Не удалось сохранить. Попробуйте ещё раз.");
    } finally {
      setSkipBusy(false);
    }
  }

  async function handleAddMealToShopping(meal: PlanTodayMeal) {
    if (!initData || meal.meal.recipe_id == null) {
      return;
    }
    setShoppingBusy(true);
    try {
      await addRecipeToShopping(initData, meal.meal.recipe_id, undefined, mode);
      invalidateCache("shopping-list");
      invalidateCache("menu-overview");
      showToast("Ингредиенты добавлены в покупки");
      setActionMeal(null);
    } catch {
      showToast("Не удалось добавить в покупки. Попробуйте ещё раз.");
    } finally {
      setShoppingBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="px-4 pb-8 pt-4">
        <AiProcessLoadingV2
          variant="menu"
          title="PLANAM загружает меню"
          subtitle="Проверяем блюда, покупки и запасы"
        />
      </div>
    );
  }

  if (!menu) {
    return (
      <div className="px-4 py-8">
        <V2EmptyState
          icon={<span aria-hidden>🍽</span>}
          title="Меню пока не собрано"
          description="PLANAM может предложить рацион и список покупок."
          actionLabel="Собрать меню"
          onAction={() => router.push(PLAN_PATHS.generate)}
        />
      </div>
    );
  }

  if (error) {
    return (
      <V2EmptyState
        title="Не получилось загрузить меню"
        description="Попробуйте ещё раз."
        actionLabel="Повторить"
        onAction={() => void load()}
      />
    );
  }

  const dateLabel = formatPlanDayLabel(menu, dayIndex);
  const justSaved = searchParams.get("saved") === "1";

  return (
    <div className="bg-pa-canvas pb-4">
      <div className="px-4 pt-2">
        {justSaved ? (
          <div className="mb-3 rounded-card border border-sage-200 bg-sage-50 px-4 py-3 dark:border-sage-700/40 dark:bg-sage-700/20">
            <p className="pa26-caption font-semibold text-sage-800 dark:text-sage-300">
              План сохранён — отмечайте приёмы пищи ниже
            </p>
          </div>
        ) : null}
        <h1 className="pa26-page-title">Меню</h1>
        <p className="pa26-micro mt-0.5 text-pa-muted">
          Ваш рацион на сегодня · можно заменить любое блюдо
        </p>

        {multiDay ? (
          <div className="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1">
            {days.map((day) => (
              <button
                key={day.day_index}
                type="button"
                onClick={() => selectDay(day.day_index)}
                className={cn(
                  "shrink-0 rounded-pill px-3.5 py-2 pa26-micro font-semibold transition",
                  dayIndex === day.day_index
                    ? "bg-sage-500 text-white dark:bg-sage-400"
                    : "border border-pa-border bg-pa-surface text-pa-muted",
                )}
              >
                {day.label}
              </button>
            ))}
          </div>
        ) : (
          <p className="pa26-caption mt-2 capitalize text-pa-muted">{dateLabel}</p>
        )}

        {plannedDate ? (
          <DayNutritionCard2026
            plannedDate={plannedDate}
            familyId={menuFamilyId ?? context?.family?.id ?? null}
            menuSelectionId={menuSelectionId}
            dayIndex={dayIndex}
            refreshKey={nutritionRefreshKey}
          />
        ) : null}
      </div>

      <div className="mt-3 px-4">
        {timeline.length === 0 ? (
          <V2EmptyState
            title="На этот день нет блюд"
            description="Выберите другой день или пересоберите план."
            actionLabel="Неделя"
            onAction={() => router.push(PLAN_PATHS.week)}
          />
        ) : (
          <div className="space-y-4">
            {timeline.map((group) => (
              <section key={group.slot.id}>
                <h2 className="pa26-section-title flex items-center gap-2">
                  <span aria-hidden>{group.slot.emoji}</span>
                  {group.slot.label}
                </h2>
                <div className="mt-2 space-y-2">
                  {group.meals.map((item) => (
                    <MealRowV2
                      key={`${item.meal.meal_type}-${item.mealIndex}`}
                      item={item}
                      highlighted={
                        (highlightedSlotId != null &&
                          item.slotId === highlightedSlotId) ||
                        (highlightedRecipeId != null &&
                          item.meal.recipe_id === highlightedRecipeId) ||
                        (mealQuery != null &&
                          item.meal.meal_type === mealQuery)
                      }
                      onOpen={() => {
                        if (item.meal.recipe_id) {
                          openRecipe(item.meal.recipe_id);
                        } else {
                          setOutcomeMealIndex(item.mealIndex);
                          setOutcomeOpen(true);
                        }
                      }}
                      onQuickActions={() => setActionMeal(item)}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}

        <div className="mt-4 flex gap-2">
          <V2Button
            variant="secondary"
            className="flex-1"
            onClick={() => {
              setReplaceMealIndex(null);
              setReplaceOpen(true);
            }}
          >
            Заменить блюдо
          </V2Button>
          <V2Button variant="ghost" onClick={() => setConsumptionOpen(true)}>
            {MENU_TODAY_MARK_CONSUMPTION_BUTTON}
          </V2Button>
        </div>
      </div>

      <V2BottomSheet
        open={actionMeal != null}
        title="Что сделать с блюдом?"
        onClose={() => setActionMeal(null)}
      >
        {actionMeal ? (
          <div className="space-y-2 pb-2">
            <p className="pa26-caption -mt-1 text-pa-muted">
              {menuMealHeading(actionMeal.meal)}
            </p>
            {actionMeal.meal.recipe_id ? (
              <SheetAction
                label="Открыть рецепт"
                onClick={() => {
                  const id = actionMeal.meal.recipe_id!;
                  setActionMeal(null);
                  openRecipe(id);
                }}
              />
            ) : null}
            <SheetAction
              label="Заменить блюдо"
              onClick={() => {
                const slotId = actionMeal.slotId;
                const recipeId = actionMeal.meal.recipe_id ?? undefined;
                setActionMeal(null);
                if (slotId) {
                  router.push(
                    buildReplaceCatalogUrl(slotId, recipeId, returnToToday),
                  );
                } else {
                  setReplaceOpen(true);
                }
              }}
            />
            <SheetAction
              label="Ел другое"
              onClick={() => {
                setAteOtherMeal(actionMeal);
                setActionMeal(null);
              }}
            />
            <SheetAction
              label={skipBusy ? "Сохраняем…" : "Пропустил"}
              onClick={() => void handleSkipMeal(actionMeal)}
            />
            {actionMeal.meal.recipe_id ? (
              <SheetAction
                label={shoppingBusy ? "Добавляем…" : "Добавить в покупки"}
                onClick={() => void handleAddMealToShopping(actionMeal)}
              />
            ) : null}
            {actionMeal.slotId ? (
              <SheetAction
                label="Удалить из меню"
                destructive
                onClick={async () => {
                  if (!initData || !actionMeal.slotId) {
                    return;
                  }
                  try {
                    await deleteMenuItem(initData, mode, actionMeal.slotId);
                    invalidateCache(cacheKey.menuOverview(mode));
                    invalidateCache(cacheKey.selectedMenu(mode));
                    showToast("Блюдо удалено из меню");
                    setActionMeal(null);
                    await load();
                  } catch {
                    showToast("Не удалось удалить блюдо. Попробуйте ещё раз.");
                  }
                }}
              />
            ) : null}
          </div>
        ) : null}
      </V2BottomSheet>

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

      <MealEatenSheetV2
        open={ateOtherMeal != null}
        onClose={() => setAteOtherMeal(null)}
        onSaved={() => {
          invalidateCache(cacheKey.menuOverview(mode));
          void reloadCheckins();
        }}
        mealType={ateOtherMeal?.meal.meal_type ?? null}
        mealName={ateOtherMeal ? menuMealHeading(ateOtherMeal.meal) : null}
        plannedDate={plannedDate || null}
        initialStep="other"
        title="Ел другое"
      />

      <MealConsumptionSheetV2
        open={consumptionOpen}
        meals={flatMeals}
        familyId={menuFamilyId ?? context?.family?.id ?? null}
        menuSelectionId={menuSelectionId}
        dayIndex={dayIndex}
        plannedDate={plannedDate || null}
        onClose={() => setConsumptionOpen(false)}
        onSaved={() => {
          showToast(MEAL_CONSUMPTION_SAVED_TOAST);
          setNutritionRefreshKey((k) => k + 1);
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

function MealRowV2({
  item,
  highlighted,
  onOpen,
  onQuickActions,
}: {
  item: PlanTodayMeal;
  highlighted: boolean;
  onOpen: () => void;
  onQuickActions: () => void;
}) {
  const { meal, imageUrl, statusLabel } = item;
  const heading = menuMealHeading(meal);
  const metaParts: string[] = [];
  if (meal.prep_time_minutes > 0) {
    metaParts.push(`${meal.prep_time_minutes} мин`);
  }
  if (meal.calories_estimate != null && meal.calories_estimate > 0) {
    metaParts.push(`${Math.round(meal.calories_estimate)} ккал`);
  }

  return (
    <article
      id={`meal-card-${meal.meal_type}`}
      data-meal-type={meal.meal_type}
      data-recipe-id={meal.recipe_id ?? undefined}
      data-slot-id={item.slotId ?? undefined}
      className={cn(
        "flex items-center gap-3 overflow-hidden rounded-card border bg-pa-surface p-3 shadow-soft dark:shadow-none",
        highlighted
          ? "border-pa-brand ring-2 ring-pa-brand/30"
          : "border-pa-border",
      )}
    >
      <button
        type="button"
        onClick={onOpen}
        className="flex min-w-0 flex-1 items-center gap-3 text-left transition hover:opacity-90"
      >
        <div className="relative size-14 shrink-0 overflow-hidden rounded-control">
          <RecipeImage2026
            imageUrl={imageUrl}
            alt={heading}
            variant="thumb"
            mealType={meal.meal_type}
            className="size-full"
          />
        </div>
        <div className="min-w-0 flex-1">
          <p className="pa26-micro text-pa-muted">{mealTypeLabel(meal.meal_type)}</p>
          <h3 className="pa26-card-title line-clamp-2 leading-snug">{heading}</h3>
          {metaParts.length ? (
            <p className="pa26-micro mt-0.5 text-pa-muted">{metaParts.join(" · ")}</p>
          ) : null}
          {statusLabel ? (
            <p className="pa26-micro mt-0.5 font-medium text-sage-700 dark:text-sage-300">
              {statusLabel}
            </p>
          ) : null}
        </div>
      </button>
      <button
        type="button"
        onClick={onQuickActions}
        className={cn(
          "shrink-0 rounded-pill border border-sage-300 bg-sage-50 px-3 py-2",
          "pa26-micro font-semibold text-sage-700 transition hover:bg-sage-100",
          "dark:border-sage-700/60 dark:bg-sage-900/30 dark:text-sage-300 dark:hover:bg-sage-800/40",
        )}
        aria-label="Действия с блюдом"
      >
        Ещё
      </button>
    </article>
  );
}

function SheetAction({
  label,
  onClick,
  destructive = false,
}: {
  label: string;
  onClick: () => void;
  destructive?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full min-h-[48px] items-center rounded-card border border-pa-border bg-pa-surface px-4 py-3 text-left pa26-card-title transition",
        destructive
          ? "text-pa-error hover:bg-pa-error/5"
          : "hover:bg-sage-50 dark:hover:bg-pa-elevated/40",
      )}
    >
      {label}
    </button>
  );
}
