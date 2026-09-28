"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import { buildApiUrl } from "@/lib/api-base";

export function MaintenanceBoundary({ children }: { children: ReactNode }) {
  const enforce = process.env.NEXT_PUBLIC_PLANAM_CUTOVER_ENFORCE === "true";
  const [paused, setPaused] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(buildApiUrl("/health/cutover"), { cache: "no-store" });
      if (response.ok) {
        const state = (await response.json()) as { write_paused?: boolean };
        setPaused(state.write_paused === true);
      } else if (response.status === 503) {
        setPaused(true);
      }
    } catch {
      // A network failure alone does not prove a cutover pause.
    }
  }, []);

  useEffect(() => {
    if (!enforce) return;
    const onPaused = () => setPaused(true);
    window.addEventListener("planam:write-paused", onPaused);
    void refresh();
    const timer = window.setInterval(() => void refresh(), 30_000);
    return () => {
      window.removeEventListener("planam:write-paused", onPaused);
      window.clearInterval(timer);
    };
  }, [enforce, refresh]);

  if (enforce && paused) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-pa-canvas px-6 text-center text-pa-foreground" role="status">
        <h1 className="text-2xl font-semibold">ПланАм временно на обслуживании</h1>
        <p className="max-w-md text-sm text-pa-muted">Ваши данные сохранены. Доступ восстановится после завершения работ.</p>
        <button type="button" onClick={() => void refresh()} className="min-h-11 rounded border border-pa-border bg-pa-surface px-4 text-sm font-medium">
          Проверить доступ
        </button>
      </main>
    );
  }
  return children;
}
