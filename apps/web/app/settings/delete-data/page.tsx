"use client";

import { useState } from "react";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";
import { useTelegram } from "@/components/TelegramProvider";
import { requestDataDeletion } from "@/lib/legal/api";

export default function DeleteDataPage() {
  const { initData } = useTelegram();
  const [confirmed, setConfirmed] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!initData || !confirmed) return;
    setLoading(true);
    try {
      const res = await requestDataDeletion(initData);
      setMessage(res.message);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SettingsScaffold title="Удалить мои данные">
      <p className="text-sm leading-relaxed text-stone-600">
        Запрос на удаление персональных данных. Полное удаление будет доступно в
        следующем обновлении; сейчас фиксируем обращение.
      </p>
      <label className="mt-4 flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
          className="mt-1"
        />
        <span>Я понимаю, что это действие необратимо после обработки запроса</span>
      </label>
      {message ? (
        <p className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {message}
        </p>
      ) : null}
      <button
        type="button"
        disabled={!confirmed || loading}
        onClick={() => void submit()}
        className="mt-6 w-full rounded-xl bg-red-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
      >
        {loading ? "Отправка…" : "Отправить запрос"}
      </button>
    </SettingsScaffold>
  );
}
