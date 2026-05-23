"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { ProfileModeControl } from "@/components/profile/ProfileModeControl";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useTelegram } from "@/components/TelegramProvider";
import {
  getNutritionProfileProgress,
  getNutritionSectionChecks,
} from "@/lib/profile/nutrition-summary";
import { fetchNutritionProfile } from "@/lib/nutrition-profile/api";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";

const PROFILE_MENU = [
  { href: "/profile/nutrition", label: "Питание", desc: "Цели и ограничения", emoji: "🥗" },
  { href: "/family", label: "Семья", desc: "Участники и меню", emoji: "👨‍👩‍👧" },
  { href: "/subscription", label: "Подписка", desc: "Тариф и Амы", emoji: "✨" },
  { href: "/progress", label: "Прогресс", desc: "Вес и цели", emoji: "📈" },
  { href: "/notifications", label: "Уведомления", desc: "Покупки и готовка", emoji: "🔔" },
  { href: "/settings/about", label: "О приложении", desc: "Версия и поддержка", emoji: "ℹ️" },
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
  const { loading: modeLoading } = useAppMode();
  const [nutrition, setNutrition] = useState<NutritionProfileData | null>(null);
  const [loadingNutrition, setLoadingNutrition] = useState(true);

  const loadNutrition = useCallback(async () => {
    if (!initData) {
      setNutrition(null);
      setLoadingNutrition(false);
      return;
    }
    setLoadingNutrition(true);
    try {
      setNutrition(await fetchNutritionProfile(initData));
    } catch {
      setNutrition(null);
    } finally {
      setLoadingNutrition(false);
    }
  }, [initData]);

  useEffect(() => {
    void loadNutrition();
  }, [loadNutrition]);

  const fullName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    "Пользователь";

  const progressPercent = getNutritionProfileProgress(nutrition);
  const sectionChecks = nutrition
    ? getNutritionSectionChecks(nutrition)
    : null;

  return (
    <ScreenLayout
      title="Профиль"
      subtitle="Настройки и данные ПланАм"
      headerExtra={<SettingsGearLink />}
    >
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
                <p className="mt-1 text-sm text-stone-500">Ваш аккаунт</p>
              </div>
            </div>
            {!modeLoading ? (
              <div className="mt-5">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Режим
                </p>
                <ProfileModeControl />
              </div>
            ) : null}
          </section>

          <Link
            href="/profile/nutrition"
            className="block rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50/90 to-white p-4 shadow-sm transition active:scale-[0.99] hover:border-emerald-200"
          >
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                  Профиль питания
                </p>
                {loadingNutrition ? (
                  <p className="mt-2 text-sm text-stone-500">Загрузка…</p>
                ) : sectionChecks ? (
                  <p className="mt-1.5 text-sm font-medium text-stone-800">
                    Заполнено {sectionChecks.filled} из {sectionChecks.total}{" "}
                    · {progressPercent}%
                  </p>
                ) : (
                  <p className="mt-1.5 text-sm text-stone-600">
                    Настройте цели и ограничения
                  </p>
                )}
              </div>
              <span className="text-stone-400" aria-hidden>
                ›
              </span>
            </div>
            {sectionChecks && progressPercent < 100 ? (
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-emerald-100">
                <div
                  className="h-full rounded-full bg-emerald-600 transition-all"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            ) : null}
          </Link>
        </>
      )}

      <ul className="mt-4 space-y-2">
        {PROFILE_MENU.map((item) => (
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
    </ScreenLayout>
  );
}
