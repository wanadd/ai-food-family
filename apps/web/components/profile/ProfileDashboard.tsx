"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ProfileModeControl } from "@/components/profile/ProfileModeControl";
import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { useTelegram } from "@/components/TelegramProvider";
import { formatAmasBalance, billingFromSubscription } from "@/lib/profile/billing";
import { fetchSubscriptionOverview } from "@/lib/subscription/api";
import {
  getNutritionGoalLabel,
  getNutritionProfileProgress,
  isNutritionProfileComplete,
} from "@/lib/profile/nutrition-summary";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";

const QUICK_LINKS = [
  {
    href: "/profile/nutrition",
    label: "Мой профиль питания",
    desc: "Цели, диеты, ограничения",
    emoji: "🥗",
  },
  {
    href: "/family",
    label: "Семья и участники",
    desc: "Семейный режим и состав",
    emoji: "👨‍👩‍👧",
  },
  {
    href: "/subscription",
    label: "Тариф и Амы",
    desc: "Подписка и баланс AI-действий",
    emoji: "✨",
  },
  {
    href: "/notifications",
    label: "Уведомления",
    desc: "Покупки, готовка, напоминания",
    emoji: "🔔",
  },
  {
    href: "/settings",
    label: "Настройки",
    desc: "Аккаунт, язык, конфиденциальность",
    emoji: "⚙️",
  },
] as const;

function SettingsGearLink() {
  return (
    <Link
      href="/settings"
      aria-label="Настройки"
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-stone-200 bg-white text-stone-600 shadow-sm transition hover:border-emerald-200 hover:text-emerald-700"
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
        <path
          d="M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7z"
          stroke="currentColor"
          strokeWidth="1.75"
        />
        <path
          d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9c.26.604.852.997 1.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </Link>
  );
}

function UserAvatar({ name }: { name: string }) {
  const initial = name.trim().charAt(0).toUpperCase() || "П";
  return (
    <div
      className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-700 text-xl font-bold text-white shadow-md shadow-emerald-200/50"
      aria-hidden
    >
      {initial}
    </div>
  );
}

