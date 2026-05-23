"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { CareTelegramLinkCard } from "@/components/care/CareTelegramLinkCard";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
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
import { buildFamilyMemberInsights } from "@/lib/nutritionist/family-insights";
import { pickMainAdvice } from "@/lib/nutritionist/main-advice";
import { buildTodayStatus } from "@/lib/nutritionist/today-status";
import { fetchProgressOverview } from "@/lib/progress/api";
import type { ProgressOverview } from "@/lib/progress/types";
import { fetchSubscriptionOverview } from "@/lib/subscription/api";

const QUICK_ACTIONS = [
  { href: "/nutritionist/chat", label: "Спросить нутрициолога", emoji: "💬" },
  { href: "/progress?focus=weight", label: "Добавить вес", emoji: "⚖️" },
  { href: "/progress?focus=training", label: "Добавить тренировку", emoji: "🏃" },
  { href: "/profile/nutrition", label: "Изменить цель", emoji: "🎯" },
] as const;

export function NutritionistDashboard() {
  const { initData, isTelegram } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<NutritionProfileData | null>(null);
  const [menu, setMenu] = useState<MenuVariant | null>(null);
  const [pantry, setPantry] = useState<PantryList | null>(null);
  const [progress, setProgress] = useState<ProgressOverview | null>(null);
  const [familySummaryOpen, setFamilySummaryOpen] = useState(false);
  const [familyProgressOpen, setFamilyProgressOpen] = useState(false);

  const load = useCallback(async () => {
    if (!initData) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [nutrition, selected, pantryList, progressData] = await Promise.all([
        fetchNutritionProfile(initData).catch(() => null),
        fetchSelectedMenu(initData, mode).catch(() => null),
        fetchPantry(initData, mode).catch(() => null),
        fetchProgressOverview(initData, mode).catch(() => null),
      ]);
      setProfile(nutrition);
      setMenu(selected?.menu ?? null);
      setPantry(pantryList);
      setProgress(progressData);
      void fetchSubscriptionOverview(initData, mode);
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

  const today = buildTodayStatus({
    goalLabel,
    progress,
    familyName: context?.family?.name ?? null,
    memberCount: personsCount,
    mode,
  });

  const advice = pickMainAdvice({
    profile,
    menu,
    pantry,
    pantryActiveCount: pantry?.active_count ?? 0,
  });

  const familyInsights = useMemo(() => {
    if (mode !== "family" || !context?.family) return [];
    return buildFamilyMemberInsights(context.family);
  }, [mode, context?.family]);

  const familyProgress = progress?.family_progress ?? [];

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
    <ScreenLayout
      title="Нутрициолог"
      subtitle="Семейный AI-помощник по питанию"
      contentClassName="space-y-3"
    >
      <section className="rounded-3xl border border-emerald-100 bg-gradient-to-br from-emerald-600 to-emerald-800 p-5 text-white shadow-lg shadow-emerald-200/50">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-100">
          Сегодня
        </p>
        {profileComplete ? (
          <>
            <h2 className="mt-2 text-2xl font-bold leading-tight">
              {today.goalLabel}
            </h2>
            {today.goalToTarget ? (
              <p className="mt-3 text-sm text-emerald-50">
                До цели:{" "}
                <span className="text-lg font-bold text-white">
                  {today.goalToTarget}
                </span>
              </p>
            ) : null}
            {today.progressPercent != null ? (
              <div className="mt-4">
                <div className="mb-1 flex justify-between text-xs text-emerald-100">
                  <span>Прогресс</span>
                  <span className="font-bold">{today.progressPercent}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-emerald-900/40">
                  <div
                    className="h-full rounded-full bg-white transition-all"
                    style={{ width: `${today.progressPercent}%` }}
                  />
                </div>
              </div>
            ) : null}
            <p className="mt-4 text-sm leading-relaxed text-emerald-50">
              {today.statusLine}
            </p>
            {today.familyLine ? (
              <p className="mt-2 text-sm font-medium text-white">
                {today.familyLine}
              </p>
            ) : null}
          </>
        ) : (
          <>
            <p className="mt-2 text-lg font-semibold">Заполните профиль питания</p>
            <p className="mt-2 text-sm text-emerald-50">
              Это основа персональных советов ПланАм
            </p>
            <Link
              href="/profile/nutrition"
              className="mt-4 inline-flex min-h-[44px] items-center rounded-xl bg-white px-4 text-sm font-semibold text-emerald-800"
            >
              Открыть профиль
            </Link>
          </>
        )}
      </section>

      <section className="rounded-2xl border border-amber-100 bg-amber-50/70 p-4 shadow-sm">
        <p className="text-xs font-bold uppercase tracking-wide text-amber-900">
          Совет ПланАм
        </p>
        <p className="mt-2 text-base font-semibold text-stone-900">{advice.title}</p>
        <p className="mt-1.5 text-sm leading-relaxed text-stone-700">
          {advice.body}
        </p>
      </section>

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
