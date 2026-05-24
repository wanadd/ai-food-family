"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { PageLoading } from "@/components/ui/PageLoading";
import { ProtectedScreenFallback } from "@/components/auth/ProtectedScreenFallback";
import { useProtectedScreen } from "@/lib/use-protected-screen";
import {
  fetchMenuOverview,
  runMenuQuickAction,
  type QuickActionId,
} from "@/lib/menu/overview-api";
import { menuHasMultipleDays } from "@/lib/menu/menu-days";
import type { MenuOverview } from "@/lib/menu/overview-types";

const QUICK_ACTIONS: { id: QuickActionId; label: string }[] = [
  { id: "cheaper", label: "Сделать дешевле" },
  { id: "more_pantry", label: "Использовать запасы" },
  { id: "more_protein", label: "Больше белка" },
  { id: "less_cooking_time", label: "Меньше времени на готовку" },
  { id: "replace_dish", label: "Заменить блюдо" },
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
  const [data, setData] = useState<MenuOverview | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [acting, setActing] = useState<QuickActionId | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const load = useCallback(async () => {
    if (!initData) {
      return;
    }
    setLoadState("loading");
    console.info("[PlanAm] menu selected request started");
    try {
      const overview = await fetchMenuOverview(initData, mode);
      setData(overview);
      if (!overview.plan_summary.has_selected_menu) {
        setLoadState("empty");
        console.info("[PlanAm] menu selected empty");
      } else {
        setLoadState("success");
        console.info("[PlanAm] menu selected loaded");
      }
    } catch (err) {
      setData(null);
      setLoadState("error");
      setMessage(
        err instanceof Error ? err.message : "Не удалось загрузить меню",
      );
      console.info("[PlanAm] menu selected failed");
    }
  }, [initData, mode]);

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

  async function handleQuickAction(action: QuickActionId) {
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
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Не удалось выполнить действие");
    } finally {
      setActing(null);
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
      <div className="min-h-screen bg-stone-50">
        <PageLoading message="Загрузка меню…" />
      </div>
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
        <div className="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm">
          <p className="text-lg font-bold text-stone-900">План пока не создан</p>
          <p className="mt-2 text-sm text-stone-600">
            ПланАм может составить меню с учётом:
          </p>
          <ul className="mt-3 space-y-1.5 text-sm text-stone-700">
            {[
              "цели",
              "семьи",
              "запасов",
              "аллергий",
              "ограничений",
              "бюджета",
              "времени готовки",
            ].map((item) => (
              <li key={item} className="flex items-center gap-2">
                <span className="text-emerald-600" aria-hidden>
                  ✓
                </span>
                {item}
              </li>
            ))}
          </ul>
          <Link
            href="/menu/generate"
            className="mt-6 flex min-h-[48px] w-full items-center justify-center rounded-2xl bg-emerald-600 px-6 py-3.5 text-base font-semibold text-white shadow-md shadow-emerald-200/40"
          >
            Составить меню
          </Link>
        </div>
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
      subtitle="ПланАм рекомендует — вы выбираете"
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
            Цель изменилась — рекомендуется обновить меню
          </p>
          {advice.update_reason ? (
            <p className="mt-1 text-xs text-amber-900">{advice.update_reason}</p>
          ) : null}
          <Link
            href="/menu/generate"
            className="mt-3 inline-block rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white"
          >
            Обновить меню
          </Link>
        </section>
      ) : null}

      <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
          ПланАм рекомендует
        </p>
        <p className="mt-2 text-xl font-bold text-stone-900">{plan.goal_label}</p>
        <p className="mt-1 text-sm text-stone-600">{plan.persons_label}</p>
        <p className="text-sm text-stone-600">Тип плана: {plan.plan_mode_label}</p>
        <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
          <div>
            <dt className="text-stone-500">Стоимость</dt>
            <dd className="font-bold text-stone-900">
              {formatRub(plan.estimated_cost_rub)}
            </dd>
          </div>
          <div>
            <dt className="text-stone-500">Запасы</dt>
            <dd className="font-bold text-stone-900">
              {plan.pantry_used_rub != null
                ? `на ${formatRub(plan.pantry_used_rub)}`
                : "—"}
            </dd>
          </div>
          {plan.savings_rub != null ? (
            <div className="col-span-2">
              <dt className="text-stone-500">Экономия</dt>
              <dd className="font-bold text-emerald-800">
                {formatRub(plan.savings_rub)}
              </dd>
            </div>
          ) : null}
        </dl>
      </section>

      <section
        className={`rounded-2xl border p-4 shadow-sm ${
          needsUpdate
            ? "border-amber-200 bg-amber-50/50"
            : "border-violet-100 bg-violet-50/30"
        }`}
      >
        <p className="text-xs font-semibold uppercase tracking-wide text-violet-800">
          Рекомендация нутрициолога
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

      {data.today_meals.length > 0 ? (
        <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
          <p className="text-sm font-bold text-stone-900">Сегодня</p>
          <ul className="mt-2 space-y-2">
            {data.today_meals.map((meal) => (
              <li
                key={meal.meal_type}
                className="flex justify-between gap-2 text-sm"
              >
                <span className="text-stone-500">{meal.label}</span>
                <span className="font-medium text-stone-900">{meal.name}</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
            <Link
              href="/menu/current"
              className="text-sm font-semibold text-emerald-700"
            >
              Подробнее →
            </Link>
            {multiDayPlan ? (
              <Link
                href="/menu/current"
                className="text-sm font-semibold text-emerald-700"
              >
                Открыть все дни →
              </Link>
            ) : null}
          </div>
        </section>
      ) : null}

      {data.home_attendance ? (
        <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
          <p className="text-sm font-bold text-stone-900">Сегодня дома едят</p>
          <ul className="mt-2 space-y-1 text-sm text-stone-700">
            <li>Завтрак: {data.home_attendance.breakfast_home} человек</li>
            <li>Обед: {data.home_attendance.lunch_home} человек</li>
            <li>Ужин: {data.home_attendance.dinner_home} человек</li>
          </ul>
          <Link
            href="/menu/settings"
            className="mt-3 inline-block text-sm font-semibold text-emerald-700"
          >
            Изменить на сегодня →
          </Link>
        </section>
      ) : null}

      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        <p className="text-sm font-bold text-stone-900">Быстрые действия</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.id}
              type="button"
              disabled={Boolean(acting)}
              onClick={() => void handleQuickAction(action.id)}
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

      <Link
        href="/menu/current"
        className="flex items-center justify-between rounded-2xl border border-emerald-100 bg-white px-4 py-3.5 shadow-sm"
      >
        <span className="font-semibold text-stone-900">
          {plan.menu_title ?? "Текущее меню"}
        </span>
        <span className="text-stone-400">→</span>
      </Link>

      <Link
        href="/menu/leftovers"
        className="flex items-center justify-between rounded-2xl border border-stone-100 bg-white px-4 py-3.5 shadow-sm"
      >
        <span className="font-semibold text-stone-900">Остатки блюд</span>
        <span className="text-sm text-stone-500">
          {data.meal_leftovers_count > 0
            ? `${data.meal_leftovers_count} · `
            : ""}
          →
        </span>
      </Link>

      <Link
        href="/recipes"
        className="flex items-center justify-between rounded-2xl border border-stone-100 bg-white px-4 py-3.5 shadow-sm"
      >
        <span className="font-semibold text-stone-900">Рецепты</span>
        <span className="text-stone-400">→</span>
      </Link>
    </ScreenLayout>
  );
}
