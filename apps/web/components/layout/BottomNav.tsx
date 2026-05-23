"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/nutritionist", label: "Нутрициолог", icon: "🥗", isHome: false },
  { href: "/menu", label: "Меню", icon: "🍽", isHome: false },
  { href: "/", label: "Главная", icon: "🏠", isHome: true },
  { href: "/shopping", label: "Покупки", icon: "🛒", isHome: false },
  { href: "/pantry", label: "Запасы", icon: "📦", isHome: false },
] as const;

const HIDDEN_PREFIXES = ["/onboarding", "/settings", "/subscription", "/profile"];

export function BottomNav() {
  const pathname = usePathname();

  if (HIDDEN_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return null;
  }

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-stone-200/90 bg-white/95 px-1 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5 backdrop-blur-md"
      aria-label="Основная навигация"
    >
      <div className="mx-auto flex max-w-lg items-end justify-between gap-0.5">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          if (item.isHome) {
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex min-w-0 flex-1 flex-col items-center px-1 pb-1 pt-0.5 ${
                  isActive ? "text-emerald-700" : "text-stone-500"
                }`}
              >
                <span
                  className={`flex h-11 w-11 items-center justify-center rounded-full text-xl shadow-sm transition ${
                    isActive
                      ? "bg-emerald-600 text-white shadow-emerald-200"
                      : "bg-stone-100"
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
              key={item.href}
              href={item.href}
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
