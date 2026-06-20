"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_TABS, getActiveTabId, isNavHidden } from "@/lib/navigation/nav-config";

export function BottomNavigation() {
  const pathname = usePathname();

  if (isNavHidden(pathname)) {
    return null;
  }

  const activeId = getActiveTabId(pathname);

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-stone-200/90 bg-white/95 px-1 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5 backdrop-blur-md"
      aria-label="Основная навигация"
    >
      <div className="mx-auto flex max-w-lg items-end justify-between gap-0.5">
        {NAV_TABS.map((item) => {
          const isActive = activeId === item.id;

          if (item.isCenter) {
            // ПланАм — центральная вкладка и AI-хаб: усиленный, но лёгкий
            // акцент (без тяжёлой floating-кнопки).
            return (
              <Link
                key={item.id}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`flex min-w-0 flex-1 flex-col items-center px-1 pb-1 pt-0.5 ${
                  isActive ? "text-emerald-700" : "text-emerald-600"
                }`}
              >
                <span
                  className={`flex h-11 w-11 items-center justify-center rounded-full text-xl shadow-sm ring-1 transition ${
                    isActive
                      ? "bg-emerald-600 text-white ring-emerald-600 shadow-emerald-200"
                      : "bg-emerald-50 text-emerald-700 ring-emerald-200"
                  }`}
                  aria-hidden
                >
                  {item.icon}
                </span>
                <span className="mt-1 text-[10px] font-bold leading-tight">
                  {item.label}
                </span>
              </Link>
            );
          }

          return (
            <Link
              key={item.id}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={`flex min-w-0 flex-1 flex-col items-center rounded-xl px-1 py-2 text-center transition ${
                isActive
                  ? "bg-emerald-50 text-emerald-800"
                  : "text-stone-500 hover:bg-stone-50"
              }`}
            >
              <span className="text-base leading-none" aria-hidden>
                {item.icon}
              </span>
              <span className="mt-1 text-[10px] font-semibold leading-tight">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
