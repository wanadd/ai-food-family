"use client";

import Link from "next/link";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { buildFamilyMemberInsights } from "@/lib/nutritionist/family-insights";

/**
 * Блок «Сводка семьи» (family mode) — производная сводка из уже загруженного
 * контекста семьи (без backend и без новых запросов). Это НЕ лента активности:
 * показываем состав и короткие инсайты по членам. Если данных мало — мягкое
 * пустое состояние.
 */
export function HomeFamilySummary() {
  const { mode, context } = useAppMode();

  if (mode !== "family" || !context?.family) {
    return null;
  }

  const family = context.family;
  const membersCount = family.members_count ?? family.members.length;
  const insights = buildFamilyMemberInsights(family).slice(0, 4);

  return (
    <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
            Сводка семьи
          </p>
          <p className="mt-1.5 text-sm font-semibold text-stone-900">
            {family.name}
          </p>
          <p className="mt-0.5 text-xs text-stone-500">
            {membersCount}{" "}
            {membersCount === 1 ? "участник" : "участников"} · меню учитывает
            каждого
          </p>
        </div>
        <Link
          href="/profile"
          className="shrink-0 rounded-xl bg-stone-100 px-3 py-2 text-xs font-semibold text-stone-700 transition hover:bg-emerald-50 hover:text-emerald-800"
        >
          Открыть
        </Link>
      </div>

      {insights.length > 0 ? (
        <ul className="mt-3 space-y-1.5 border-t border-stone-100 pt-3 text-sm text-stone-700">
          {insights.map((row) => (
            <li key={row.name}>
              <span className="font-semibold text-stone-900">{row.name}:</span>{" "}
              {row.line}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 border-t border-stone-100 pt-3 text-sm text-stone-500">
          Добавьте членов семьи в профиле — и ПланАм будет учитывать их цели и
          ограничения в меню.
        </p>
      )}
    </section>
  );
}
