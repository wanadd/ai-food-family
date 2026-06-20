"use client";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import type { AppMode } from "@/lib/app-mode/types";

export function ProfileModeControl() {
  const { mode, context, loading, setMode } = useAppMode();

  if (loading) {
    return (
      <p className="text-sm text-graphite-500" aria-live="polite">
        Загрузка режима…
      </p>
    );
  }

  const modeLabel = mode === "family" ? "Семейный" : "Личный";
  const familyName = context?.family?.name;

  if (!context?.can_use_family_mode) {
    return (
      <div className="inline-flex items-center gap-2">
        <span className="pa-chip">{modeLabel}</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex rounded-control bg-cream-deep p-1">
        {(["personal", "family"] as AppMode[]).map((option) => {
          const isActive = mode === option;
          return (
            <button
              key={option}
              type="button"
              onClick={() => void setMode(option)}
              className={`min-h-[40px] flex-1 rounded-control text-sm font-semibold transition active:scale-[0.98] ${
                isActive
                  ? "bg-sage-500 text-white shadow-soft"
                  : "text-graphite-600"
              }`}
            >
              {option === "personal" ? "Личный" : "Семейный"}
            </button>
          );
        })}
      </div>
      {familyName ? (
        <p className="text-center text-xs text-graphite-500">Семья «{familyName}»</p>
      ) : null}
    </div>
  );
}
