"use client";

import { useEffect, useState } from "react";

import { fetchAdminAnalytics } from "@/lib/admin/v2-api";

export function AdminAnalyticsV2() {
  const [state, setState] = useState<{ state: string; message: string } | null>(null);
  useEffect(() => { fetchAdminAnalytics().then(setState).catch(() => setState({ state: "unavailable", message: "Аналитика недоступна." })); }, []);
  return <section className="border border-stone-200 bg-white p-5"><p className="text-xs uppercase tracking-wide text-stone-500">Analytics</p><h2 className="mt-1 text-2xl font-semibold">Продуктовая аналитика</h2><p className="mt-3 text-sm text-stone-600">{state?.message ?? "Проверяем состояние хранилища..."}</p></section>;
}
