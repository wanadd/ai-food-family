"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { MenuSubTabs } from "@/components/menu/MenuSubTabs";
import { MenuQuickActionsSheet } from "@/components/menu/MenuQuickActionsSheet";
import { HubTile } from "@/components/ui/HubTile";
import { SkeletonList } from "@/components/ui/Skeleton";
import { ProtectedScreenFallback } from "@/components/auth/ProtectedScreenFallback";
import { useSubscriptionOverview } from "@/components/subscription/SubscriptionProvider";

const AmaConfirmDialog = dynamic(
  () =>
    import("@/components/subscription/AmaConfirmDialog").then(
      (m) => m.AmaConfirmDialog,
    ),
  { ssr: false },
);
import {
  cacheKey,
  getCached,
  invalidate as invalidateCache,
  setCached,
} from "@/lib/cache/session-cache";
import { useProtectedScreen } from "@/lib/use-protected-screen";
import {
  fetchMenuOverview,
  runMenuQuickAction,
  type QuickActionId,
} from "@/lib/menu/overview-api";
import { type QuickActionMeta } from "@/lib/menu/quick-actions";
import { menuHasMultipleDays } from "@/lib/menu/menu-days";
import type { MenuOverview } from "@/lib/menu/overview-types";

type LoadState = "loading" | "success" | "empty" | "error";

