"use client";

import { useTelegram } from "@/components/TelegramProvider";
import { isClientDevMode } from "@/lib/dev-auth";

export function TelegramAuthPanel() {
  const {
    isTelegram,
    isDevMode,
    platform,
    colorScheme,
    user,
    isNewUser,
    isAuthenticating,
    authError,
    retryAuth,
  } = useTelegram();

  if (!isTelegram && !isDevMode) {
    return (
      <p className="text-sm text-slate-600">
        {isClientDevMode()
          ? "Не удалось войти в dev-режиме. Проверьте, что API запущен с ENVIRONMENT=development."
          : "Откройте приложение через Telegram Mini App."}
      </p>
    );
  }

  if (isAuthenticating) {
    return <p className="text-sm text-slate-500">Авторизация через Telegram…</p>;
  }

  if (authError) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-red-600">{authError}</p>
        <button
          type="button"
          onClick={retryAuth}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        >
          Повторить
        </button>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const displayName =
    [user.first_name, user.last_name].filter(Boolean).join(" ") ||
    user.username ||
    `User ${user.telegram_id}`;

  return (
    <div className="space-y-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-emerald-900">Авторизация</span>
        <span className="rounded-full bg-emerald-200 px-2.5 py-0.5 text-xs font-semibold text-emerald-900">
          OK
        </span>
      </div>
      <div className="space-y-1 text-sm text-emerald-950">
        <p className="font-semibold">{displayName}</p>
        {user.username ? <p>@{user.username}</p> : null}
        <p>Telegram ID: {user.telegram_id}</p>
        <p>User ID в БД: {user.id}</p>
        <p>
          Статус: {isNewUser ? "новый пользователь создан" : "существующий пользователь"}
        </p>
        <p className="text-emerald-800">
          Платформа: {platform}, тема: {colorScheme}
        </p>
      </div>
    </div>
  );
}
