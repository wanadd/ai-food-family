"use client";

import Link from "next/link";

// Примеры вопросов для AI-хаба. Пока ведут в чат нутрициолога (/health/chat);
// позже AI-чат переедет в центральный ПланАм-хаб.
const ASK_EXAMPLES = [
  "Что приготовить сегодня?",
  "Что докупить?",
  "Как сделать меню полезнее?",
];

const CHAT_HREF = "/health/chat";

/**
 * Блок «Спросить ПланАм» — компактный вход в AI-чат с примерами вопросов.
 * Без новых AI-запросов на Home: это только навигационный CTA.
 */
export function HomeAskPlanAm() {
  return (
    <section className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50/80 to-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-bold text-stone-900">Спросить ПланАм</p>
          <p className="mt-0.5 text-xs text-stone-600">
            AI-помощник по питанию, меню и покупкам
          </p>
        </div>
        <span
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-lg text-white shadow-sm"
          aria-hidden
        >
          ✨
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {ASK_EXAMPLES.map((example) => (
          <Link
            key={example}
            href={CHAT_HREF}
            className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200 transition hover:bg-emerald-50"
          >
            {example}
          </Link>
        ))}
      </div>

      <Link
        href={CHAT_HREF}
        className="mt-3 flex min-h-[44px] w-full items-center justify-center rounded-xl bg-stone-900 px-4 py-2.5 text-sm font-semibold text-white transition active:scale-[0.99]"
      >
        Открыть чат
      </Link>
    </section>
  );
}
