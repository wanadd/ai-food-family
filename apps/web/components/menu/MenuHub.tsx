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
import type { MenuOverview } from "@/lib/menu/overview-types";

const QUICK_ACTIONS: { id: QuickActionId; label: string }[] = [
  { id: "cheaper", label: "Сделать дешевле" },
  { id: "more_pantry", label: "Использовать больше запасов" },
  { id: "more_protein", label: "Больше белка" },
  { id: "less_cooking_time", label: "Меньше времени на готовку" },
  { id: "replace_dish", label: "Заменить блюдо" },
];

function formatRub(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toLocaleString("ru-RU")} ₽`;
}

function ProCoverageBar({ label, percent }: { label: string; percent: number }) {
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span className="text-stone-600">{label}</span>
        <span className="font-semibold text-stone-900">{percent}%</span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full bg-stone-100">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all"
          style={{ width: `${Math.min(100, percent)}%` }}
        />
      </div>
    </div>
  );
}

export function MenuHub() {
  const router = useRouter();
  const { initData, state: authState } = useProtectedScreen();
  const { mode, loading: modeLoading } = useAppMode();
  const [data, setData] = useState<MenuOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState<QuickActionId | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!initData) {
      return;
    }
    setLoading(true);
    try {
      const overview = await fetchMenuOverview(initData, mode);
      setData(overview);
      console.info("[PlanAm] Menu loaded");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Не удалось загрузить меню",
      );
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

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

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-stone-50">
        <PageLoading message="Загрузка меню…" />
      </div>
    );
  }

  const { plan_summary: plan, nutritionist_advice: advice } = data;
  const needsUpdate = advice.freshness_status === "needs_update";

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

      <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
          ПланАм рекомендует
        </p>
        <p className="mt-2 text-2xl font-bold text-stone-900">{plan.goal_label}</p>
        <p className="mt-1 text-sm text-stone-600">{plan.persons_label}</p>
        <p className="text-sm text-stone-600">Тип плана: {plan.plan_mode_label}</p>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
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
        {plan.has_selected_menu && plan.menu_title ? (
          <Link
            href="/menu/current"
            className="mt-4 block rounded-xl border border-emerald-200 bg-white px-3 py-2.5 text-sm font-semibold text-emerald-800"
          >
            {plan.menu_title} →
          </Link>
        ) : (
          <Link
            href="/menu/generate"
            className="mt-4 block rounded-xl bg-emerald-600 px-3 py-2.5 text-center text-sm font-semibold text-white"
          >
            Составить меню
          </Link>
        )}
      </section>

      {data.why_reasons.length > 0 ? (
        <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
          <p className="text-sm font-bold text-stone-900">Почему выбран этот план</p>
          <p className="mt-1 text-xs text-stone-500">ПланАм учёл:</p>
          <ul className="mt-2 space-y-1.5">
            {data.why_reasons.map((r) => (
              <li key={r.text} className="flex gap-2 text-sm text-stone-700">
                <span className="text-emerald-600">{r.included ? "✓" : "·"}</span>
                <span>{r.text}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section
        className={`rounded-2xl border p-4 shadow-sm ${
          needsUpdate
            ? "border-amber-200 bg-amber-50/50"
            : "border-violet-100 bg-violet-50/30"
        }`}
      >
        <div className="flex items-start justify-between gap-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-violet-800">
            Рекомендация нутрициолога
          </p>
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
              needsUpdate
                ? "bg-amber-200 text-amber-950"
                : advice.freshness_status === "no_menu"
                  ? "bg-stone-200 text-stone-700"
                  : "bg-emerald-200 text-emerald-900"
            }`}
          >
            {needsUpdate
              ? "Требует обновления"
              : advice.freshness_status === "no_menu"
                ? "Нет меню"
                : "Актуально"}
          </span>
        </div>
        <p className="mt-2 font-semibold text-stone-900">{advice.title}</p>
        <p className="mt-1 text-sm leading-relaxed text-stone-600">{advice.body}</p>
        {advice.update_reason ? (
          <p className="mt-2 text-xs font-medium text-amber-900">
            {advice.update_reason}
          </p>
        ) : null}
        {needsUpdate ? (
          <Link
            href="/menu/generate"
            className="mt-3 inline-block text-sm font-semibold text-emerald-700"
          >
            Обновить меню →
          </Link>
        ) : null}
      </section>

      {data.is_pro && data.pro_coverage ? (
        <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
          <p className="text-sm font-bold text-stone-900">Покрытие целей</p>
          <div className="mt-3 space-y-3">
            <ProCoverageBar label="Белок" percent={data.pro_coverage.protein_percent} />
            <ProCoverageBar label="Клетчатка" percent={data.pro_coverage.fiber_percent} />
            <ProCoverageBar label="Калории" percent={data.pro_coverage.calories_percent} />
            <ProCoverageBar label="Вода" percent={data.pro_coverage.water_percent} />
          </div>
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
              className="min-h-[44px] rounded-xl border border-stone-200 bg-stone-50 px-2 py-2.5 text-xs font-semibold text-stone-800 disabled:opacity-50 active:scale-[0.98]"
            >
              {acting === action.id ? "…" : action.label}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-2">
        <Link
          href="/recipes"
          className="flex items-center justify-between rounded-2xl border border-stone-100 bg-white px-4 py-3.5 shadow-sm"
        >
          <span className="font-semibold text-stone-900">Каталог рецептов</span>
          <span className="text-stone-400">→</span>
        </Link>
        <Link
          href="/menu/event"
          className="flex items-center justify-between rounded-2xl border border-violet-100 bg-violet-50/50 px-4 py-3.5 shadow-sm"
        >
          <span className="font-semibold text-stone-900">Создать событие</span>
          <span className="text-stone-400">→</span>
        </Link>
        {data.meal_leftovers_count > 0 || mode === "family" ? (
          <Link
            href="/menu/leftovers"
            className="flex items-center justify-between rounded-2xl border border-stone-100 bg-white px-4 py-3.5 shadow-sm"
          >
            <span className="font-semibold text-stone-900">
              Остатки блюд
              {data.meal_leftovers_count > 0
                ? ` (${data.meal_leftovers_count})`
                : ""}
            </span>
            <span className="text-stone-400">→</span>
          </Link>
        ) : null}
        <Link
          href="/menu/settings"
          className="flex items-center justify-between rounded-2xl border border-dashed border-stone-200 bg-stone-50/80 px-4 py-3.5"
        >
          <span className="font-semibold text-stone-800">Настройки меню</span>
          <span className="text-stone-400">→</span>
        </Link>
      </section>
    </ScreenLayout>
  );
}
