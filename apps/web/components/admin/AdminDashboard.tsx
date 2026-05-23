"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PageLoading } from "@/components/ui/PageLoading";
import {
  createAdminBackup,
  fetchAdminAiUsage,
  fetchAdminBackups,
  fetchAdminFamilies,
  fetchAdminPlans,
  fetchAdminSubscriptions,
  fetchAdminSummary,
  fetchAdminUsers,
  grantAdminAms,
  grantAdminSubscription,
} from "@/lib/admin/api";
import type {
  AdminAiUsageRow,
  AdminBackupRow,
  AdminFamilyRow,
  AdminPlanOption,
  AdminSubscriptionRow,
  AdminSummary,
  AdminUserRow,
} from "@/lib/admin/types";
import { getTelegramInitData } from "@/lib/telegram-webapp";

type Tab =
  | "summary"
  | "users"
  | "families"
  | "subscriptions"
  | "ams"
  | "ai"
  | "backups";

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function ConfirmButton({
  label,
  confirmText,
  onConfirm,
  disabled,
  variant = "primary",
}: {
  label: string;
  confirmText: string;
  onConfirm: () => void | Promise<void>;
  disabled?: boolean;
  variant?: "primary" | "danger";
}) {
  const [armed, setArmed] = useState(false);

  const base =
    variant === "danger"
      ? "bg-red-600 text-white"
      : "bg-stone-800 text-white";

  if (!armed) {
    return (
      <button
        type="button"
        disabled={disabled}
        onClick={() => setArmed(true)}
        className={`rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-50 ${base}`}
      >
        {label}
      </button>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        onClick={async () => {
          await onConfirm();
          setArmed(false);
        }}
        className="rounded-lg bg-red-600 px-3 py-2 text-sm font-semibold text-white"
      >
        {confirmText}
      </button>
      <button
        type="button"
        onClick={() => setArmed(false)}
        className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700"
      >
        Отмена
      </button>
    </div>
  );
}

export function AdminDashboard() {
  const [tab, setTab] = useState<Tab>("summary");
  const [loading, setLoading] = useState(true);
  const [forbidden, setForbidden] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [families, setFamilies] = useState<AdminFamilyRow[]>([]);
  const [subscriptions, setSubscriptions] = useState<AdminSubscriptionRow[]>([]);
  const [aiUsage, setAiUsage] = useState<AdminAiUsageRow[]>([]);
  const [backups, setBackups] = useState<AdminBackupRow[]>([]);
  const [plans, setPlans] = useState<AdminPlanOption[]>([]);

  const [grantUserId, setGrantUserId] = useState("");
  const [grantPlan, setGrantPlan] = useState("family");
  const [grantDays, setGrantDays] = useState("30");
  const [promoNote, setPromoNote] = useState("");
  const [amsUserId, setAmsUserId] = useState("");
  const [amsAmount, setAmsAmount] = useState("100");

  const initData = getTelegramInitData();

  const loadTab = useCallback(async () => {
    if (!initData) {
      setError("Откройте админку из Telegram Mini App");
      setLoading(false);
      return;
    }
    setError(null);
    try {
      if (tab === "summary") {
        const data = await fetchAdminSummary(initData);
        if (!data) {
          setForbidden(true);
          return;
        }
        setSummary(data);
        setForbidden(false);
      } else if (tab === "users") {
        setUsers(await fetchAdminUsers(initData));
      } else if (tab === "families") {
        setFamilies(await fetchAdminFamilies(initData));
      } else if (tab === "subscriptions") {
        setSubscriptions(await fetchAdminSubscriptions(initData));
        setPlans(await fetchAdminPlans(initData));
      } else if (tab === "ai") {
        setAiUsage(await fetchAdminAiUsage(initData));
      } else if (tab === "backups") {
        setBackups(await fetchAdminBackups(initData));
      } else if (tab === "ams") {
        setPlans(await fetchAdminPlans(initData));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    }
  }, [initData, tab]);

  useEffect(() => {
    setLoading(true);
    loadTab().finally(() => setLoading(false));
  }, [loadTab]);

  const handleGrantPlan = async () => {
    if (!initData) return;
    const userId = Number(grantUserId);
    if (!userId) {
      setError("Укажите user_id");
      return;
    }
    const result = await grantAdminSubscription(initData, {
      user_id: userId,
      plan_code: grantPlan,
      extend_days: Number(grantDays) || 30,
      promo_note: promoNote || undefined,
    });
    setMessage(result.message);
    await loadTab();
  };

  const handleGrantAms = async () => {
    if (!initData) return;
    const userId = Number(amsUserId);
    const amount = Number(amsAmount);
    if (!userId || !amount) {
      setError("Укажите user_id и сумму Амов");
      return;
    }
    const result = await grantAdminAms(initData, { user_id: userId, amount });
    setMessage(result.message);
  };

  const handleCreateBackup = async () => {
    if (!initData) return;
    const result = await createAdminBackup(initData);
    setMessage(result.message);
    setBackups(await fetchAdminBackups(initData));
  };

  if (loading && !summary && !forbidden) {
    return <PageLoading message="Загружаем админку..." />;
  }

  if (forbidden) {
    return (
      <div className="mx-auto max-w-lg px-4 py-10 text-center">
        <h1 className="text-lg font-bold text-stone-900">Нет доступа</h1>
        <p className="mt-2 text-sm text-stone-600">
          Раздел только для владельца проекта. Проверьте ADMIN_TELEGRAM_IDS на
          сервере.
        </p>
        <Link href="/profile" className="mt-6 inline-block text-sm text-teal-700">
          ← В профиль
        </Link>
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "summary", label: "Сводка" },
    { id: "users", label: "Пользователи" },
    { id: "families", label: "Семьи" },
    { id: "subscriptions", label: "Подписки" },
    { id: "ams", label: "Амы" },
    { id: "ai", label: "AI" },
    { id: "backups", label: "Backup" },
  ];

  return (
    <div className="min-h-screen bg-stone-100 pb-24">
      <header className="sticky top-0 z-10 border-b border-stone-200 bg-white px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-lg font-bold text-stone-900">Админ ПланАм</h1>
          <Link href="/profile" className="text-xs text-stone-500">
            Профиль
          </Link>
        </div>
        <div className="mt-2 flex gap-1 overflow-x-auto pb-1">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
                tab === item.id
                  ? "bg-stone-900 text-white"
                  : "bg-stone-200 text-stone-700"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-3 px-4 py-4">
        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}
        {message ? (
          <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            {message}
          </p>
        ) : null}

        {tab === "summary" && summary ? (
          <section className="grid grid-cols-2 gap-2">
            {[
              ["Пользователей", summary.total_users],
              ["Сегодня", summary.users_today],
              ["Семей", summary.total_families],
              ["Активных подписок", summary.active_subscriptions],
              ["Амов списано", summary.ams_used_total],
              ["AI-запросов", summary.ai_requests_total],
              [
                "AI cost (USD)",
                summary.ai_estimated_cost_usd.toFixed(4),
              ],
              ["Ошибок 24ч", summary.errors_last_24h],
            ].map(([label, value]) => (
              <div
                key={String(label)}
                className="rounded-xl border border-stone-200 bg-white p-3"
              >
                <p className="text-[11px] text-stone-500">{label}</p>
                <p className="mt-1 text-lg font-semibold text-stone-900">{value}</p>
              </div>
            ))}
          </section>
        ) : null}

        {tab === "users" ? (
          <section className="space-y-2">
            {users.map((user) => (
              <article
                key={user.id}
                className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
              >
                <p className="font-semibold text-stone-900">{user.display_name}</p>
                <p className="text-xs text-stone-500">
                  @{user.username ?? "—"} · tg {user.telegram_id}
                </p>
                <p className="mt-1 text-xs text-stone-600">
                  {user.plan_code} ({user.plan_status}) · {user.ama_balance} Амов ·
                  меню: {user.menu_count}
                </p>
                <p className="text-[11px] text-stone-400">
                  Рег: {formatDate(user.created_at)} · Активность:{" "}
                  {formatDate(user.last_activity_at)}
                </p>
              </article>
            ))}
          </section>
        ) : null}

        {tab === "families" ? (
          <section className="space-y-2">
            {families.map((family) => (
              <article
                key={family.id}
                className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
              >
                <p className="font-semibold">{family.name}</p>
                <p className="text-xs text-stone-600">
                  Участников: {family.member_count} · Тариф: {family.plan_code}
                </p>
                <p className="text-xs text-stone-500">
                  Админ: {family.admin_name} · {formatDate(family.created_at)}
                </p>
              </article>
            ))}
          </section>
        ) : null}

        {tab === "subscriptions" ? (
          <>
            <section className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm">
              <p className="font-medium text-amber-950">Выдать тариф</p>
              <div className="mt-2 space-y-2">
                <input
                  type="number"
                  placeholder="user_id"
                  value={grantUserId}
                  onChange={(e) => setGrantUserId(e.target.value)}
                  className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
                />
                <select
                  value={grantPlan}
                  onChange={(e) => setGrantPlan(e.target.value)}
                  className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
                >
                  {plans.map((plan) => (
                    <option key={plan.code} value={plan.code}>
                      {plan.name} ({plan.code})
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  placeholder="Дней"
                  value={grantDays}
                  onChange={(e) => setGrantDays(e.target.value)}
                  className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
                />
                <input
                  type="text"
                  placeholder="Промо / комментарий"
                  value={promoNote}
                  onChange={(e) => setPromoNote(e.target.value)}
                  className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
                />
                <ConfirmButton
                  label="Выдать тариф"
                  confirmText="Подтвердить выдачу"
                  onConfirm={handleGrantPlan}
                />
              </div>
            </section>
            <section className="space-y-2">
              {subscriptions.map((sub) => (
                <article
                  key={sub.id}
                  className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
                >
                  <p className="font-semibold">{sub.user_name}</p>
                  <p className="text-xs text-stone-600">
                    {sub.plan_code} · {sub.status} · меню {sub.menu_generations_used}
                  </p>
                  <p className="text-[11px] text-stone-400">
                    user_id {sub.user_id} · {formatDate(sub.started_at)}
                  </p>
                </article>
              ))}
            </section>
          </>
        ) : null}

        {tab === "ams" ? (
          <section className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm">
            <p className="font-medium text-amber-950">Начислить Амы</p>
            <div className="mt-2 space-y-2">
              <input
                type="number"
                placeholder="user_id"
                value={amsUserId}
                onChange={(e) => setAmsUserId(e.target.value)}
                className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
              />
              <input
                type="number"
                placeholder="Количество Амов"
                value={amsAmount}
                onChange={(e) => setAmsAmount(e.target.value)}
                className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
              />
              <ConfirmButton
                label="Начислить Амы"
                confirmText="Подтвердить начисление"
                variant="danger"
                onConfirm={handleGrantAms}
              />
            </div>
          </section>
        ) : null}

        {tab === "ai" ? (
          <section className="space-y-2">
            {aiUsage.map((row) => (
              <article
                key={row.id}
                className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
              >
                <p className="font-medium">{row.action_type}</p>
                <p className="text-xs text-stone-600">
                  {row.user_name} · {row.ams_spent} Амов · {row.model ?? "—"}
                </p>
                <p className="text-[11px] text-stone-400">
                  {row.input_tokens ?? "—"} / {row.output_tokens ?? "—"} tok · cost{" "}
                  {row.estimated_cost ?? "—"} · {formatDate(row.created_at)}
                </p>
              </article>
            ))}
          </section>
        ) : null}

        {tab === "backups" ? (
          <section className="space-y-3">
            <ConfirmButton
              label="Создать backup"
              confirmText="Подтвердить создание"
              variant="danger"
              onConfirm={handleCreateBackup}
            />
            <p className="text-xs text-stone-500">
              На сервере также: ./scripts/backup.sh (см. docs/DEPLOY_SAFE.md)
            </p>
            {backups.map((backup) => (
              <article
                key={backup.id}
                className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
              >
                <p className="font-semibold">{backup.id}</p>
                <p className="text-xs text-stone-600">
                  {formatBytes(backup.size_bytes)} · БД:{" "}
                  {backup.has_database ? "да" : "нет"} · .env:{" "}
                  {backup.has_env ? "да" : "нет"}
                </p>
                <p className="text-[11px] text-stone-400">{backup.created_at}</p>
              </article>
            ))}
          </section>
        ) : null}
      </main>
    </div>
  );
}
