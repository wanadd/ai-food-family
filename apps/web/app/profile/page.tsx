"use client";

import Link from "next/link";

import { ModeSwitcher } from "@/components/app-mode/ModeSwitcher";
import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { useTelegram } from "@/components/TelegramProvider";
import { HealthStatus } from "@/components/HealthStatus";
import { apiUrl } from "@/lib/api";

const MORE_LINKS = [
  { href: "/onboarding", label: "Настройки питания", desc: "Цели, диеты, ограничения" },
  { href: "/family", label: "Семья", desc: "Семейный режим и участники" },
  { href: "/recipes", label: "Рецепты", desc: "Каталог и избранное" },
  { href: "/notifications", label: "Уведомления", desc: "Напоминания о покупках и готовке" },
] as const;

export default function ProfilePage() {
  const { user, isTelegram, isAuthenticating } = useTelegram();
  const { mode, context } = useAppMode();

  const fullName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    "Пользователь";

  const modeLabel =
    mode === "family"
      ? `Семейный${context?.family?.name ? ` · ${context.family.name}` : ""}`
      : "Личный";

  return (
    <div className="min-h-screen bg-white">
      <header className="px-5 pb-2 pt-8">
        <h1 className="text-2xl font-bold text-stone-900">Профиль</h1>
        <p className="mt-1 text-sm text-stone-500">Аккаунт и настройки ПланАм</p>
      </header>

      <main className="mx-auto max-w-lg space-y-4 px-5 pb-4">
        <section className="rounded-2xl border border-stone-100 bg-white p-5 shadow-sm">
          {isTelegram && user ? (
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Имя
                </dt>
                <dd className="mt-0.5 font-semibold text-stone-900">{fullName}</dd>
              </div>
              {user.username ? (
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                    Username
                  </dt>
                  <dd className="mt-0.5 text-stone-700">@{user.username}</dd>
                </div>
              ) : null}
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Телефон
                </dt>
                <dd className="mt-0.5 text-stone-700">
                  {user.phone_number ?? "Не указан — подтвердите в боте /start"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Telegram ID
                </dt>
                <dd className="mt-0.5 font-mono text-stone-700">{user.telegram_id}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Режим
                </dt>
                <dd className="mt-0.5 font-medium text-emerald-800">{modeLabel}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-stone-500">
              {isAuthenticating
                ? "Подключаем Telegram…"
                : "Откройте приложение через Telegram Mini App"}
            </p>
          )}
        </section>

        <section className="rounded-2xl border border-stone-100 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
            Режим приложения
          </p>
          <div className="mt-3">
            <ModeSwitcher />
          </div>
        </section>

        <section className="space-y-2">
          <p className="px-1 text-xs font-semibold uppercase tracking-wide text-stone-400">
            Настройки
          </p>
          {MORE_LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-2xl border border-stone-100 bg-white p-4 shadow-sm transition hover:border-emerald-200"
            >
              <p className="font-semibold text-stone-900">{item.label}</p>
              <p className="mt-0.5 text-sm text-stone-500">{item.desc}</p>
            </Link>
          ))}
          <Link
            href="/pantry"
            className="block rounded-2xl border border-stone-100 bg-white p-4 shadow-sm transition hover:border-emerald-200"
          >
            <p className="font-semibold text-stone-900">Склад</p>
            <p className="mt-0.5 text-sm text-stone-500">Продукты дома для AI-меню</p>
          </Link>
        </section>

        {process.env.NODE_ENV === "development" ? (
          <section className="rounded-2xl border border-dashed border-stone-200 bg-stone-50 p-4 text-xs text-stone-500">
            <p className="font-semibold text-stone-600">Dev</p>
            <p className="mt-1 break-all">API: {apiUrl}</p>
            {user ? (
              <p className="mt-1">User ID в БД: {user.id}</p>
            ) : null}
            <HealthStatus apiUrl={apiUrl} />
          </section>
        ) : null}
      </main>

      <BottomBackButton className="pb-2 pt-2" />
    </div>
  );
}
