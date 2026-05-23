"use client";

import { useCallback, useEffect, useState } from "react";

import { PhoneRequiredScreen } from "@/components/auth/PhoneRequiredScreen";
import { useTelegram } from "@/components/TelegramProvider";
import {
  acceptLegal,
  fetchLegalDocuments,
  type LegalDocument,
} from "@/lib/legal/api";

export function LegalConsentScreen() {
  const { initData, retryAuth } = useTelegram();
  const [docs, setDocs] = useState<LegalDocument[]>([]);
  const [terms, setTerms] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  const [personal, setPersonal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    void fetchLegalDocuments()
      .then((r) => setDocs(r.documents))
      .catch(() => setError("Не удалось загрузить документы"));
  }, []);

  const allChecked = terms && privacy && personal;

  const submit = useCallback(async () => {
    if (!initData || !allChecked) return;
    setLoading(true);
    setError(null);
    try {
      await acceptLegal(initData, {
        accepted_terms: true,
        accepted_privacy: true,
        accepted_personal_data: true,
      });
      setDone(true);
      retryAuth();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка сохранения");
    } finally {
      setLoading(false);
    }
  }, [initData, allChecked, retryAuth]);

  if (done) {
    return <PhoneRequiredScreen />;
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col bg-stone-50 px-4 py-8">
      <h1 className="text-2xl font-bold text-stone-900">Добро пожаловать в ПланАм</h1>
      <p className="mt-3 text-sm leading-relaxed text-stone-600">
        Ваш AI-помощник по меню, покупкам, запасам, семейному питанию и спортивным
        целям. Перед началом ознакомьтесь с документами.
      </p>

      <ul className="mt-6 space-y-4">
        {docs.map((doc) => (
          <li key={doc.id} className="rounded-2xl border border-stone-100 bg-white p-4">
            <a
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-emerald-700"
            >
              {doc.title} →
            </a>
            <p className="mt-2 text-xs leading-relaxed text-stone-500">{doc.stub_text}</p>
          </li>
        ))}
      </ul>

      <div className="mt-6 space-y-3">
        <label className="flex cursor-pointer items-start gap-3 text-sm">
          <input
            type="checkbox"
            checked={terms}
            onChange={(e) => setTerms(e.target.checked)}
            className="mt-1"
          />
          <span>Я ознакомился и согласен с пользовательским соглашением</span>
        </label>
        <label className="flex cursor-pointer items-start gap-3 text-sm">
          <input
            type="checkbox"
            checked={privacy}
            onChange={(e) => setPrivacy(e.target.checked)}
            className="mt-1"
          />
          <span>Я ознакомился и согласен с политикой конфиденциальности</span>
        </label>
        <label className="flex cursor-pointer items-start gap-3 text-sm">
          <input
            type="checkbox"
            checked={personal}
            onChange={(e) => setPersonal(e.target.checked)}
            className="mt-1"
          />
          <span>Я даю согласие на обработку персональных данных</span>
        </label>
      </div>

      {error ? (
        <p className="mt-4 text-sm text-red-700">{error}</p>
      ) : null}

      <button
        type="button"
        disabled={!allChecked || loading}
        onClick={() => void submit()}
        className="mt-8 w-full rounded-2xl bg-emerald-600 py-3.5 text-base font-semibold text-white disabled:opacity-40"
      >
        {loading ? "Сохранение…" : "Продолжить"}
      </button>
    </div>
  );
}
