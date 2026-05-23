"use client";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import type { AppMode } from "@/lib/app-mode/types";

export function ProfileModeControl() {
  const { mode, context, loading, setMode } = useAppMode();

  if (loading) {
    return (
      <p className="text-sm text-stone-500" aria-live="polite">
        Загрузка режима…
      </p>
    );
  }

  const modeLabel = mode === "family" ? "Семейный" : "Личный";
  const familyName = context?.family?.name;

  if (!context?.can_use_family_mode) {
    return (
      <div className="inline-flex items-center gap-2">
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800">
          {modeLabel}
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex rounded-xl bg-stone-100/90 p-1">
        {(["personal", "family"] as AppMode[]).map((option) => {
          const isActive = mode === option;
          return (
            <button
              key={option}
              type="button"
              onClick={() => void setMode(option)}
              className={`min-h-[40px] flex-1 rounded-lg text-sm font-semibold transition active:scale-[0.98] ${
                isActive
                  ? option === "family"
                    ? "bg-violet-600 text-white shadow-sm"
                    : "bg-emerald-600 text-white shadow-sm"
                  : "text-stone-600"
              }`}
            >
              {option === "personal" ? "Личный" : "Семейный"}
            </button>
          );
        })}
      </div>
      {familyName ? (
        <p className="text-center text-xs text-stone-500">Семья «{familyName}»</p>
      ) : null}
    </div>
  );
}