export function MenuHub() {
  const router = useRouter();
  const { initData, state: authState } = useProtectedScreen();
  const { mode, loading: modeLoading } = useAppMode();
  const cachedOverview = initData
    ? getCached<MenuOverview>(cacheKey.menuOverview(mode))
    : null;
  const [data, setData] = useState<MenuOverview | null>(cachedOverview);
  const [loadState, setLoadState] = useState<LoadState>(() => {
    if (!cachedOverview) return "loading";
    return cachedOverview.plan_summary.has_selected_menu ? "success" : "empty";
  });
  const [acting, setActing] = useState<QuickActionId | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [quickSheetOpen, setQuickSheetOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<QuickActionMeta | null>(
    null,
  );
  const {
    overview: subscription,
    ensureLoaded: ensureSubscriptionLoaded,
    refresh: refreshSubscription,
  } = useSubscriptionOverview();
  const amaBalance = subscription?.ama_balance ?? null;
  const amaCosts = subscription?.ama_costs ?? null;

  const load = useCallback(
    async (opts: { force?: boolean } = {}) => {
      if (!initData) return;
      const key = cacheKey.menuOverview(mode);
      if (!opts.force) {
        const primed = getCached<MenuOverview>(key);
        if (primed) {
          setData(primed);
          setLoadState(
            primed.plan_summary.has_selected_menu ? "success" : "empty",
          );
        } else {
          setLoadState("loading");
        }
      } else {
        setLoadState("loading");
      }
      console.info("[PlanAm] menu selected request started");
      try {
        const overview = await fetchMenuOverview(initData, mode);
        setCached(key, overview);
        setData(overview);
        if (!overview.plan_summary.has_selected_menu) {
          setLoadState("empty");
          console.info("[PlanAm] menu selected empty");
        } else {
          setLoadState("success");
          console.info("[PlanAm] menu selected loaded");
        }
      } catch (err) {
        setLoadState("error");
        setMessage(
          err instanceof Error ? err.message : "Не удалось загрузить меню",
        );
        console.info("[PlanAm] menu selected failed");
      }
    },
    [initData, mode],
  );

  useEffect(() => {
    console.info("[PlanAm] menu screen mounted");
  }, []);

  useEffect(() => {
    if (authState === "ready") {
      console.info("[PlanAm] menu auth ready");
    }
  }, [authState]);

  useEffect(() => {
    if (modeLoading || authState !== "ready") return;
    void load();
  }, [load, modeLoading, authState]);

  useEffect(() => {
    if (!initData || authState !== "ready") return;
    ensureSubscriptionLoaded();
  }, [initData, authState, ensureSubscriptionLoaded]);

  async function runConfirmedQuickAction(action: QuickActionId) {
    if (!initData) return;
    setActing(action);
    setMessage(null);
    try {
      const result = await runMenuQuickAction(initData, mode, action);
      if (result.redirect_path) {
        router.push(result.redirect_path);
        return;
      }
      if (result.message) setMessage(result.message);
      // Quick actions change the active plan and downstream shopping/pantry.
      invalidateCache("menu-overview");
      invalidateCache("selected-menu");
      invalidateCache("shopping-list");
      invalidateCache("pantry");
      await load({ force: true });
      void refreshSubscription();
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Не получилось выполнить действие. Попробуйте ещё раз.",
      );
    } finally {
      setActing(null);
      setPendingAction(null);
    }
  }

  if (authState !== "ready") {
    return (
      <ProtectedScreenFallback
        loadingMessage="Загрузка меню…"
        telegramMessage="Меню доступно в Telegram Mini App."
      />
    );
  }

  if (loadState === "loading") {
    return (
      <ScreenLayout title="Меню" contentClassName="space-y-3 pb-24">
        <MenuSubTabs />
        <SkeletonList count={3} />
      </ScreenLayout>
    );
  }

  if (loadState === "error") {
    return (
      <ScreenLayout title="Меню" contentClassName="space-y-4 pb-24">
        <div className="rounded-2xl border border-red-100 bg-red-50 p-6 text-center">
          <p className="font-semibold text-graphite-900">Не удалось загрузить меню</p>
          {message ? (
            <p className="mt-2 text-sm text-graphite-600">{message}</p>
          ) : null}
          <div className="mt-4 flex flex-col gap-2">
            <button
              type="button"
              onClick={() => void load()}
              className="pa-btn-primary px-4 py-3 text-sm"
            >
              Повторить
            </button>
            <Link
              href="/"
              className="pa-btn px-4 py-3 text-sm text-center"
            >
              На главную
            </Link>
          </div>
        </div>
      </ScreenLayout>
    );
  }

  if (loadState === "empty" || !data) {
    return (
      <ScreenLayout
        title="Меню"
        subtitle="Что приготовим сегодня?"
        contentClassName="space-y-4 pb-28"
      >
        <MenuSubTabs />
        <div className="pa-card p-5">
          <p className="text-lg font-bold text-graphite-900">
            Давайте составим меню
          </p>
          <p className="mt-1.5 text-sm text-graphite-500">
            ПланАм предложит варианты — выбираете вы.
          </p>
        </div>
        <HubTile
          href="/menu/generate"
          icon="🍽"
          title="Составить меню"
          hint="Учтём цели, семью и запасы"
          tone="primary"
        />
      </ScreenLayout>
    );
  }

  const needsUpdate = data.nutritionist_advice.freshness_status === "needs_update";
  const activeMenu = data.selected_menu?.menu ?? null;
  const multiDayPlan = activeMenu ? menuHasMultipleDays(activeMenu) : false;
  const hasToday = data.today_meals.length > 0;

  return (
    <ScreenLayout
      title="Меню"
      subtitle="Что приготовим сегодня?"
      contentClassName="space-y-3 pb-28"
    >
      <MenuSubTabs />

      {message ? (
        <p className="rounded-control border border-sage-200 bg-sage-50 px-4 py-3 text-sm text-sage-700">
          {message}
        </p>
      ) : null}

      {/* Один главный ответ: что сегодня в плане. */}
      <div className="pa-card p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
          Сегодня в плане
        </p>
        {hasToday ? (
          <ul className="mt-2.5 space-y-1.5">
            {data.today_meals.map((meal) => (
              <li
                key={meal.meal_type}
                className="flex justify-between gap-2 text-sm"
              >
                <span className="text-graphite-500">{meal.label}</span>
                <span className="text-right font-semibold text-graphite-900">
                  {meal.name}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-1.5 text-sm text-graphite-500">
            Меню готово — откройте план на сегодня.
          </p>
        )}
      </div>

      {needsUpdate ? (
        <Link
          href="/menu/generate"
          className="block rounded-control border border-warm/40 bg-warm/10 px-4 py-2.5 text-sm font-semibold text-graphite-700"
        >
          Цель изменилась — пересобрать меню →
        </Link>
      ) : null}

      {/* Главная кнопка + «Настроить» (быстрые действия в листе). */}
      <HubTile
        href="/menu/current"
        icon="🍽"
        title={multiDayPlan ? "Открыть все дни" : "Открыть план"}
        hint="Блюда, замены и отметки"
        tone="primary"
      />
      <HubTile
        icon="⚙️"
        title="Настроить меню"
        hint="Дешевле, из запасов, больше белка…"
        onClick={() => setQuickSheetOpen(true)}
      />

      <MenuQuickActionsSheet
        open={quickSheetOpen}
        busy={Boolean(acting)}
        onClose={() => setQuickSheetOpen(false)}
        onPick={(action) => {
          setQuickSheetOpen(false);
          setPendingAction(action);
        }}
      />

      <AmaConfirmDialog
        open={pendingAction !== null}
        title={pendingAction?.label ?? ""}
        description={pendingAction?.description ?? ""}
        benefit={
          pendingAction
            ? "Меню и список покупок подстроятся под выбранную опцию"
            : undefined
        }
        costAma={
          pendingAction?.costKey != null
            ? (amaCosts?.[pendingAction.costKey] ?? null)
            : null
        }
        balanceAma={amaBalance}
        busy={Boolean(acting)}
        cancelLabel="Передумал"
        confirmLabel="Да, применить"
        onCancel={() => {
          if (!acting) setPendingAction(null);
        }}
        onConfirm={() => {
          if (pendingAction) void runConfirmedQuickAction(pendingAction.id);
        }}
      />
    </ScreenLayout>
  );
}
