"use client";

import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  services: {
    postgres: string;
    redis: string;
  };
};

type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

export function HealthStatus({ apiUrl }: { apiUrl: string }) {
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = (await response.json()) as HealthResponse;
        if (!cancelled) {
          setHealth({ kind: "ok", data });
        }
      } catch (error) {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Unknown error";
          setHealth({ kind: "error", message });
        }
      }
    }

    loadHealth();

    return () => {
      cancelled = true;
    };
  }, [apiUrl]);

  if (health.kind === "loading") {
    return <p className="text-sm text-slate-500">Проверяем backend…</p>;
  }

  if (health.kind === "error") {
    return (
      <p className="text-sm text-amber-700">
        Backend недоступен: {health.message}
      </p>
    );
  }

  const badgeClass =
    health.data.status === "ok"
      ? "bg-emerald-100 text-emerald-800"
      : "bg-amber-100 text-amber-800";

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-500">Статус API</span>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase ${badgeClass}`}
        >
          {health.data.status}
        </span>
      </div>
      <ul className="grid gap-1 text-sm text-slate-600">
        <li>PostgreSQL: {health.data.services.postgres}</li>
        <li>Redis: {health.data.services.redis}</li>
      </ul>
    </div>
  );
}
