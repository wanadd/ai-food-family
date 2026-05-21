"use client";

import { useAppMode } from "@/components/app-mode/AppModeProvider";

export function ModeBanner() {
  const { mode, context } = useAppMode();

  if (mode === "family" && context?.family) {
    return (
      <p className="rounded-xl border border-violet-200 bg-violet-50 px-4 py-2 text-sm text-violet-900">
        Семейный режим · {context.family.name}
      </p>
    );
  }

  return (
    <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-900">
      Личный режим · данные только для вас
    </p>
  );
}
