"use client";

import { useEffect, useState } from "react";

import { fetchAdminOverview, type AdminOverview } from "@/lib/admin/v2-api";

function Metric({ label, metric }: { label: string; metric: { value: number | null; state: string } }) {
  return (
    <article className="border border-stone-200 bg-white p-4">
      <p className="text-xs text-stone-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-stone-900">
        {metric.state === "available" && metric.value !== null ? metric.value : "Нет данных"}
      </p>
      {metric.state !== "available" ? <p className="mt-1 text-xs text-stone-500">{metric.state}</p> : null}
    </article>
  );
}

export function AdminOverviewV2() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetchAdminOverview().then(setOverview).catch((reason: Error) => setError(reason.message));
  }, []);
  if (error) return <p className="border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</p>;
  if (!overview) return <p className="p-4 text-sm text-stone-600">Загружаем операционный обзор...</p>;
  return (
    <section>
      <div className="mb-5 flex items-end justify-between gap-4">
        <div><p className="text-xs uppercase tracking-wide text-stone-500">Operations</p><h2 className="text-2xl font-semibold text-stone-950">Обзор системы</h2></div>
        <time className="text-xs text-stone-500">{new Date(overview.generated_at).toLocaleString("ru-RU")}</time>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="API" metric={overview.api} />
        <Metric label="База данных" metric={overview.database} />
        <Metric label="Accounts" metric={overview.users} />
        <Metric label="Households" metric={overview.households} />
        <Metric label="Активные entitlement" metric={overview.active_subscriptions} />
        <Metric label="Ошибки за 24 часа" metric={overview.errors_last_24h} />
        <Metric label="Analytics" metric={overview.analytics} />
      </div>
    </section>
  );
}
