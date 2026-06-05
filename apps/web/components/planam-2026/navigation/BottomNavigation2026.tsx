"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NavIcon2026 } from "@/components/planam-2026/navigation/NavIcon2026";
import { cn } from "@/lib/planam/cn";
import {
  NAV_TABS_2026,
  getActiveTabId2026,
  isNavHidden2026,
} from "@/lib/navigation/nav-config-2026";

export function BottomNavigation2026() {
  const pathname = usePathname();

  if (isNavHidden2026(pathname)) {
    return null;
  }

  const activeId = getActiveTabId2026(pathname);

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-pa-border bg-pa-surface/95 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5 backdrop-blur-md"
      aria-label="Основная навигация"
    >
      <div className="mx-auto flex max-w-lg items-end justify-between gap-0.5 px-1">
        {NAV_TABS_2026.map((item) => {
          const isActive = activeId === item.id;

          return (
            <Link
              key={item.id}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex min-w-0 flex-1 flex-col items-center rounded-control px-1 py-2 text-center transition",
                isActive
                  ? "bg-sage-50 text-sage-800 dark:bg-pa-elevated/40 dark:text-sage-300"
                  : "text-pa-muted hover:bg-sage-50/80 dark:hover:bg-pa-elevated/50 dark:hover:text-pa-foreground",
              )}
            >
              <NavIcon2026 id={item.icon} className="size-5" />
              <span className="pa26-micro mt-1 font-semibold">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
