"use client";

import { useCallback, useEffect, useState } from "react";

import { PageLoading } from "@/components/ui/PageLoading";
import {
  fetchAdminFamilies,
  fetchAdminPlans,
  fetchAdminSubscriptions,
  fetchAdminSummary,
  fetchAdminAmaTransactions,
  fetchAdminAmsSummary,
  fetchAdminUsers,
  grantAdminAms,
  grantAdminFamilyAms,
  grantAdminSubscription,
} from "@/lib/admin/api";
import type {
  AdminAmaTransactionRow,
  AdminAmsSummary,
  AdminFamilyRow,
  AdminPlanOption,
  AdminSubscriptionRow,
  AdminSummary,
  AdminTab,
  AdminUserRow,
} from "@/lib/admin/types";
import { useTelegram } from "@/components/TelegramProvider";

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

export function AdminDashboard({ forcedTab = "summary" }: { forcedTab?: AdminTab }) {
  const tab = forcedTab;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [families, setFamilies] = useState<AdminFamilyRow[]>([]);
  const [subscriptions, setSubscriptions] = useState<AdminSubscriptionRow[]>([]);
  const [amsSummary, setAmsSummary] = useState<AdminAmsSummary | null>(null);
  const [amaTx, setAmaTx] = useState<AdminAmaTransactionRow[]>([]);
  const [plans, setPlans] = useState<AdminPlanOption[]>([]);

  const [userSearch, setUserSearch] = useState("");
  const [userFilter, setUserFilter] = useState("all");

  const [grantUserId, setGrantUserId] = useState("");
  const [grantPlan, setGrantPlan] = useState("family");
  const [grantDays, setGrantDays] = useState("30");
  const [promoNote, setPromoNote] = useState("");
  const [amsUserId, setAmsUserId] = useState("");
  const [amsFamilyId, setAmsFamilyId] = useState("");
  const [amsAmount, setAmsAmount] = useState("100");

  const { initData } = useTelegram();

  const loadTab = useCallback(async () => {
    if (!initData) {
      setError("Откройте админку из Telegram Mini App");
      setLoading(false);
      return;
    }
    setError(null);
    try {
      if (tab === "summary") {
        setSummary(await fetchAdminSummary(initData));
      } else if (tab === "users") {
        setUsers(
          await fetchAdminUsers(initData, {
            q: userSearch || undefined,
            filter: userFilter,
          }),
        );
      } else if (tab === "families") {
        setFamilies(await fetchAdminFamilies(initData));
      } else if (tab === "subscriptions") {
        setSubscriptions(await fetchAdminSubscriptions(initData));
        setPlans(await fetchAdminPlans(initData));
      } else if (tab === "ams") {
        setAmsSummary(await fetchAdminAmsSummary(initData));
        setAmaTx(await fetchAdminAmaTransactions(initData));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    }
  }, [initData, tab, userSearch, userFilter]);

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

  const handleGrantFamilyAms = async () => {
    if (!initData) return;
    const familyId = Number(amsFamilyId);
    const amount = Number(amsAmount);
    if (!familyId || !amount) {
      setError("Укажите family_id и сумму");
      return;
    }
    const result = await grantAdminFamilyAms(initData, {
      family_id: familyId,
      amount,
    });
    setMessage(result.message);
    await loadTab();
  };

  if (loading && tab === "summary" && !summary) {
    return <PageLoading message="Загружаем..." />;
  }

  return (
    <div className="space-y-3">
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
              ["Активно сегодня", summary.active_today],
              ["Активно 7 дней", summary.active_7d],
              ["Семей", summary.total_families],
              ["Подписок", summary.active_subscriptions],
              ["Бесплатных", summary.free_users],
              ["Баланс Амов", summary.total_ams_balance],
              ["OpenAI сегодня $", summary.openai_cost_today_usd.toFixed(4)],
              ["OpenAI месяц $", summary.openai_cost_month_usd.toFixed(4)],
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
            <div className="space-y-2 rounded-xl border border-stone-200 bg-white p-3">
              <input
                type="search"
                placeholder="Имя, username или Telegram ID"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
              />
              <select
                value={userFilter}
                onChange={(e) => setUserFilter(e.target.value)}
                className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
              >
                <option value="all">Все</option>
                <option value="active">Активные</option>
                <option value="free">Бесплатные</option>
                <option value="paid">Платные</option>
                <option value="blocked">Заблокированные</option>
              </select>
            </div>
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
                  {user.family_name ? ` ${user.family_name} ·` : ""} {user.status}
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
          <>
            {amsSummary ? (
              <section className="grid grid-cols-2 gap-2">
                {[
                  ["Начислено", amsSummary.credited_total],
                  ["Списано", amsSummary.debited_total],
                  ["Баланс users", amsSummary.user_balance_total],
                  ["Баланс families", amsSummary.family_balance_total],
                  ["Сегодня", amsSummary.spent_today],
                  ["Месяц", amsSummary.spent_month],
                ].map(([label, value]) => (
                  <div
                    key={String(label)}
                    className="rounded-xl border border-stone-200 bg-white p-3"
                  >
                    <p className="text-[11px] text-stone-500">{label}</p>
                    <p className="mt-1 text-lg font-semibold">{value}</p>
                  </div>
                ))}
              </section>
            ) : null}
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
                  placeholder="family_id (семья)"
                  value={amsFamilyId}
                  onChange={(e) => setAmsFamilyId(e.target.value)}
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
                  label="Начислить пользователю"
                  confirmText="Подтвердить"
                  variant="danger"
                  onConfirm={handleGrantAms}
                />
                <ConfirmButton
                  label="Начислить семье"
                  confirmText="Подтвердить"
                  onConfirm={handleGrantFamilyAms}
                />
              </div>
            </section>
            <section className="space-y-2">
              {amaTx.map((tx) => (
                <article
                  key={tx.id}
                  className="rounded-xl border border-stone-200 bg-white p-3 text-sm"
                >
                  <p className="font-medium">
                    {tx.amount > 0 ? "+" : ""}
                    {tx.amount} · {tx.reason}
                  </p>
                  <p className="text-xs text-stone-500">
                    user {tx.user_id ?? "—"} · family {tx.family_id ?? "—"} ·{" "}
                    {formatDate(tx.created_at)}
                  </p>
                </article>
              ))}
            </section>
          </>
        ) : null}
    </div>
  );
}
