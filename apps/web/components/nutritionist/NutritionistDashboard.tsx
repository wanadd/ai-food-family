"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { NutritionistChat } from "@/components/nutritionist/NutritionistChat";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
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
import { CareTelegramBlock } from "@/components/care/CareTelegramBlock";
import { buildDailyTip } from "@/lib/nutritionist/daily-tip";
import { buildFamilySummary } from "@/lib/nutritionist/family-summary";
import { buildStatCards, getOverallProgress } from "@/lib/nutritionist/metrics";
import { fetchShoppingList } from "@/lib/shopping/api";
import { fetchSubscriptionOverview } from "@/lib/subscription/api";
import { getNutritionistAskCost } from "@/lib/subscription/ama";
import type { ShoppingList } from "@/lib/shopping/types";

const QUICK_ACTIONS: { id: string; label: string; prompt?: string }[] = [
  { id: "protein", label: "Добрать белок", prompt: "Как добрать белок сегодня?" },
  {
    id: "healthier",
    label: "Сделать меню полезнее",
    prompt: "Как сделать меню полезнее?",
  },
  {
    id: "pantry",
    label: "Что из запасов",
    prompt: "Что приготовить из запасов?",
  },
  {
    id: "calories",
    label: "Снизить калории",
    prompt: "Как снизить калории без голода?",
  },
  { id: "ask", label: "Спросить нутрициолога" },
];

const PRO_FEATURES = [
  "Анализ питания за неделю",
  "Спортивные цели",
  "Прогресс веса",
  "Персональные уведомления",
];

function ModeLabel({
  mode,
  personsCount,
  familyName,
}: {
  mode: string;
  personsCount: number;
  familyName: string | null;
}) {
  if (mode === "family" && familyName) {
    return (
      <p className="mt-1 text-sm text-stone-500">
        Семейный · {personsCount}{" "}
        {personsCount === 1 ? "участник" : "участников"}
      </p>
    );
  }
  return (
    <p className="mt-1 text-sm text-stone-500">
      {personsCount === 1 ? "Личный" : `Личный · ${personsCount} чел.`}
    </p>
  );
}

