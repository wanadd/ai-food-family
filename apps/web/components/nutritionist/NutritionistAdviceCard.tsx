"use client";

import Link from "next/link";
import { useState } from "react";

import type { AppMode } from "@/lib/app-mode/types";
import { withReturnTo } from "@/lib/navigation/return-to";
import { deferAdvice } from "@/lib/nutritionist/advice-deferred";
import type { MainAdvice } from "@/lib/nutritionist/main-advice";

type Props = {
  advice: MainAdvice;
  initData: string;
  mode: AppMode;
  onDeferred?: () => void;
};

function extractFoodHint(body: string): string {
  const match = body.match(/(?:добавьте|добавить|съешьте)\s+([^—.]+)/i);
  if (match?.[1]) return match[1].trim().slice(0, 40);
  if (body.toLowerCase().includes("творог")) return "творог";
  if (body.toLowerCase().includes("белок")) return "белок перекус";
  return "перекус";
}

export function NutritionistAdviceCard({
  advice,
  initData,
  mode,
  onDeferred,
}: Props) {
  const [snoozed, setSnoozed] = useState(false);
  const [deferring, setDeferring] = useState(false);
  const hint = extractFoodHint(advice.body);
  const returnTo = "/health";

  if (snoozed) return null;

  return (
    <section className="pa-card border-warm/30 bg-warm/10 p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-warm">
        Совет ПланАм
      </p>
      <p className="mt-2 text-base font-semibold text-graphite-900">{advice.title}</p>
      <p className="mt-1.5 text-sm leading-relaxed text-graphite-700">{advice.body}</p>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <Link
          href={withReturnTo("/menu/generate", returnTo)}
          className="pa-btn-primary px-2 py-2.5 text-center text-xs"
        >
          Добавить в меню
        </Link>
        <Link
          href={`/menu/recipes?q=${encodeURIComponent(hint)}`}
          className="pa-btn px-2 py-2.5 text-center text-xs"
        >
          Найти рецепт
        </Link>
        <Link
          href={`/shopping?add=${encodeURIComponent(hint)}`}
          className="pa-btn px-2 py-2.5 text-center text-xs"
        >
          Добавить в покупки
        </Link>
        <button
          type="button"
          disabled={deferring}
          onClick={() => {
            setDeferring(true);
            void deferAdvice(initData, mode as import("@/lib/app-mode/types").AppMode, advice)
              .then(() => {
                setSnoozed(true);
                onDeferred?.();
              })
              .finally(() => setDeferring(false));
          }}
          className="pa-btn-ghost px-2 py-2.5 text-center text-xs disabled:opacity-50"
        >
          {deferring ? "…" : "Не сейчас"}
        </button>
      </div>
    </section>
  );
}
