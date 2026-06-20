"use client";

import { SettingsScaffold } from "@/components/settings/SettingsScaffold";
import { HealthStatus } from "@/components/HealthStatus";
import { useTelegram } from "@/components/TelegramProvider";
import {
  formatAccountDisplayName,
  formatAccountUsernameLabel,
} from "@/lib/display/sanitize-label";
import { apiUrl } from "@/lib/api";

const BOT_USERNAME = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME;

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-stone-100 py-3 last:border-0">
      <dt className="text-xs font-semibold uppercase tracking-wide text-stone-400">
        {label}
      </dt>
      <dd className="mt-1 break-all text-sm font-medium text-stone-800">{value}</dd>
    </div>
  );
}

export default function SettingsAccountPage() {
  const { user, isTelegram, isAuthenticating } = useTelegram();

  const fullName = formatAccountDisplayName(
    user?.first_name,
    user?.last_name,
    user?.username,
  );

  return (
    <SettingsScaffold title="Аккаунт" subtitle="Данные Telegram и ПланАм">
      <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
        {!isTelegram || !user ? (
          <p className="text-sm text-stone-600">
            {isAuthenticating
              ? "Подключаем Telegram…"
              : "Войдите через Telegram Mini App"}
          </p>
        ) : (
          <dl>
            <InfoRow label="Имя" value={fullName} />
            <InfoRow
              label="Username"
              value={formatAccountUsernameLabel(user.username)}
            />
            <InfoRow
              label="Телефон"
              value={
                user.phone_number ??
                "Не подтверждён — отправьте контакт боту в /start"
              }
            />
            <InfoRow label="Telegram ID" value={String(user.telegram_id)} />
            <InfoRow label="ID в ПланАм" value={String(user.id)} />
          </dl>
        )}
      </section>

      {user && !user.phone_number && BOT_USERNAME ? (
        <section className="rounded-2xl border border-amber-100 bg-amber-50/80 p-4 text-sm text-amber-950">
          <p className="font-semibold">Подтвердите телефон</p>
          <p className="mt-1 text-amber-900/90">
            Откройте{" "}
            <a
              href={`https://t.me/${BOT_USERNAME}`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold underline"
            >
              @{BOT_USERNAME}
            </a>
            , нажмите «Старт» и отправьте номер телефона.
          </p>
        </section>
      ) : null}

      {process.env.NODE_ENV === "development" ? (
        <section className="rounded-2xl border border-dashed border-stone-200 bg-stone-100/80 p-4 text-xs text-stone-600">
          <p className="font-semibold text-stone-700">Для разработчиков</p>
          <p className="mt-1 break-all">API: {apiUrl}</p>
          <HealthStatus apiUrl={apiUrl} />
        </section>
      ) : null}
    </SettingsScaffold>
  );
}
