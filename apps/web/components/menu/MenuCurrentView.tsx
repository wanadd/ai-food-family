"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";

const AmaConfirmDialog = dynamic(
  () =>
    import("@/components/subscription/AmaConfirmDialog").then(
      (m) => m.AmaConfirmDialog,
    ),
  { ssr: false },
);
import { MealCheckinPanel } from "@/components/menu/MealCheckinPanel";
import { MenuDayPicker } from "@/components/menu/MenuDayPicker";
import { MenuVariantCard } from "@/components/menu/MenuVariantCard";
import { ReplaceDishModal } from "@/components/menu/ReplaceDishModal";
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
  menuHasMultipleDays,
  menuViewForDay,
} from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { MEAL_LABELS } from "@/lib/menu/labels";

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
  const [selectedAt, setSelectedAt] = useState<string | null>(
    cachedSelected?.selected_at ?? null,
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
      setSelectedAt(primed.selected_at);
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
      setSelectedAt(selected?.selected_at ?? null);
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
      setReplaceTarget(menu);
    }
  }, [searchParams, menu]);

  useEffect(() => {
    if (!initData) return;
    ensureSubscriptionLoaded();
  }, [initData, ensureSubscriptionLoaded]);

  async function handleConfirmReplace() {
    if (!initData || !replaceTarget || pendingMealIndex == null || !menu) return;
    setReplacing(true);
    setError(null);
    try {
      const updated = await replaceDish(
        initData,
        mode,
        replaceTarget,
        pendingMealIndex,
      );
      await selectMenu(initData, mode, updated);
      // Plan changed → drop overview, selected and downstream caches.
      invalidateCache("selected-menu");
      invalidateCache("menu-overview");
      invalidateCache("shopping-list");
      invalidateCache("pantry");
      setCached(cacheKey.selectedMenu(mode), {
        menu: updated,
        selected_at: new Date().toISOString(),
      });
      setMenu(updated);
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

  const plannedDate = menu ? dateIsoForDayIndex(menu, dayIndex) : "";
  const dayMenu = menu ? menuViewForDay(menu, dayIndex) : null;
  const multiDay = menu ? menuHasMultipleDays(menu) : false;

  const dateLabel = multiDay
    ? new Date(plannedDate).toLocaleDateString("ru-RU", {
        weekday: "short",
        day: "numeric",
        month: "short",
      })
    : selectedAt
      ? new Date(selectedAt).toLocaleDateString("ru-RU", {
          day: "numeric",
          month: "long",
        })
      : "Сегодня";

  return (
    <ScreenLayout
      title={menu.title}
      subtitle={
        multiDay
          ? `${dateLabel} · день ${dayIndex}${menu.plan_days ? ` из ${menu.plan_days}` : ""}`
          : `${dateLabel} · активен`
      }
      back={{ label: "Меню", href: "/menu" }}
      contentClassName="space-y-4"
    >
        {justSaved ? (
          <div className="rounded-control border border-sage-200 bg-sage-50 px-4 py-3 text-sm text-graphite-900">
            <p className="font-semibold">Меню сохранено</p>
            <p className="mt-1 text-sage-800">
              План активен — отмечайте приёмы пищи и смотрите другие дни ниже.
            </p>
          </div>
        ) : null}

        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
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
          <MenuVariantCard
            menu={dayMenu}
            selected
            onSelect={() => {}}
            onReplace={() => setReplaceTarget(dayMenu)}
            selecting={false}
          />
        ) : null}

        {dayMenu ? (
          <MealCheckinPanel
            menu={dayMenu}
            plannedDate={plannedDate}
            onUpdated={() => void load()}
          />
        ) : null}

        <Link
          href="/shopping/leftovers"
          className="pa-btn flex min-h-[44px] items-center justify-center px-4 py-3 text-sm"
        >
          Остатки блюд
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
              ПланАм предложит альтернативу для блюда
              {" «"}
              <span className="font-semibold text-graphite-900">{meal.name}</span>
              {"» ("}
              {MEAL_LABELS[meal.meal_type]}
              {"). "}
              Активный план обновится, список покупок пересчитается. Если новое
              блюдо не подойдёт — можно заменить ещё раз.
            </span>
          );
        })()}
        benefit="ПланАм учтёт ваши предпочтения и обновит покупки"
        costAma={amaCosts?.menu_replace_dish ?? null}
        balanceAma={amaBalance}
        busy={replacing}
        confirmLabel="Подтвердить замену"
        onCancel={() => {
          if (!replacing) setPendingMealIndex(null);
        }}
        onConfirm={() => void handleConfirmReplace()}
      />
    </ScreenLayout>
  );
}
