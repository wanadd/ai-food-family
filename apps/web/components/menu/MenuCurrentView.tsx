"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MenuDayOverview } from "@/components/menu/MenuDayOverview";
import { MenuDayPicker } from "@/components/menu/MenuDayPicker";
import { ReplaceDishModal } from "@/components/menu/ReplaceDishModal";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";
import { SkeletonCard, SkeletonList } from "@/components/ui/Skeleton";
import { useTelegram } from "@/components/TelegramProvider";
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import {
  fetchSelectedMenu,
  replaceDish,
  selectMenu,
} from "@/lib/menu/api";
import {
  dateIsoForDayIndex,
  defaultDayIndex,
  mergeReplaceResult,
  menuHasMultipleDays,
  menuViewForDay,
} from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { MEAL_LABELS } from "@/lib/menu/labels";

const AmaConfirmDialog = dynamic(
  () =>
    import("@/components/subscription/AmaConfirmDialog").then(
      (m) => m.AmaConfirmDialog,
    ),
  { ssr: false },
);

type CachedSelected = { menu: MenuVariant | null; selected_at: string | null };

export function MenuCurrentView() {
  const searchParams = useSearchParams();
  const { initData } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const cachedSelected = initData
    ? getCached<CachedSelected>(cacheKey.selectedMenu(mode))
    : null;
  const [menu, setMenu] = useState<MenuVariant | null>(
    cachedSelected?.menu ?? null,
  );
  const [loading, setLoading] = useState(cachedSelected == null);
  const [replacing, setReplacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replaceTarget, setReplaceTarget] = useState<MenuVariant | null>(null);
  const [pendingMealIndex, setPendingMealIndex] = useState<number | null>(null);
  const {
    overview: subscription,
    ensureLoaded: ensureSubscriptionLoaded,
    refresh: refreshSubscription,
  } = useSubscriptionOverview();
  const amaBalance = subscription?.ama_balance ?? null;
  const amaCosts = subscription?.ama_costs ?? null;
  const [dayIndex, setDayIndex] = useState(() =>
    cachedSelected?.menu ? defaultDayIndex(cachedSelected.menu) : 1,
  );
  const justSaved = searchParams.get("saved") === "1";

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    const key = cacheKey.selectedMenu(mode);
    const primed = getCached<CachedSelected>(key);
    if (primed) {
      const loaded = primed.menu;
      setMenu(loaded);
      if (loaded) setDayIndex(defaultDayIndex(loaded));
      setLoading(false);
    } else {
      setLoading(true);
    }
    try {
      const selected = await fetchSelectedMenu(initData, mode);
      const loaded = selected?.menu ?? null;
      setCached(key, {
        menu: loaded,
        selected_at: selected?.selected_at ?? null,
      });
      setMenu(loaded);
      if (loaded) setDayIndex(defaultDayIndex(loaded));
    } catch {
      setError("Не удалось загрузить план");
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading) return;
    void load();
  }, [load, modeLoading]);

  useEffect(() => {
    if (searchParams.get("replace") === "1" && menu) {
      setReplaceTarget(menuViewForDay(menu, dayIndex));
      setPendingMealIndex(null);
    }
  }, [searchParams, menu, dayIndex]);

  useEffect(() => {
    if (!initData) return;
    ensureSubscriptionLoaded();
  }, [initData, ensureSubscriptionLoaded]);

  async function handleConfirmReplace() {
    if (!initData || !replaceTarget || pendingMealIndex == null || !menu) return;
    setReplacing(true);
    setError(null);
    try {
      const dayMenuPayload = menuViewForDay(menu, dayIndex);
      const updated = await replaceDish(
        initData,
        mode,
        dayMenuPayload,
        pendingMealIndex,
      );
      const merged = mergeReplaceResult(menu, updated, dayIndex);
      await selectMenu(initData, mode, merged);
      invalidateCache("selected-menu");
      invalidateCache("menu-overview");
      invalidateCache("shopping-list");
      invalidateCache("pantry");
      setCached(cacheKey.selectedMenu(mode), {
        menu: merged,
        selected_at: new Date().toISOString(),
      });
      setMenu(merged);
      setReplaceTarget(null);
      setPendingMealIndex(null);
      void refreshSubscription();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Не получилось заменить блюдо. Попробуйте ещё раз.",
      );
    } finally {
      setReplacing(false);
    }
  }

  if (loading || modeLoading) {
    return (
      <ScreenLayout
        title="Текущий план"
        back={{ href: "/menu", label: "Меню" }}
        contentClassName="space-y-3 pb-24"
      >
        <SkeletonCard titleWidth="w-1/2" lines={4} withButton />
        <SkeletonList count={2} />
      </ScreenLayout>
    );
  }

  if (!menu) {
    return (
      <div className="min-h-screen bg-cream px-4 py-16 text-center">
        <p className="text-graphite-600">Активного плана пока нет</p>
        <Link
          href="/menu"
          className="mt-4 inline-block text-sm font-semibold text-sage-700"
        >
          Настроить план
        </Link>
      </div>
    );
  }

  const plannedDate = dateIsoForDayIndex(menu, dayIndex);
  const dayMenu = menuViewForDay(menu, dayIndex);
  const multiDay = menuHasMultipleDays(menu);

  const dateLabel = multiDay
    ? new Date(plannedDate).toLocaleDateString("ru-RU", {
        weekday: "short",
        day: "numeric",
        month: "short",
      })
    : "Сегодня";

  return (
    <ScreenLayout
      title="Текущий план"
      subtitle={
        multiDay
          ? `${dateLabel} · день ${dayIndex}${menu.plan_days ? ` из ${menu.plan_days}` : ""}`
          : dateLabel
      }
      back={{ label: "Меню", href: "/menu" }}
      contentClassName="space-y-3"
    >
      {justSaved ? (
        <div className="rounded-control border border-sage-200 bg-sage-50 px-4 py-3 text-sm text-graphite-900">
          <p className="font-semibold">Меню сохранено</p>
          <p className="mt-1 text-sage-800">Отмечайте приёмы пищи ниже.</p>
        </div>
      ) : null}

      {error ? (
        <p className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      {multiDay ? (
        <MenuDayPicker
          menu={menu}
          dayIndex={dayIndex}
          onDayIndexChange={setDayIndex}
        />
      ) : null}

      {dayMenu ? (
        <MenuDayOverview
          menu={dayMenu}
          plannedDate={plannedDate}
          onReplaceMeal={(index) => {
            setReplaceTarget(dayMenu);
            setPendingMealIndex(index);
          }}
          onUpdated={() => void load()}
        />
      ) : null}

      <Link
        href="/shopping/leftovers"
        className="pa-btn-ghost block text-center text-sm text-graphite-600"
      >
        Остатки блюд →
      </Link>

      {replaceTarget && pendingMealIndex === null ? (
        <ReplaceDishModal
          menu={replaceTarget}
          onClose={() => !replacing && setReplaceTarget(null)}
          onSelectMeal={setPendingMealIndex}
          loading={replacing}
        />
      ) : null}

      <AmaConfirmDialog
        open={pendingMealIndex !== null && replaceTarget !== null}
        title="Заменить блюдо"
        description={(() => {
          const meal =
            replaceTarget && pendingMealIndex !== null
              ? replaceTarget.meals[pendingMealIndex]
              : null;
          if (!meal) return null;
          return (
            <span>
              ПланАм предложит альтернативу для «
              <span className="font-semibold text-graphite-900">{meal.name}</span>
              » ({MEAL_LABELS[meal.meal_type]}).
            </span>
          );
        })()}
        benefit="ПланАм учтёт ваши предпочтения и обновит покупки"
        costAma={amaCosts?.menu_replace_dish ?? null}
        balanceAma={amaBalance}
        busy={replacing}
        confirmLabel="Подтвердить замену"
        onCancel={() => {
          if (!replacing) {
            setPendingMealIndex(null);
            setReplaceTarget(null);
          }
        }}
        onConfirm={() => void handleConfirmReplace()}
      />
    </ScreenLayout>
  );
}
