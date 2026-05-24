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
  const returnTo = "/nutritionist";

  if (snoozed) return null;

  return (
    <section className="rounded-2xl border border-amber-100 bg-amber-50/70 p-4 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wide text-amber-900">
        Совет ПланАм
      </p>
      <p className="mt-2 text-base font-semibold text-stone-900">{advice.title}</p>
      <p className="mt-1.5 text-sm leading-relaxed text-stone-700">{advice.body}</p>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <Link
          href={withReturnTo("/menu/generate", returnTo)}
          className="rounded-xl bg-emerald-600 px-2 py-2.5 text-center text-xs font-semibold text-white"
        >
          Добавить в меню
        </Link>
        <Link
          href={`/recipes?search=${encodeURIComponent(hint)}`}
          className="rounded-xl border border-stone-200 bg-white px-2 py-2.5 text-center text-xs font-semibold text-stone-800"
        >
          Найти рецепт
        </Link>
        <Link
          href={`/shopping?add=${encodeURIComponent(hint)}`}
          className="rounded-xl border border-stone-200 bg-white px-2 py-2.5 text-center text-xs font-semibold text-stone-800"
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
          className="rounded-xl border border-transparent px-2 py-2.5 text-center text-xs font-semibold text-stone-500 disabled:opacity-50"
        >
          {deferring ? "…" : "Не сейчас"}
        </button>
      </div>
    </section>
  );
}
