"use client";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import type { AppMode } from "@/lib/app-mode/types";

export function ModeSwitcher() {
  const { mode, context, loading, setMode } = useAppMode();

  if (loading) {
    return (
      <p className="text-sm text-stone-500">Загрузка режима…</p>
    );
  }

  if (!context?.can_use_family_mode) {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">
          Личный режим
        </p>
        <p className="mt-1 text-sm text-emerald-950">
          Все данные сохраняются для вас. Семейный режим можно включить в разделе
          «Семья».
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-1 shadow-sm">
      <p className="px-3 pt-2 text-xs font-semibold uppercase tracking-wide text-stone-500">
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
              className={`flex-1 rounded-lg py-2.5 text-sm font-semibold transition ${
                isActive
                  ? option === "family"
                    ? "bg-violet-600 text-white"
                    : "bg-emerald-600 text-white"
                  : "text-stone-600 hover:bg-stone-50"
              }`}
            >
              {option === "personal" ? "Личный" : "Семейный"}
            </button>
          );
        })}
      </div>
      {context.family ? (
        <p className="px-3 pb-2 text-xs text-stone-500">
          Семья: {context.family.name}
        </p>
      ) : null}
    </div>
  );
}
