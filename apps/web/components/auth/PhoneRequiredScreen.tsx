"use client";

import { useState } from "react";

import { useTelegram } from "@/components/TelegramProvider";
import { skipPhone } from "@/lib/legal/api";

export function PhoneRequiredScreen() {
  const { initData, retryAuth } = useTelegram();
  const [loading, setLoading] = useState(false);

  async function handleSkip() {
    if (!initData) return;
    setLoading(true);
    try {
      await skipPhone(initData);
      retryAuth();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#fafaf9] p-6">
      <section className="w-full max-w-md rounded-[24px] border border-emerald-100 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-semibold text-emerald-700">ПланАм</p>
        <h1 className="mt-3 text-2xl font-bold text-stone-900">Номер телефона</h1>
        <p className="mt-4 text-sm leading-relaxed text-stone-600">
          Поделитесь номером в боте — так проще восстановить доступ и получать
          уведомления.
        </p>
        <ol className="mt-6 space-y-3 text-left text-sm text-stone-700">
          <li>1. Откройте чат с ботом ПланАм</li>
          <li>2. Отправьте /start</li>
          <li>3. Нажмите «📱 Поделиться номером»</li>
          <li>4. Вернитесь в Mini App</li>
        </ol>
        <button
          type="button"
          disabled={loading || !initData}
          onClick={() => void handleSkip()}
          className="mt-6 w-full rounded-xl border border-stone-200 py-3 text-sm font-semibold text-stone-700"
        >
          {loading ? "…" : "Пропустить"}
        </button>
        <p className="mt-2 text-xs text-amber-800">
          Некоторые функции могут быть недоступны без номера.
        </p>
      </section>
    </div>
  );
}
