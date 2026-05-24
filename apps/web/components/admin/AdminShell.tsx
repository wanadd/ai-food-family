"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import { pingAdmin } from "@/lib/admin/api";

import { AdminSessionCapture } from "./AdminSessionCapture";

const NAV = [
  { href: "/admin", label: "Дашборд", exact: true },
  { href: "/admin/users", label: "Пользователи" },
  { href: "/admin/families", label: "Семьи" },
  { href: "/admin/subscriptions", label: "Подписки" },
  { href: "/admin/ams", label: "Амы" },
  { href: "/admin/openai", label: "OpenAI" },
  { href: "/admin/errors", label: "Ошибки" },
] as const;

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { initData } = useTelegram();
  const [checking, setChecking] = useState(true);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!initData) {
        setAllowed(false);
        setChecking(false);
        return;
      }
      const ok = await pingAdmin(initData);
      if (!cancelled) {
        setAllowed(ok);
        setChecking(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [initData]);

  if (checking) {
    return <PageLoading message="Проверяем доступ..." />;
  }

  if (!allowed) {
    return (
      <div className="mx-auto max-w-lg px-4 py-10 text-center">
        <AdminSessionCapture />
        <h1 className="text-lg font-bold text-stone-900">Нет доступа</h1>
        <p className="mt-2 text-sm text-stone-600">
          Откройте Telegram-бота, выполните команду /admin и подтвердите PIN. После
          этого нажмите кнопку открытия панели.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-100 pb-8">
      <AdminSessionCapture />
      <header className="sticky top-0 z-10 border-b border-stone-200 bg-white px-4 py-3">
        <h1 className="text-lg font-bold text-stone-900">ПланАм · панель</h1>
        <nav className="mt-2 flex gap-1 overflow-x-auto pb-1">
          {NAV.map((item) => {
            const active =
              "exact" in item && item.exact
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
                  active
                    ? "bg-stone-900 text-white"
                    : "bg-stone-200 text-stone-700"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main className="mx-auto max-w-lg px-4 py-4">{children}</main>
    </div>
  );
}
