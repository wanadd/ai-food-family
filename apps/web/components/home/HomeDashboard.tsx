"use client";

import Link from "next/link";

import { ModeSwitcher } from "@/components/app-mode/ModeSwitcher";
import { HealthStatus } from "@/components/HealthStatus";
import { OpenMiniAppButton } from "@/components/OpenMiniAppButton";
import { TelegramAuthPanel } from "@/components/TelegramAuthPanel";
import { apiUrl } from "@/lib/api";

export function HomeDashboard() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <section className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-600">
          Telegram Mini App
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">
          AI Food Family
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-600">
          Питание для себя или всей семьи: меню, покупки и остатки — сразу после
          входа через Telegram.
        </p>

        <div className="mt-6">
          <ModeSwitcher />
        </div>

        <div className="mt-6 space-y-3 border-t border-slate-200 pt-6">
          <Link
            href="/onboarding"
            className="inline-flex w-full items-center justify-center rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
          >
            Настройки питания
          </Link>
          <Link
            href="/menu"
            className="inline-flex w-full items-center justify-center rounded-xl border border-violet-300 bg-violet-50 px-5 py-3 text-sm font-semibold text-violet-800 transition hover:bg-violet-100"
          >
            AI Меню
          </Link>
          <Link
            href="/shopping"
            className="inline-flex w-full items-center justify-center rounded-xl border border-amber-300 bg-amber-50 px-5 py-3 text-sm font-semibold text-amber-900 transition hover:bg-amber-100"
          >
            Список покупок
          </Link>
          <Link
            href="/pantry"
            className="inline-flex w-full items-center justify-center rounded-xl border border-teal-300 bg-teal-50 px-5 py-3 text-sm font-semibold text-teal-900 transition hover:bg-teal-100"
          >
            Остатки
          </Link>
          <Link
            href="/recipes"
            className="inline-flex w-full items-center justify-center rounded-xl border border-rose-300 bg-rose-50 px-5 py-3 text-sm font-semibold text-rose-900 transition hover:bg-rose-100"
          >
            Рецепты
          </Link>
          <Link
            href="/notifications"
            className="inline-flex w-full items-center justify-center rounded-xl border border-sky-300 bg-sky-50 px-5 py-3 text-sm font-semibold text-sky-900 transition hover:bg-sky-100"
          >
            Уведомления
          </Link>
          <Link
            href="/family"
            className="inline-flex w-full items-center justify-center rounded-xl border border-violet-200 bg-violet-50/50 px-5 py-3 text-sm font-semibold text-violet-900 transition hover:bg-violet-100"
          >
            Семейный режим
          </Link>
          <OpenMiniAppButton />
          <TelegramAuthPanel />
        </div>

        <div className="mt-6 space-y-3 border-t border-slate-200 pt-6">
          <div>
            <span className="text-sm text-slate-500">Backend API</span>
            <code className="mt-1 block break-all text-sm text-slate-800">
              {apiUrl}
            </code>
          </div>
          <HealthStatus apiUrl={apiUrl} />
        </div>
      </section>
    </main>
  );
}
