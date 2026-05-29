"use client";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import type { AppMode } from "@/lib/app-mode/types";

export function ModeSwitcher() {
  const { mode, context, loading, setMode } = useAppMode();

  if (loading) {
    return (
      <p className="text-sm text-graphite-500">Загрузка режима…</p>
    );
  }

  if (!context?.can_use_family_mode) {
    return (
      <div className="pa-card border-sage-200 bg-sage-50/50 px-4 py-3">
        <p className="text-xs font-bold uppercase tracking-wide text-sage-700">
          Личный режим
        </p>
        <p className="mt-1 text-sm text-graphite-700">
          Все данные сохраняются для вас. Семейный режим можно включить в разделе
          «Семья».
        </p>
      </div>
    );
  }

  return (
    <div className="pa-card p-1">
      <p className="px-3 pt-2 text-xs font-semibold uppercase tracking-wide text-graphite-500">
        Режим работы
      </p>
      <div className="mt-2 flex gap-1 p-1">
        {(["personal", "family"] as AppMode[]).map((option) => {
          const isActive = mode === option;
          return (
            <button
              key={option}
              type="button"
              onClick={() => setMode(option)}
              className={`flex-1 rounded-control py-2.5 text-sm font-semibold transition ${
                isActive
                  ? "bg-sage-500 text-white shadow-soft"
                  : "text-graphite-600 hover:bg-cream-deep"
              }`}
            >
              {option === "personal" ? "Личный" : "Семейный"}
            </button>
          );
        })}
      </div>
      {context.family ? (
        <p className="px-3 pb-2 text-xs text-graphite-500">
          Семья: {context.family.name}
        </p>
      ) : null}
    </div>
  );
}