export function NutritionistDashboard() {
  const { initData, isTelegram } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [pantry, setPantry] = useState<PantryList | null>(null);
  const [shopping, setShopping] = useState<ShoppingList | null>(null);
  const [chatPrompt, setChatPrompt] = useState<string | null>(null);
  const [amaBalance, setAmaBalance] = useState(0);
  const [amaAskCost, setAmaAskCost] = useState(2);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [nutrition, selected, pantryList, shoppingList, sub] =
        await Promise.all([
          fetchNutritionProfile(initData).catch(() => null),
          fetchSelectedMenu(initData, mode).catch(() => null),
          fetchPantry(initData, mode).catch(() => null),
          fetchShoppingList(initData, mode).catch(() => null),
          fetchSubscriptionOverview(initData, mode).catch(() => null),
        ]);
      setProfile(nutrition);
      setMenu(selected?.menu ?? null);
      setPantry(pantryList);
      setShopping(shoppingList);
      if (sub) {
        setAmaBalance(sub.ama_balance);
        setAmaAskCost(getNutritionistAskCost(sub.ama_costs));
      }
    } finally {
      setLoading(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading) return;
    void load();
  }, [load, modeLoading]);

  const personsCount = getPersonsCount(mode, context);
  const goalLabel = getNutritionGoalLabel(profile);
  const profileComplete = isNutritionProfileComplete(profile);
  const progress = getOverallProgress(profile, Boolean(menu), shopping);
  const statCards = buildStatCards(profile, menu, shopping);
  const dailyTip = buildDailyTip({
    profile,
    menu,
    pantry,
    pantryActiveCount: pantry?.active_count ?? 0,
  });

  const familySummary = useMemo(() => {
    if (mode !== "family" || !context?.family) return null;
    return buildFamilySummary(context.family);
  }, [mode, context?.family]);

  function handleQuickAction(action: (typeof QUICK_ACTIONS)[number]) {
    document
      .getElementById("nutritionist-chat")
      ?.scrollIntoView({ behavior: "smooth" });
    if (action.prompt) {
      setChatPrompt(action.prompt);
    }
  }

  if (!initData && !isTelegram && !loading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-sm text-stone-600">
          Нутрициолог доступен в Telegram Mini App.
        </p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-emerald-700">
          На главную
        </Link>
      </div>
    );
  }

  if (loading || modeLoading) {
    return (
      <div className="min-h-screen bg-stone-50">
        <PageLoading message="Загрузка…" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 pb-24">
      <header className="border-b border-stone-100 bg-white px-4 py-4">
        <div className="mx-auto max-w-lg">
          <h1 className="text-xl font-bold text-stone-900">Нутрициолог</h1>
          <p className="mt-0.5 text-sm text-stone-500">
            Рекомендации по питанию на основе ваших целей
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-3 px-4 py-4">
        <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm">
          {profileComplete && goalLabel ? (
            <>
              <p className="text-lg font-bold text-stone-900">{goalLabel}</p>
              {progress !== null ? (
                <p className="mt-1 text-sm font-medium text-emerald-800">
                  Прогресс: {progress}%
                </p>
              ) : null}
              <ModeLabel
                mode={mode}
                personsCount={personsCount}
                familyName={context?.family?.name ?? null}
              />
            </>
          ) : (
            <>
              <p className="text-base font-semibold text-stone-800">
                Заполните профиль питания
              </p>
              <p className="mt-1 text-sm text-stone-500">
                Цели, ограничения и режим — основа рекомендаций ПланАм
              </p>
            </>
          )}
          <Link
            href="/profile/nutrition"
            className="mt-3 inline-flex min-h-[40px] items-center justify-center rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white"
          >
            Открыть профиль питания
          </Link>
        </section>

        <section className="grid grid-cols-2 gap-2">
          {statCards.map((card) => (
            <article
              key={card.id}
              className={`rounded-2xl border p-3 shadow-sm ${
                card.ready
                  ? "border-stone-100 bg-white"
                  : "border-stone-100 bg-stone-50/80"
              }`}
            >
              <p className="text-xs font-medium text-stone-500">{card.label}</p>
              <p
                className={`mt-1 text-lg font-bold ${
                  card.ready ? "text-stone-900" : "text-stone-400"
                }`}
              >
                {card.value}
              </p>
              <p className="mt-0.5 text-[11px] leading-tight text-stone-500">
                {card.hint}
              </p>
            </article>
          ))}
        </section>

        <section className="rounded-2xl border border-amber-100 bg-amber-50/60 p-4 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wide text-amber-900">
            Совет ПланАм
          </p>
          <p className="mt-2 text-sm leading-relaxed text-stone-800">
            {dailyTip}
          </p>
        </section>

        <section>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">
            Быстрые действия
          </p>
          <div className="flex flex-wrap gap-2">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.id}
                type="button"
                onClick={() => handleQuickAction(action)}
                className="rounded-full border border-stone-200 bg-white px-3 py-2 text-sm font-medium text-stone-800 shadow-sm active:scale-[0.98]"
              >
                {action.label}
              </button>
            ))}
          </div>
        </section>

        {familySummary ? (
          <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
            <h2 className="text-sm font-bold text-stone-900">Семейная сводка</h2>
            <p className="mt-1 text-sm text-stone-600">
              {familySummary.memberCount} участников · профиль заполнен у{" "}
              {familySummary.profilesComplete}
            </p>
            {familySummary.goalLines.length > 0 ? (
              <ul className="mt-2 space-y-1 text-sm text-stone-700">
                {familySummary.goalLines.map((line) => (
                  <li key={line} className="truncate">
                    {line}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-stone-500">
                Цели участников появятся после заполнения профилей
              </p>
            )}
            <Link
              href="/family"
              className="mt-3 inline-block text-xs font-semibold text-emerald-700"
            >
              Управление семьёй
            </Link>
          </section>
        ) : null}

        <NutritionistChat
          mode={mode}
          profile={profile}
          menu={menu}
          amaAskCost={amaAskCost}
          amaBalance={amaBalance}
          initialPrompt={chatPrompt}
          onInitialPromptConsumed={() => setChatPrompt(null)}
          onBalanceChange={setAmaBalance}
        />

        <section className="rounded-2xl border border-stone-200 bg-stone-50/90 p-4">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-bold text-stone-900">PRO-рекомендации</p>
              <p className="mt-0.5 text-xs text-stone-500">Скоро в ПланАм PRO</p>
            </div>
            <span className="rounded-full bg-stone-200 px-2 py-0.5 text-[10px] font-bold uppercase text-stone-600">
              PRO
            </span>
          </div>
          <ul className="mt-3 space-y-1.5 text-sm text-stone-600">
            {PRO_FEATURES.map((feature) => (
              <li key={feature} className="flex items-center gap-2">
                <span className="text-stone-400" aria-hidden>
                  🔒
                </span>
                {feature}
              </li>
            ))}
          </ul>
          <Link
            href="/subscription"
            className="mt-3 flex min-h-[40px] items-center justify-center rounded-xl border border-stone-300 bg-white text-sm font-semibold text-stone-800"
          >
            Узнать о PRO
          </Link>
        </section>

        <CareTelegramBlock />
      </main>
    </div>
  );
}
