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
  { href: "/notifications", label: "Уведомления", desc: "Забота, готовка, тихие часы", emoji: "🔔" },
  { href: "/settings/about", label: "О приложении", desc: "Версия и поддержка", emoji: "ℹ️" },
] as const;

function SettingsGearLink() {
  return (
    <Link
      href="/settings"
      aria-label="Настройки"
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-pill border border-cream-border bg-cream-surface text-graphite-600 shadow-soft transition hover:border-sage-200 hover:text-sage-700"
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

function UserAvatar({
  name,
  photoUrl,
}: {
  name: string;
  photoUrl: string | null | undefined;
}) {
  const initial = name.trim().charAt(0).toUpperCase() || "П";
  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt=""
        className="h-14 w-14 shrink-0 rounded-card object-cover shadow-soft ring-2 ring-cream-surface"
      />
    );
  }
  return (
    <div
      className="flex h-14 w-14 shrink-0 items-center justify-center rounded-card bg-sage-500 text-xl font-bold text-white shadow-soft"
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
        <section className="pa-card p-5">
          <p className="text-sm text-graphite-500">
            {isAuthenticating
              ? "Подключаем Telegram…"
              : "Откройте приложение через Telegram Mini App"}
          </p>
        </section>
      ) : (
        <>
          <section className="pa-card p-5">
            <div className="flex items-center gap-4">
              <UserAvatar name={fullName} photoUrl={user?.photo_url} />
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-xl font-bold text-graphite-900">
                  {fullName}
                </h2>
                <p className="mt-1 text-sm text-graphite-500">Ваш аккаунт</p>
              </div>
            </div>
            {!modeLoading ? (
              <div className="mt-5">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-graphite-400">
                  Режим
                </p>
                <ProfileModeControl />
              </div>
            ) : null}
          </section>

          <Link
            href="/profile/nutrition"
            className="pa-card block p-4 transition active:scale-[0.99] hover:border-sage-200"
          >
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
                  Профиль питания
                </p>
                {loadingNutrition ? (
                  <p className="mt-2 text-sm text-graphite-500">Загрузка…</p>
                ) : sectionChecks ? (
                  <p className="mt-1.5 text-sm font-medium text-graphite-900">
                    Заполнено {sectionChecks.filled} из {sectionChecks.total}{" "}
                    · {progressPercent}%
                  </p>
                ) : (
                  <p className="mt-1.5 text-sm text-graphite-500">
                    Настройте цели и ограничения
                  </p>
                )}
              </div>
              <span className="text-graphite-400" aria-hidden>
                ›
              </span>
            </div>
            {sectionChecks && progressPercent < 100 ? (
              <div className="mt-3 h-2 overflow-hidden rounded-pill bg-sage-100">
                <div
                  className="h-full rounded-pill bg-sage-500 transition-all"
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
              className="pa-card flex min-h-[60px] items-center gap-3 px-4 py-3.5 transition hover:border-sage-200 active:scale-[0.99]"
            >
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-sage-50 text-lg"
                aria-hidden
              >
                {item.emoji}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-graphite-900">{item.label}</p>
                <p className="mt-0.5 truncate text-sm text-graphite-500">
                  {item.desc}
                </p>
              </div>
              <span className="shrink-0 text-graphite-400" aria-hidden>
                ›
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </ScreenLayout>
  );
}
