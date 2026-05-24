"use client";

import { useCallback, useEffect, useState } from "react";

import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchAdminOpenAi } from "@/lib/admin/api";
import type { AdminOpenAiStats } from "@/lib/admin/types";

const PERIODS = [
  { id: "today", label: "Сегодня" },
  { id: "7d", label: "7 дней" },
  { id: "30d", label: "30 дней" },
  { id: "month", label: "Месяц" },
] as const;

export function AdminOpenAiPage() {
  const { initData } = useTelegram();
  const [period, setPeriod] = useState<string>("30d");
  const [stats, setStats] = useState<AdminOpenAiStats | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!initData) return;
    setLoading(true);
    const data = await fetchAdminOpenAi(initData, period);
    setStats(data);
    setLoading(false);
  }, [initData, period]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !stats) {
    return <PageLoading message="Загружаем расходы..." />;
  }

  if (!stats) {
    return <p className="text-sm text-stone-600">Нет данных</p>;
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1">
        {PERIODS.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setPeriod(p.id)}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              period === p.id
                ? "bg-stone-900 text-white"
                : "bg-stone-200 text-stone-700"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <section className="grid grid-cols-2 gap-2">
        {[
          ["Запросов", stats.requests],
          ["OpenAI $", stats.openai_cost_usd.toFixed(4)],
          ["Input tok", stats.input_tokens],
          ["Output tok", stats.output_tokens],
          ["Амов", stats.ams_spent],
          ["Меню", stats.menu_generations],
          ["Ср. запрос $", stats.avg_request_cost_usd.toFixed(5)],
          ["Ср. меню $", stats.avg_menu_cost_usd.toFixed(5)],
        ].map(([label, value]) => (
          <div
            key={String(label)}
            className="rounded-xl border border-stone-200 bg-white p-3"
          >
            <p className="text-[11px] text-stone-500">{label}</p>
            <p className="mt-1 text-sm font-semibold text-stone-900">{value}</p>
          </div>
        ))}
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-stone-800">По категориям</h2>
        {stats.categories.map((cat) => (
          <article
            key={cat.category}
            className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
          >
            <p className="font-medium">{cat.category}</p>
            <p className="text-xs text-stone-600">
              {cat.requests} запр. · ${cat.openai_cost_usd.toFixed(4)} · {cat.ams_spent}{" "}
              Амов
            </p>
          </article>
        ))}
      </section>
    </div>
  );
}
