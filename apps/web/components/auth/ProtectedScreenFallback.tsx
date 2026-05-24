"use client";

import Link from "next/link";

import { PageLoading } from "@/components/ui/PageLoading";
import { useProtectedScreen } from "@/lib/use-protected-screen";

type ProtectedScreenFallbackProps = {
  loadingMessage?: string;
  telegramMessage?: string;
};

export function ProtectedScreenFallback({
  loadingMessage = "Загрузка…",
  telegramMessage = "Откройте приложение через Telegram.",
}: ProtectedScreenFallbackProps) {
  const { state, authError, retryAuth } = useProtectedScreen();

  if (state === "loading") {
    return <PageLoading message={loadingMessage} />;
  }

  if (state === "error") {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-700">
          {authError ?? "Не удалось загрузить данные. Попробуйте ещё раз."}
        </p>
        <button
          type="button"
          onClick={retryAuth}
          className="mt-4 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white"
        >
          Повторить
        </button>
      </div>
    );
  }

  if (state === "telegram_only") {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">{telegramMessage}</p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-emerald-700"
        >
          На главную
        </Link>
      </div>
    );
  }

  return null;
}
