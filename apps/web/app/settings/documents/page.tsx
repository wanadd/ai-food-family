"use client";

import { useEffect, useMemo, useState } from "react";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";
import { fetchLegalDocuments, type LegalDocument } from "@/lib/legal/api";

type DocumentCard = {
  id: string;
  title: string;
  description: string;
};

const DOCUMENT_CARDS: DocumentCard[] = [
  {
    id: "terms",
    title: "Пользовательское соглашение",
    description: "Правила использования PLANAM в закрытом тестировании.",
  },
  {
    id: "privacy",
    title: "Политика конфиденциальности",
    description: "Как приложение работает с данными профиля и Telegram.",
  },
  {
    id: "personal-data",
    title: "Согласие на обработку данных",
    description: "Согласие на обработку данных для меню, покупок и семьи.",
  },
  {
    id: "subscription",
    title: "Правила подписки",
    description: "Условия будущих тарифов Premium и Pro.",
  },
];

function normalize(value: string): string {
  return value.toLowerCase().replace(/ё/g, "е");
}

function findRemoteDocument(card: DocumentCard, docs: LegalDocument[]) {
  const haystack = normalize(`${card.id} ${card.title}`);
  return docs.find((doc) => {
    const text = normalize(`${doc.id} ${doc.title}`);
    return haystack.includes(text) || text.includes(card.id) || text.includes(normalize(card.title));
  });
}

export default function DocumentsSettingsPage() {
  const [docs, setDocs] = useState<LegalDocument[]>([]);

  useEffect(() => {
    let cancelled = false;
    void fetchLegalDocuments()
      .then((r) => {
        if (!cancelled) setDocs(r.documents);
      })
      .catch(() => {
        if (!cancelled) setDocs([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const cards = useMemo(
    () =>
      DOCUMENT_CARDS.map((card) => ({
        ...card,
        remote: findRemoteDocument(card, docs),
      })),
    [docs],
  );

  return (
    <SettingsScaffold
      title="Документы"
      subtitle="Юридическая информация для закрытого тестирования"
    >
      <section className="rounded-card border border-sage-100 bg-sage-50/60 p-4 dark:border-sage-700/40 dark:bg-sage-900/20">
        <p className="text-sm font-semibold text-pa-foreground">
          Сейчас PLANAM находится в закрытом тестировании.
        </p>
        <p className="mt-1 text-sm leading-relaxed text-pa-muted">
          Финальные документы появятся перед публичным запуском. Если документ
          уже опубликован, его можно открыть из карточки ниже.
        </p>
      </section>

      <section className="space-y-2">
        {cards.map((doc) => (
          <article
            key={doc.id}
            className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h2 className="text-sm font-bold text-pa-foreground">{doc.title}</h2>
                <p className="mt-1 text-sm leading-relaxed text-pa-muted">
                  {doc.description}
                </p>
              </div>
              <span className="shrink-0 rounded-pill bg-cream-deep px-2.5 py-1 text-[11px] font-semibold text-pa-muted dark:bg-pa-elevated">
                {doc.remote?.url ? "Готово" : "Скоро"}
              </span>
            </div>
            {doc.remote?.url ? (
              <a
                href={doc.remote.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-flex min-h-[40px] items-center rounded-control bg-sage-600 px-4 py-2 text-sm font-semibold text-white active:scale-[0.99]"
              >
                Открыть документ
              </a>
            ) : (
              <p className="mt-3 text-xs text-pa-muted">Скоро будет доступно.</p>
            )}
          </article>
        ))}
      </section>
    </SettingsScaffold>
  );
}