export function ProfileDashboard() {
  const { initData, user, isTelegram, isAuthenticating } = useTelegram();
  const { mode, context, loading: modeLoading } = useAppMode();
  const [billing, setBilling] = useState(() => billingFromSubscription(null));
  const [nutrition, setNutrition] = useState<NutritionProfileData | null>(null);
  const [loadingNutrition, setLoadingNutrition] = useState(true);

  const loadNutrition = useCallback(async () => {
    if (!initData) {
      setNutrition(null);
      setBilling(billingFromSubscription(null));
      setLoadingNutrition(false);
      return;
    }
    setLoadingNutrition(true);
    try {
      const [data, sub] = await Promise.all([
        fetchNutritionProfile(initData),
        fetchSubscriptionOverview(initData, mode),
      ]);
      setNutrition(data);
      setBilling(billingFromSubscription(sub));
    } catch {
      setNutrition(null);
    } finally {
      setLoadingNutrition(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    void loadNutrition();
  }, [loadNutrition]);

  const fullName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    "Пользователь";

  const progress = getNutritionProfileProgress(nutrition);
  const primaryGoal = getNutritionGoalLabel(nutrition);
  const profileComplete = isNutritionProfileComplete(nutrition);
  const showProgress = !profileComplete && progress < 100;
  const family = context?.family;
  const memberCount = family?.members?.length ?? 0;

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="bg-white px-4 pb-2 pt-7 sm:px-5">
        <div className="mx-auto flex max-w-lg items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-stone-900">Профиль</h1>
            <p className="mt-0.5 text-sm text-stone-500">Ваш ПланАм</p>
          </div>
          <SettingsGearLink />
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-4 px-4 pb-4 pt-4 sm:px-5">
        {!isTelegram || !user ? (
          <section className="rounded-3xl border border-stone-100 bg-white p-5 shadow-sm">
            <p className="text-sm text-stone-600">
              {isAuthenticating
                ? "Подключаем Telegram…"
                : "Откройте приложение через Telegram Mini App"}
            </p>
          </section>
        ) : (
          <>
            <section className="rounded-3xl border border-stone-100 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-4">
                <UserAvatar name={fullName} />
                <div className="min-w-0 flex-1">
                  <h2 className="truncate text-xl font-bold text-stone-900">
                    {fullName}
                  </h2>
                  <p className="mt-1 text-sm text-stone-500">ПланАм</p>
                </div>
              </div>

              <div className="mt-5">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Режим
                </p>
                <ProfileModeControl />
              </div>
            </section>

            <Link
              href="/subscription"
              className="block rounded-2xl border border-amber-100 bg-gradient-to-br from-amber-50/80 to-white p-4 shadow-sm transition hover:border-amber-200 active:scale-[0.99]"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">
                    Тариф и Амы
                  </p>
                  <p className="mt-1 text-lg font-bold text-stone-900">
                    {billing.planLabel}
                  </p>
                  <p className="mt-0.5 text-sm text-amber-900/80">
                    {formatAmasBalance(billing.amasBalance)}
                    {billing.menuRemaining != null
                      ? ` · меню: ${billing.menuRemaining}`
                      : null}
                  </p>
                </div>
                <span className="text-stone-400" aria-hidden>
                  →
                </span>
              </div>
            </Link>

            <section className="rounded-3xl border border-emerald-100 bg-gradient-to-b from-emerald-50/90 to-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                    Цель питания
                  </p>
                  {loadingNutrition ? (
                    <p className="mt-2 text-sm text-stone-500">Загрузка…</p>
                  ) : primaryGoal ? (
                    <p className="mt-1.5 text-lg font-bold text-stone-900">
                      {primaryGoal}
                    </p>
                  ) : (
                    <p className="mt-1.5 text-base font-medium text-stone-700">
                      Не задана
                    </p>
                  )}
                </div>
                <Link
                  href="/profile/nutrition"
                  className="shrink-0 rounded-xl bg-white px-3 py-2 text-sm font-semibold text-emerald-700 shadow-sm ring-1 ring-emerald-100"
                >
                  Изменить
                </Link>
              </div>

              {showProgress ? (
                <div className="mt-4">
                  <div className="mb-1.5 flex justify-between text-xs text-stone-600">
                    <span>Настройка профиля питания</span>
                    <span className="font-semibold">{progress}%</span>
                  </div>
                  <div
                    className="h-2 overflow-hidden rounded-full bg-emerald-100"
                    role="progressbar"
                    aria-valuenow={progress}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div
                      className="h-full rounded-full bg-emerald-600 transition-all"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <Link
                    href="/profile/nutrition"
                    className="mt-3 inline-block text-sm font-semibold text-emerald-700"
                  >
                    Продолжить настройку →
                  </Link>
                </div>
              ) : profileComplete ? (
                <p className="mt-3 text-sm text-emerald-800">
                  Профиль питания настроен — меню учитывает ваши цели
                </p>
              ) : (
                <Link
                  href="/profile/nutrition"
                  className="mt-3 inline-block text-sm font-semibold text-emerald-700"
                >
                  Настроить профиль питания →
                </Link>
              )}
            </section>

            {family ? (
              <Link
                href="/family"
                className="block rounded-3xl border border-violet-100 bg-gradient-to-r from-violet-50/80 to-white p-5 shadow-sm transition hover:border-violet-200 active:scale-[0.99]"
              >
                <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">
                  Семья
                </p>
                <p className="mt-1 truncate text-lg font-bold text-stone-900">
                  {family.name}
                </p>
                <p className="mt-1 text-sm text-stone-600">
                  {memberCount}{" "}
                  {memberCount === 1
                    ? "участник"
                    : memberCount >= 2 && memberCount <= 4
                      ? "участника"
                      : "участников"}
                </p>
              </Link>
            ) : !modeLoading && context?.has_family === false ? (
              <Link
                href="/family"
                className="block rounded-3xl border border-dashed border-stone-200 bg-white p-5 text-center shadow-sm transition hover:border-emerald-200 active:scale-[0.99]"
              >
                <p className="font-semibold text-stone-800">
                  Добавить семью или участников
                </p>
                <p className="mt-1 text-sm text-stone-500">
                  Необязательно — можно пользоваться одному
                </p>
              </Link>
            ) : null}
          </>
        )}

        <section>
          <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-stone-400">
            Разделы
          </p>
          <ul className="space-y-2">
            {QUICK_LINKS.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="flex min-h-[60px] items-center gap-3 rounded-2xl border border-stone-100 bg-white px-4 py-3.5 shadow-sm transition hover:border-emerald-200 active:scale-[0.99]"
                >
                  <span
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-stone-50 text-lg"
                    aria-hidden
                  >
                    {item.emoji}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-stone-900">{item.label}</p>
                    <p className="mt-0.5 truncate text-sm text-stone-500">
                      {item.desc}
                    </p>
                  </div>
                  <span className="shrink-0 text-stone-400" aria-hidden>
                    ›
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </main>

      <BottomBackButton className="pb-2 pt-2" />
    </div>
  );
}
