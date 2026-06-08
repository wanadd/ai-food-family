"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AdminConfirmDialog } from "@/components/admin/AdminConfirmDialog";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  adminFamilyAction,
  adminFamilyAms,
  adminFamilySubscription,
  adminRemoveFamilyMember,
  adminRenameFamily,
  fetchAdminFamilyCard,
  fetchAdminPlans,
} from "@/lib/admin/api";
import { hasAdminAuthCredential } from "@/lib/admin/session";
import type { AdminFamilyCard, AdminPlanOption } from "@/lib/admin/types";

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString("ru-RU");
  } catch {
    return value;
  }
}

export function AdminFamilyDetailPage({ familyId }: { familyId: number }) {
  const { initData } = useTelegram();
  const [card, setCard] = useState<AdminFamilyCard | null>(null);
  const [plans, setPlans] = useState<AdminPlanOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [planCode, setPlanCode] = useState("family");
  const [days, setDays] = useState("30");
  const [amsAmount, setAmsAmount] = useState("100");
  const [newAdminUserId, setNewAdminUserId] = useState("");

  const reload = useCallback(async () => {
    if (!hasAdminAuthCredential(initData)) return;
    const auth = initData || null;
    const data = await fetchAdminFamilyCard(auth, familyId);
    setCard(data);
    if (data) setName(data.name);
    setPlans(await fetchAdminPlans(auth));
  }, [initData, familyId]);

  useEffect(() => {
    reload()
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка"))
      .finally(() => setLoading(false));
  }, [reload]);

  const run = async (fn: () => Promise<{ message: string }>) => {
    setError(null);
    try {
      const res = await fn();
      setMessage(res.message);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  };

  if (loading) return <PageLoading message="Загружаем семью..." />;
  if (!card) {
    return (
      <p className="text-sm text-stone-600">
        Семья не найдена.{" "}
        <Link href="/admin/families" className="text-teal-700">
          ← Назад
        </Link>
      </p>
    );
  }

  const sub = card.subscription;

  return (
    <div className="space-y-4">
      <Link href="/admin/families" className="text-sm text-teal-700">
        ← Семьи
      </Link>

      <header className="rounded-xl border border-stone-200 bg-white p-4">
        <h1 className="text-lg font-bold text-stone-900">{card.name}</h1>
        <p className="text-xs text-stone-500">
          id {card.id} · {card.member_count} участников · админ {card.admin_name}
        </p>
        <p className="text-[11px] text-stone-400">{formatDate(card.created_at)}</p>
        <div className="mt-2 flex gap-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 rounded border border-stone-300 px-2 py-1 text-sm"
          />
          <button
            type="button"
            className="rounded-lg bg-stone-800 px-3 py-1.5 text-xs text-white"
            onClick={() => run(() => adminRenameFamily(initData || null, familyId, name))}
          >
            Переименовать
          </button>
        </div>
      </header>

      {message ? (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <section className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
        <h2 className="font-semibold">Участники</h2>
        <ul className="mt-2 space-y-2">
          {card.members.map((m) => (
            <li
              key={m.id}
              className="flex items-center justify-between rounded-lg bg-stone-50 px-3 py-2 text-xs"
            >
              <span>
                {m.display_name} · {m.role}
                {m.is_virtual ? " · виртуальный" : ""}
                {m.user_id ? ` · user ${m.user_id}` : ""}
              </span>
              {!m.is_virtual && m.role !== "admin" ? (
                <AdminConfirmDialog
                  danger
                  triggerLabel="Удалить"
                  title="Удалить участника?"
                  description={`Участник ${m.display_name} будет удалён из семьи.`}
                  confirmLabel="Удалить"
                  onConfirm={() =>
                    run(() => adminRemoveFamilyMember(initData || null, familyId, m.id))
                  }
                />
              ) : null}
            </li>
          ))}
        </ul>
        <div className="mt-3 flex gap-2">
          <input
            type="number"
            placeholder="user_id нового админа"
            value={newAdminUserId}
            onChange={(e) => setNewAdminUserId(e.target.value)}
            className="flex-1 rounded border border-stone-300 px-2 py-1 text-sm"
          />
          <button
            type="button"
            className="rounded-lg bg-stone-800 px-3 py-1.5 text-xs text-white"
            onClick={() =>
              run(() =>
                adminFamilyAction(initData || null, familyId, "/transfer-owner", "POST", {
                  new_admin_user_id: Number(newAdminUserId),
                }),
              )
            }
          >
            Назначить админа
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
        <h2 className="font-semibold">Семейная подписка</h2>
        {sub ? (
          <p className="mt-1 text-xs text-stone-600">
            {sub.plan_code} · {sub.status} · {sub.grant_source}
          </p>
        ) : (
          <p className="mt-1 text-xs text-stone-500">Нет подписки</p>
        )}
        <select
          value={planCode}
          onChange={(e) => setPlanCode(e.target.value)}
          className="mt-2 w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
        >
          {plans.map((p) => (
            <option key={p.code} value={p.code}>
              {p.name}
            </option>
          ))}
        </select>
        <input
          type="number"
          value={days}
          onChange={(e) => setDays(e.target.value)}
          className="mt-2 w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
        />
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg bg-stone-800 px-3 py-1.5 text-xs text-white"
            onClick={() =>
              run(() =>
                adminFamilySubscription(initData || null, familyId, "grant", {
                  plan_code: planCode,
                  days: Number(days) || 30,
                }),
              )
            }
          >
            Выдать тариф
          </button>
          <button
            type="button"
            className="rounded-lg bg-stone-200 px-3 py-1.5 text-xs"
            onClick={() =>
              run(() =>
                adminFamilySubscription(initData || null, familyId, "extend", {
                  days: Number(days) || 30,
                }),
              )
            }
          >
            Продлить
          </button>
          <AdminConfirmDialog
            danger
            triggerLabel="Отключить"
            title="Отключить семейную подписку?"
            description="Все участники потеряют семейные возможности тарифа."
            confirmLabel="Отключить"
            onConfirm={() =>
              run(() => adminFamilySubscription(initData || null, familyId, "disable"))
            }
          />
          <button
            type="button"
            className="rounded-lg bg-violet-100 px-3 py-1.5 text-xs text-violet-900"
            onClick={() =>
              run(() =>
                adminFamilySubscription(initData || null, familyId, "grant", {
                  plan_code: "pro",
                  days: Number(days) || 14,
                  as_trial: true,
                }),
              )
            }
          >
            PRO на тест
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
        <h2 className="font-semibold">Семейный баланс Амов</h2>
        <p className="text-xs text-stone-600">Баланс: {card.ams.balance}</p>
        <input
          type="number"
          value={amsAmount}
          onChange={(e) => setAmsAmount(e.target.value)}
          className="mt-2 w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
        />
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg bg-stone-800 px-3 py-1.5 text-xs text-white"
            onClick={() =>
              run(() =>
                adminFamilyAms(initData || null, familyId, "add", {
                  amount: Number(amsAmount) || 0,
                }),
              )
            }
          >
            Начислить
          </button>
          <button
            type="button"
            className="rounded-lg bg-stone-200 px-3 py-1.5 text-xs"
            onClick={() =>
              run(() =>
                adminFamilyAms(initData || null, familyId, "remove", {
                  amount: Number(amsAmount) || 0,
                }),
              )
            }
          >
            Списать
          </button>
          <AdminConfirmDialog
            danger
            triggerLabel="Обнулить"
            title="Обнулить баланс семьи?"
            description="Весь семейный баланс Амов будет списан."
            confirmLabel="Обнулить"
            onConfirm={() => run(() => adminFamilyAms(initData || null, familyId, "reset"))}
          />
        </div>
      </section>

      <section className="rounded-xl border border-red-200 bg-red-50/50 p-4 text-sm space-y-2">
        <h2 className="font-semibold text-red-950">Опасные действия</h2>
        {!card.is_blocked ? (
          <AdminConfirmDialog
            danger
            triggerLabel="Заблокировать семью"
            title={`Заблокировать «${card.name}»?`}
            description="Участники не смогут пользоваться семейным режимом."
            confirmLabel="Заблокировать"
            onConfirm={() =>
              run(() => adminFamilyAction(initData || null, familyId, "/block", "POST", {}))
            }
          />
        ) : (
          <button
            type="button"
            className="rounded-lg bg-stone-800 px-3 py-2 text-xs text-white"
            onClick={() =>
              run(() => adminFamilyAction(initData || null, familyId, "/unblock", "POST"))
            }
          >
            Разблокировать
          </button>
        )}
        <AdminConfirmDialog
          danger
          triggerLabel="Удалить семью"
          title={`Удалить семью «${card.name}»?`}
          description="Telegram-пользователи не удаляются. Семейные меню, покупки и запасы будут удалены вместе с семьёй."
          confirmLabel="Удалить"
          onConfirm={() =>
            run(() => adminFamilyAction(initData || null, familyId, "", "DELETE"))
          }
        />
      </section>
    </div>
  );
}
