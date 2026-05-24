"use client";

import { useEffect, useState } from "react";

import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import { fetchAdminErrors } from "@/lib/admin/api";
import type { AdminErrorRow } from "@/lib/admin/types";

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString("ru-RU");
  } catch {
    return value;
  }
}

export function AdminErrorsPage() {
  const { initData } = useTelegram();
  const [rows, setRows] = useState<AdminErrorRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!initData) return;
    fetchAdminErrors(initData)
      .then(setRows)
      .finally(() => setLoading(false));
  }, [initData]);

  if (loading) {
    return <PageLoading message="Загружаем ошибки..." />;
  }

  return (
    <section className="space-y-2">
      {rows.length === 0 ? (
        <p className="text-sm text-stone-600">Ошибок нет</p>
      ) : (
        rows.map((row) => (
          <article
            key={row.id}
            className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-stone-900">{row.error_type}</span>
              <span className="text-[11px] text-stone-400">
                {formatDate(row.created_at)}
              </span>
            </div>
            {row.endpoint ? (
              <p className="mt-1 text-xs text-stone-500">{row.endpoint}</p>
            ) : null}
            <p className="mt-1 text-xs text-stone-700 line-clamp-4">{row.message}</p>
            <p className="mt-1 text-[11px] text-stone-400">
              {row.status ?? "—"}
              {row.user_id ? ` · user ${row.user_id}` : ""}
              {row.family_id ? ` · family ${row.family_id}` : ""}
            </p>
          </article>
        ))
      )}
    </section>
  );
}
