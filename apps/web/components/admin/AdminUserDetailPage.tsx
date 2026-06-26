"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AdminConfirmDialog } from "@/components/admin/AdminConfirmDialog";
import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import {
  adminUserAction,
  adminUserAms,
  adminUserSubscription,
  fetchAdminPlans,
  fetchAdminUserCard,
} from "@/lib/admin/api";
import { hasAdminAuthCredential } from "@/lib/admin/session";
import type { AdminPlanOption, AdminUserCard } from "@/lib/admin/types";

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleString("ru-RU");
  } catch {
    return value;
  }
}

export function AdminUserDetailPage({ userId }: { userId: number }) {
  const { initData } = useTelegram();
  const [card, setCard] = useState<AdminUserCard | null>(null);
  const [plans, setPlans] = useState<AdminPlanOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [planCode, setPlanCode] = useState("family");
  const [days, setDays] = useState("30");
  const [amsAmount, setAmsAmount] = useState("100");
  const [blockReason, setBlockReason] = useState("");

  const reload = useCallback(async () => {
    if (!hasAdminAuthCredential(initData)) return;
    const auth = initData || null;
    const data = await fetchAdminUserCard(auth, userId);
    setCard(data);
    setPlans(await fetchAdminPlans(auth));
  }, [initData, userId]);

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

  if (loading) return <PageLoading message="Загружаем карточку..." />;
  if (!card) {
    return (
      <p className="text-sm text-stone-600">
        Пользователь не найден.{" "}
        <Link href="/admin/users" className="text-teal-700">
          ← Назад
        </Link>
      </p>
    );
  }

  const sub = card.subscription;

  return (
    <div className="space-y-4">
      <Link href="/admin/users" className="text-sm text-teal-700">
        ← Пользователи
      </Link>

      <header className="rounded-xl border border-stone-200 bg-white p-4">
        <h1 className="text-lg font-bold text-stone-900">{card.display_name}</h1>
        <p className="text-xs text-stone-500">
          @{card.username ?? "—"} · tg {card.telegram_id} · id {card.id}
        </p>
        <p className="mt-1 text-xs text-stone-600">
          {card.family_name ? `Семья: ${card.family_name}` : "Без семьи"} ·{" "}
          <span className={card.is_blocked ? "text-red-700 font-semibold" : card.is_deleted ? "text-amber-700 font-semibold" : "text-emerald-700 font-semibold"}>
            {card.is_blocked ? "Заблокирован" : card.is_deleted ? "В архиве" : "Активен"}
          </span>
          {sub ? ` · ${sub.plan_code} (${sub.status})` : " · без подписки"}
        </p>
        <p className="text-[11px] text-stone-400">
          Рег: {formatDate(card.created_at)} · Активность:{" "}
          {formatDate(card.last_activity_at)}
        </p>
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
        <h2 className="font-semibold text-stone-900">Подписка</h2>
        {sub ? (
          <p className="mt-1 text-xs text-stone-600">
            {sub.plan_code} · {sub.status} · до{" "}
            {sub.current_period_ends_at
              ? formatDate(sub.current_period_ends_at)
              : "—"}{" "}
            · {sub.grant_source} / {sub.kind}
          </p>
        ) : (
          <p className="mt-1 text-xs text-stone-500">Нет активной подписки</p>
        )}
        <div className="mt-3 space-y-2">
          <select
            value={planCode}
            onChange={(e) => setPlanCode(e.target.value)}
            className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
          >
            {plans.map((p) => (
              <option key={p.code} value={p.code}>
                {p.name} ({p.code})
              </option>
            ))}
          </select>
          <input
            type="number"
            value={days}
            onChange={(e) => setDays(e.target.value)}
            placeholder="Дней"
            className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-lg bg-stone-800 px-3 py-1.5 text-xs text-white"
              onClick={() =>
                run(() =>
                  adminUserSubscription(initData || null, userId, "grant", {
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
                  adminUserSubscription(initData || null, userId, "extend", {
                    days: Number(days) || 30,
                  }),
                )
              }
            >
              Продлить
            </button>
            <button
              type="button"
              className="rounded-lg bg-stone-200 px-3 py-1.5 text-xs"
              onClick={() =>
                run(() =>
                  adminUserSubscription(initData || null, userId, "change-plan", {
                    plan_code: planCode,
                    days: Number(days) || 30,
                  }),
                )
              }
            >
              Сменить тариф
            </button>
            <AdminConfirmDialog
              danger
              triggerLabel="Отключить подписку"
              title="Отключить подписку?"
              description="Пользователь потеряет платные возможности до новой выдачи тарифа."
              confirmLabel="Отключить"
              onConfirm={() =>
                run(() => adminUserSubscription(initData || null, userId, "disable"))
              }
            />
            <button
              type="button"
              className="rounded-lg bg-violet-100 px-3 py-1.5 text-xs text-violet-900"
              onClick={() =>
                run(() =>
                  adminUserSubscription(initData || null, userId, "grant", {
                    plan_code: "start",
                    days: 7,
                    as_trial: true,
                  }),
                )
              }
            >
              Старт 7 дней
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
        <h2 className="font-semibold text-stone-900">Амы</h2>
        <p className="mt-1 text-xs text-stone-600">
          Баланс: {card.ams.balance} · начислено {card.ams.credited_total} · потрачено{" "}
          {card.ams.spent_total}
        </p>
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
                adminUserAms(initData || null, userId, "add", {
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
                adminUserAms(initData || null, userId, "remove", {
                  amount: Number(amsAmount) || 0,
                }),
              )
            }
          >
            Списать
          </button>
          <AdminConfirmDialog
            danger
            triggerLabel="Обнулить баланс"
            title="Обнулить Амы?"
            description="Весь текущий баланс пользователя будет списан."
            confirmLabel="Обнулить"
            onConfirm={() => run(() => adminUserAms(initData || null, userId, "reset"))}
          />
        </div>
        <ul className="mt-3 space-y-1 border-t border-stone-100 pt-2">
          {card.ams.transactions.map((tx) => (
            <li key={tx.id} className="text-[11px] text-stone-500">
              {tx.amount > 0 ? "+" : ""}
              {tx.amount} {tx.reason} · {formatDate(tx.created_at)}
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
        <h2 className="font-semibold text-stone-900">Сбросы</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {[
            ["Onboarding", "/reset/onboarding"],
            ["Телефон", "/reset/phone"],
            ["Согласия", "/reset/legal"],
            ["Питание", "/reset/nutrition"],
          ].map(([label, path]) => (
            <button
              key={path}
              type="button"
              className="rounded-lg bg-stone-200 px-3 py-1.5 text-xs"
              onClick={() =>
                run(() => adminUserAction(initData || null, userId, path, "POST"))
              }
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-red-200 bg-red-50/50 p-4 text-sm space-y-3">
        <h2 className="font-semibold text-red-950">Опасные действия</h2>
        {!card.is_blocked ? (
          <>
            <input
              type="text"
              placeholder="Причина блокировки (необязательно)"
              value={blockReason}
              onChange={(e) => setBlockReason(e.target.value)}
              className="w-full rounded border border-stone-300 px-2 py-1.5 text-sm"
            />
            <AdminConfirmDialog
              danger
              triggerLabel="Заблокировать"
              title={`Заблокировать ${card.display_name}?`}
              description="Пользователь не сможет пользоваться Mini App и ботом."
              confirmLabel="Заблокировать"
              onConfirm={() =>
                run(() =>
                  adminUserAction(initData || null, userId, "/block", "POST", {
                    reason: blockReason || undefined,
                  }),
                )
              }
            />
          </>
        ) : (
          <button
            type="button"
            className="rounded-lg bg-stone-800 px-3 py-2 text-xs text-white"
            onClick={() => run(() => adminUserAction(initData || null, userId, "/unblock"))}
          >
            Разблокировать
          </button>
        )}
        {card.is_deleted ? (
          <button
            type="button"
            className="rounded-lg bg-amber-700 px-3 py-2 text-xs text-white"
            onClick={() => run(() => adminUserAction(initData || null, userId, "/restore", "POST"))}
          >
            Восстановить из архива
          </button>
        ) : (
          <AdminConfirmDialog
            danger
            triggerLabel="В архив"
            title={`Архивировать ${card.display_name}?`}
            description="Аккаунт скроется из списка. Это не блокировка — пользователь не сможет войти, пока не восстановите."
            confirmLabel="В архив"
            onConfirm={() =>
              run(() => adminUserAction(initData || null, userId, "", "DELETE"))
            }
          />
        )}
        <AdminConfirmDialog
          danger
          triggerLabel="Очистить данные"
          title={`Очистить данные ${card.display_name}?`}
          description="Меню, покупки, запасы и настройки будут сброшены. Telegram-аккаунт останется."
          confirmLabel="Очистить"
          onConfirm={() =>
            run(() => adminUserAction(initData || null, userId, "/clear-data", "POST"))
          }
        />
        <AdminConfirmDialog
          danger
          triggerLabel="Сбросить как нового"
          title={`Сбросить ${card.display_name} как нового?`}
          description="Удалит аккаунт и все данные. При следующем входе в Telegram создастся новый пользователь с 7 днями стартового доступа."
          confirmLabel="Сбросить"
          onConfirm={() =>
            run(() => adminUserAction(initData || null, userId, "/reset-as-new", "POST"))
          }
        />
        <AdminConfirmDialog
          danger
          triggerLabel="Удалить навсегда"
          title={`Удалить ${card.display_name} навсегда?`}
          description='Введите DELETE в поле подтверждения на следующем шаге. Действие необратимо.'
          confirmLabel="Далее"
          onConfirm={() => {
            const typed = window.prompt('Введите DELETE для подтверждения');
            if (typed !== "DELETE") {
              setError("Подтверждение не совпало");
              return;
            }
            void run(() =>
              adminUserAction(initData || null, userId, "/hard-delete", "POST", {
                confirmation: "DELETE",
              }),
            );
          }}
        />
      </section>
    </div>
  );
}
