"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { HealthStatus } from "@/components/HealthStatus";
import { apiUrl } from "@/lib/api";
import { fetchSelectedMenu } from "@/lib/menu/api";
import type { SelectedMenu } from "@/lib/menu/types";
import { fetchRemoteOnboarding } from "@/lib/onboarding/api";
import { fetchShoppingList } from "@/lib/shopping/api";
import type { ShoppingList } from "@/lib/shopping/types";

function formatUpdatedToday(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return "Обновлён сегодня";
  }
  return `Обновлён ${date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" })}`;
}

export function PlanAmHome() {
  const { initData, isTelegram, user, isAuthenticating } = useTelegram();
  const { mode, loading: modeLoading } = useAppMode();

  const [loadingSelectedMenu, setLoadingSelectedMenu] = useState(true);
  const [onboardingCompleted, setOnboardingCompleted] = useState<boolean | null>(
    null,
  );
  const [selectedMenu, setSelectedMenu] = useState<SelectedMenu | null>(null);
  const [shopping, setShopping] = useState<ShoppingList | null>(null);

  const displayName =
    user?.first_name?.trim() ||
    user?.username?.trim() ||
    "друг";

  const loadHomeData = useCallback(async () => {
    if (!initData) {
      setLoadingSelectedMenu(false);
      setOnboardingCompleted(null);
      setSelectedMenu(null);
      setShopping(null);
      return;
    }

    setLoadingSelectedMenu(true);
    try {
      const [onboarding, selected, list] = await Promise.all([
        fetchRemoteOnboarding(initData),
        fetchSelectedMenu(initData, mode),
        fetchShoppingList(initData, mode).catch(() => null),
      ]);
      setOnboardingCompleted(onboarding?.completed ?? false);
      setSelectedMenu(selected);
      setShopping(list);
    } finally {
      setLoadingSelectedMenu(false);
    }
  }, [initData, mode]);

  useEffect(() => {
    if (modeLoading) {
      setLoadingSelectedMenu(true);
      return;
    }
    void loadHomeData();
  }, [loadHomeData, modeLoading]);

  const isCheckingMenu = loadingSelectedMenu || modeLoading;
  const mainHref = onboardingCompleted ? "/menu" : "/onboarding";
  const mainLabel = onboardingCompleted
    ? "Сгенерировать меню"
    : "Настроить питание";
  const mainHint = onboardingCompleted
    ? "Это займёт около 30 секунд"
    : "Несколько вопросов о целях и предпочтениях";

  return (
    <div className="min-h-screen bg-[#fafaf9]">
      <main className="mx-auto max-w-lg space-y-5 px-5 pb-8 pt-8">
        <header>
          <p className="text-sm font-medium text-emerald-700">ПланАм</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-stone-900">
            Привет, {displayName}!
          </h1>
          <p className="mt-2 text-base leading-relaxed text-stone-600">
            Соберём меню и список покупок под ваши цели
          </p>
        </header>

        <section className="rounded-[24px] border border-emerald-100 bg-white p-6 shadow-sm">
          <Link
            href={mainHref}
            className="flex w-full items-center justify-center rounded-[20px] bg-gradient-to-r from-emerald-500 to-teal-600 py-4 text-base font-semibold text-white shadow-md transition hover:opacity-95"
          >
            {mainLabel}
          </Link>
          <p className="mt-3 text-center text-sm text-stone-500">{mainHint}</p>
        </section>

        <section className="rounded-[24px] border border-stone-200 bg-white p-5 shadow-sm">
          {isCheckingMenu ? (
            <div className="animate-pulse space-y-3" aria-busy="true">
              <p className="text-sm font-medium text-stone-600">
                Проверяем выбранное меню…
              </p>
              <div className="h-16 rounded-2xl bg-stone-100" />
            </div>
          ) : selectedMenu ? (
            <Link href="/menu" className="block">
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                Ваше меню
              </p>
              <h2 className="mt-2 text-xl font-bold text-stone-900">
                {selectedMenu.menu.title}
              </h2>
              <p className="mt-1 text-sm text-stone-500">Меню на день</p>
              <span className="mt-3 inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                Выбрано
              </span>
            </Link>
          ) : (
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-stone-400">
                Ваше меню
              </p>
              <h2 className="mt-2 text-lg font-semibold text-stone-800">
                Меню ещё не создано
              </h2>
              <Link
                href="/menu"
                className="mt-4 inline-flex text-sm font-semibold text-emerald-700"
              >
                Создать меню →
              </Link>
            </div>
          )}
        </section>

        <section className="rounded-[24px] border border-stone-200 bg-white p-5 shadow-sm">
          <Link href="/shopping" className="block">
            <p className="text-xs font-bold uppercase tracking-wide text-amber-800">
              Список покупок
            </p>
            {shopping && shopping.total_count > 0 ? (
              <>
                <p className="mt-2 text-2xl font-bold text-stone-900">
                  {shopping.total_count}{" "}
                  {shopping.total_count === 1
                    ? "товар"
                    : shopping.total_count < 5
                      ? "товара"
                      : "товаров"}
                </p>
                <p className="mt-1 text-sm text-stone-500">
                  {formatUpdatedToday(shopping.updated_at)}
                </p>
              </>
            ) : (
              <p className="mt-2 text-sm text-stone-500">Пока пусто</p>
            )}
          </Link>
        </section>

        <section className="rounded-[24px] border border-stone-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wide text-stone-500">
            Авторизация
          </p>
          {isTelegram && user ? (
            <div className="mt-3 space-y-1 text-sm text-stone-700">
              <p>Вход выполнен через Telegram</p>
              <p className="font-semibold text-stone-900">
                {[user.first_name, user.last_name].filter(Boolean).join(" ") ||
                  "Пользователь"}
              </p>
              {user.username ? (
                <p className="text-stone-500">@{user.username}</p>
              ) : null}
              <p className="text-stone-600">
                {user.phone_number ?? "Номер не указан"}
              </p>
              {!user.phone_number ? (
                <p className="text-xs text-stone-400">
                  Поделитесь номером в боте командой /start
                </p>
              ) : null}
            </div>
          ) : (
            <p className="mt-3 text-sm text-stone-500">
              {isAuthenticating
                ? "Подключаем Telegram…"
                : "Откройте приложение через Telegram"}
            </p>
          )}
        </section>

        {process.env.NODE_ENV === "development" ? (
          <section className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 p-4 text-xs text-stone-500">
            <p className="font-semibold text-stone-600">Dev</p>
            <p className="mt-1 break-all">API: {apiUrl}</p>
            <HealthStatus apiUrl={apiUrl} />
          </section>
        ) : null}
      </main>
    </div>
  );
}
