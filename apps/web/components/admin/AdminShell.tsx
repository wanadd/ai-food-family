"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { PageLoading } from "@/components/ui/PageLoading";
import { useTelegram } from "@/components/TelegramProvider";
import { exchangeAdminSession, fetchAdminOverview } from "@/lib/admin/v2-api";
import { getAdminSessionToken } from "@/lib/admin/session";

const NAV = [
  { href: "/admin", label: "Дашборд", exact: true },
  { href: "/admin/analytics", label: "Аналитика" },
] as const;

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { initData, isAuthenticating } = useTelegram();
  const [checking, setChecking] = useState(true);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const token = getAdminSessionToken();

    const finish = (ok: boolean) => {
      if (!cancelled) {
        setAllowed(ok);
        setChecking(false);
      }
    };

    const authorize = async () => {
      try {
        if (!token) {
          if (!initData) return finish(false);
          await exchangeAdminSession(initData);
        }
        await fetchAdminOverview();
        finish(true);
      } catch {
        finish(false);
      }
    };

    if (token || initData) authorize();

    if (isAuthenticating) {
      setChecking(true);
      return () => {
        cancelled = true;
      };
    }

    if (!token && !initData) finish(false);

    return () => {
      cancelled = true;
    };
  }, [initData, isAuthenticating]);

  if (checking) {
    return <PageLoading message="Проверяем доступ..." />;
  }

  if (!allowed) {
    return (
      <div className="mx-auto max-w-lg px-4 py-10 text-center">
        <h1 className="text-lg font-bold text-stone-900">Нет доступа</h1>
        <p className="mt-2 text-sm text-stone-600">
          Откройте Telegram-бота, выполните команду /admin и подтвердите PIN.
        </p>
      </div>
    );
  }

  const isV2AdminPath = pathname === "/admin" || pathname === "/admin/analytics";
  if (!isV2AdminPath) {
    return (
      <div className="mx-auto max-w-lg px-4 py-10 text-center">
        <h1 className="text-lg font-bold text-stone-900">Раздел ещё не перенесён</h1>
        <p className="mt-2 text-sm text-stone-600">
          Этот legacy-раздел отключён до появления соответствующего V2 read model.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-100 pb-8">
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
      <main className="mx-auto max-w-5xl px-4 py-4">{children}</main>
    </div>
  );
}
