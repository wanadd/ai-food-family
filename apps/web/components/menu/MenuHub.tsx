"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
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
import { menuHasMultipleDays } from "@/lib/menu/menu-days";
import type { MenuOverview } from "@/lib/menu/overview-types";

type QuickActionMeta = {
  id: QuickActionId;
  label: string;
  description: string;
  /**
   * Backend cost key in SubscriptionOverview.ama_costs. If unset, the
   * action is assumed free or server-decided and we show ``может
   * потребовать Амы``.
   */
  costKey?: string;
};

const QUICK_ACTIONS: QuickActionMeta[] = [
  {
    id: "cheaper",
    label: "Сделать дешевле",
    description:
      "ПланАм пересоберёт меню с акцентом на экономные блюда. Активный план изменится, список покупок пересчитается.",
  },
  {
    id: "more_pantry",
    label: "Использовать запасы",
    description:
      "ПланАм постарается использовать продукты, которые уже есть в запасах, и обновит список покупок.",
  },
  {
    id: "more_protein",
    label: "Больше белка",
    description:
      "ПланАм увеличит долю белковых блюд в плане. Покупки обновятся под новые ингредиенты.",
  },
  {
    id: "less_cooking_time",
    label: "Меньше времени на готовку",
    description:
      "ПланАм заменит длительные рецепты на более быстрые. Активный план и покупки обновятся.",
  },
  {
    id: "replace_dish",
    label: "Заменить блюдо",
    description:
      "Выберите блюдо в активном плане — ПланАм предложит альтернативу с учётом ваших ограничений.",
    costKey: "menu_replace_dish",
  },
];

type LoadState = "loading" | "success" | "empty" | "error";

