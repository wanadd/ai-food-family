"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NavIcon2026 } from "@/components/planam-2026/navigation/NavIcon2026";
import { cn } from "@/lib/planam/cn";
import {
  NAV_TABS_2026,
  getActiveTabId2026,
  isBottomNavHidden2026,
} from "@/lib/navigation/nav-config-2026";

export function BottomNavigation2026() {
  const pathname = usePathname();

  if (isBottomNavHidden2026(pathname)) {
    return null;
  }

  const activeId = getActiveTabId2026(pathname);

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-pa-border bg-pa-surface/95 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5 backdrop-blur-md"
      aria-label="Основная навигация"
    >
      <div className="mx-auto flex max-w-lg items-end justify-between gap-0.5 px-1 max-[359px]:gap-0 max-[359px]:px-0.5">
        {NAV_TABS_2026.map((item) => {
          const isActive = activeId === item.id;

          if (item.isCenter) {
            return (
              <Link
                key={item.id}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                aria-label={item.label}
                className={cn(
                  "flex min-w-0 flex-1 flex-col items-center px-1 pb-1 pt-0.5",
                  isActive ? "text-sage-700 dark:text-sage-300" : "text-sage-600",
                )}
              >
                <span
                  className={cn(
                    "flex h-11 w-11 items-center justify-center rounded-full text-xl shadow-sm ring-1 transition",
                    isActive
                      ? "bg-sage-500 text-white ring-sage-500 shadow-sage-200/80 dark:bg-sage-400 dark:ring-sage-400"
                      : "bg-sage-50 text-sage-700 ring-sage-200 dark:bg-pa-elevated dark:text-sage-300 dark:ring-sage-700/50",
                  )}
                  aria-hidden
                >
                  <NavIcon2026 id={item.icon} className="size-5" />
                </span>
                <span className="pa26-micro mt-1 font-bold leading-tight">{item.label}</span>
              </Link>
            );
          }

          return (
            <Link
              key={item.id}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex min-w-0 flex-1 flex-col items-center rounded-control px-1 py-2 text-center transition max-[359px]:px-0.5",
                isActive
                  ? "bg-sage-50 text-sage-800 dark:bg-pa-elevated/40 dark:text-sage-300"
                  : "text-pa-muted hover:bg-sage-50/80 dark:hover:bg-pa-elevated/50 dark:hover:text-pa-foreground",
              )}
            >
              <NavIcon2026
                id={item.icon}
                className="size-5 max-[359px]:size-[18px]"
              />
              <span className="pa26-micro mt-1 font-semibold leading-tight">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