function formatRub(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toLocaleString("ru-RU")} ₽`;
}

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
  const [settingsOpen, setSettingsOpen] = useState(false);
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
        <SkeletonList count={3} />
      </ScreenLayout>
    );
  }

  if (loadState === "error") {
    return (
      <ScreenLayout title="Меню" contentClassName="space-y-4 pb-24">
        <div className="rounded-2xl border border-red-100 bg-red-50 p-6 text-center">
          <p className="font-semibold text-stone-900">Не удалось загрузить меню</p>
          {message ? (
            <p className="mt-2 text-sm text-stone-600">{message}</p>
          ) : null}
          <div className="mt-4 flex flex-col gap-2">
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white"
            >
              Повторить
            </button>
            <Link
              href="/"
              className="rounded-xl border border-stone-200 bg-white px-4 py-3 text-sm font-semibold text-stone-800"
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
      <ScreenLayout title="Меню" contentClassName="space-y-4 pb-24">
        <section className="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm">
          <p className="text-lg font-bold text-stone-900">План пока не создан</p>
          <p className="mt-2 text-sm text-stone-600">
            ПланАм предложит варианты — вы сможете выбрать или заменить
            любое блюдо.
          </p>
          <Link
            href="/menu/generate"
            className="mt-5 flex min-h-[48px] w-full items-center justify-center rounded-2xl bg-emerald-600 px-6 py-3.5 text-base font-semibold text-white shadow-md shadow-emerald-200/40"
          >
            Составить меню
          </Link>
          <p className="mt-2 text-xs text-stone-500">
            После генерации можно выбрать вариант, заменить блюдо
            или начать с чистого листа.
          </p>
          <details className="mt-4 text-sm text-stone-600">
            <summary className="cursor-pointer font-semibold text-stone-700">
              Что будет учтено
            </summary>
            <ul className="mt-2 space-y-1.5">
              {[
                "цель и режим питания",
                "состав семьи",
                "что уже есть в запасах",
                "аллергии и ограничения",
                "бюджет",
                "время на готовку",
              ].map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <span className="text-emerald-600" aria-hidden>
                    ✓
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </details>
        </section>
      </ScreenLayout>
    );
  }

  const { plan_summary: plan, nutritionist_advice: advice } = data;
  const needsUpdate = advice.freshness_status === "needs_update";
  const adviceFailed = Boolean(data.nutritionist_advice_error);
  const activeMenu = data.selected_menu?.menu ?? null;
  const multiDayPlan = activeMenu ? menuHasMultipleDays(activeMenu) : false;

  return (
    <ScreenLayout
      title="Меню"
      subtitle="ПланАм подскажет — выбираете вы"
      contentClassName="space-y-3 pb-32"
    >
      {message ? (
        <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {message}
        </p>
      ) : null}

      {needsUpdate ? (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-950">
            Цель изменилась — ПланАм может пересобрать меню под неё
          </p>
          {advice.update_reason ? (
            <p className="mt-1 text-xs text-amber-900">{advice.update_reason}</p>
          ) : null}
          <p className="mt-1 text-xs text-amber-900/80">
            Можно оставить как есть — текущий план продолжит работать.
          </p>
          <Link
            href="/menu/generate"
            className="mt-3 inline-block rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white"
          >
            Пересобрать меню
          </Link>
        </section>
      ) : null}

      {data.today_meals.length > 0 ? (
        <section className="rounded-3xl border border-emerald-100 bg-gradient-to-b from-emerald-50/70 to-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Сегодня в плане
          </p>
          <ul className="mt-3 space-y-2">
            {data.today_meals.map((meal) => (
              <li
                key={meal.meal_type}
                className="flex justify-between gap-2 text-sm"
              >
                <span className="text-stone-500">{meal.label}</span>
                <span className="text-right font-semibold text-stone-900">
                  {meal.name}
                </span>
              </li>
            ))}
          </ul>
          <Link
            href="/menu/current"
            className="mt-4 flex min-h-[44px] w-full items-center justify-center rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition active:scale-[0.99]"
          >
            {multiDayPlan ? "Открыть все дни" : "Открыть план"}
          </Link>
        </section>
      ) : null}

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
          План
        </p>
        <p className="mt-1 text-sm font-semibold text-stone-900">
          {plan.goal_label} · {plan.persons_label}
        </p>
        <p className="mt-1 text-xs text-stone-500">
          Купить на {formatRub(plan.estimated_cost_rub)}
          {plan.pantry_used_rub != null
            ? ` · из запасов на ${formatRub(plan.pantry_used_rub)}`
            : ""}
          {plan.savings_rub != null
            ? ` · экономия ${formatRub(plan.savings_rub)}`
            : ""}
        </p>
        <details className="mt-3 text-sm text-stone-600">
          <summary className="cursor-pointer text-xs font-semibold text-emerald-700">
            Подробнее о плане
          </summary>
          <p className="mt-2">Тип плана: {plan.plan_mode_label}</p>
          {data.home_attendance ? (
            <ul className="mt-2 space-y-1">
              <li>Завтрак дома: {data.home_attendance.breakfast_home} чел.</li>
              <li>Обед дома: {data.home_attendance.lunch_home} чел.</li>
              <li>Ужин дома: {data.home_attendance.dinner_home} чел.</li>
            </ul>
          ) : null}
          {data.home_attendance ? (
            <Link
              href="/menu/settings"
              className="mt-2 inline-block text-xs font-semibold text-emerald-700"
            >
              Изменить на сегодня →
            </Link>
          ) : null}
        </details>
      </section>

      <section
        className={`rounded-2xl border p-4 shadow-sm ${
          needsUpdate
            ? "border-amber-200 bg-amber-50/50"
            : "border-violet-100 bg-violet-50/30"
        }`}
      >
        <p className="text-xs font-semibold uppercase tracking-wide text-violet-800">
          Совет нутрициолога
        </p>
        {adviceFailed ? (
          <p className="mt-2 text-sm text-stone-600">
            Совет временно недоступен. Основное меню загружено.
          </p>
        ) : (
          <>
            <p className="mt-2 font-semibold text-stone-900">{advice.title}</p>
            <p className="mt-1 text-sm leading-relaxed text-stone-600">
              {advice.body}
            </p>
          </>
        )}
      </section>

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-sm font-bold text-stone-900">Быстрые действия</p>
        <p className="mt-1 text-xs text-stone-500">
          ПланАм предложит вариант — вы решаете, применять или нет.
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.id}
              type="button"
              disabled={Boolean(acting)}
              onClick={() => setPendingAction(action)}
              className="min-h-[44px] rounded-xl border border-stone-200 bg-stone-50 px-2 py-2.5 text-xs font-semibold text-stone-800 disabled:opacity-50"
            >
              {acting === action.id ? "…" : action.label}
            </button>
          ))}
        </div>
      </section>

      {data.settings_summary ? (
        <section className="rounded-2xl border border-dashed border-stone-200 bg-stone-50/80">
          <button
            type="button"
            onClick={() => setSettingsOpen((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3.5 text-left"
          >
            <span className="font-semibold text-stone-800">Настройки меню</span>
            <span className="text-stone-400">{settingsOpen ? "▲" : "▼"}</span>
          </button>
          {settingsOpen ? (
            <div className="border-t border-stone-200 px-4 pb-4 pt-2 text-sm text-stone-600">
              <p>Участников: {data.settings_summary.persons_count}</p>
              <p>Цель: {data.settings_summary.goal_label}</p>
              <p>Режим: {data.settings_summary.plan_mode_label}</p>
              <p>
                Напитки: {data.settings_summary.include_drinks ? "да" : "нет"}
              </p>
              <p>
                Запасы: {data.settings_summary.use_pantry ? "использовать" : "нет"}
              </p>
              <Link
                href="/menu/settings"
                className="mt-3 inline-block font-semibold text-emerald-700"
              >
                Изменить →
              </Link>
            </div>
          ) : null}
        </section>
      ) : null}

      <div className="grid grid-cols-2 gap-2">
        <Link
          href="/menu/leftovers"
          className="flex items-center justify-between rounded-2xl border border-stone-100 bg-white px-3 py-3 text-sm shadow-sm"
        >
          <span className="font-semibold text-stone-900">Остатки</span>
          <span className="text-stone-400">
            {data.meal_leftovers_count > 0
              ? `${data.meal_leftovers_count} →`
              : "→"}
          </span>
        </Link>
        <Link
          href="/recipes"
          className="flex items-center justify-between rounded-2xl border border-stone-100 bg-white px-3 py-3 text-sm shadow-sm"
        >
          <span className="font-semibold text-stone-900">Рецепты</span>
          <span className="text-stone-400">→</span>
        </Link>
      </div>

      <AmaConfirmDialog
        open={pendingAction !== null}
        title={pendingAction?.label ?? ""}
        description={pendingAction?.description ?? ""}
        costAma={
          pendingAction?.costKey != null
            ? (amaCosts?.[pendingAction.costKey] ?? null)
            : null
        }
        balanceAma={amaBalance}
        busy={Boolean(acting)}
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
