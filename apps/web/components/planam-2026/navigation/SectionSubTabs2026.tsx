"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/planam/cn";
import {
  getActiveTabId2026,
  getSubTabsForTab2026,
  isSubTabActive2026,
} from "@/lib/navigation/nav-config-2026";

export function SectionSubTabs2026() {
  const pathname = usePathname();
  const tabId = getActiveTabId2026(pathname);

  if (!tabId || tabId === "account") {
    return null;
  }

  const subTabs = getSubTabsForTab2026(tabId).filter(
    (t) => t.href !== "/" && t.href !== "/home",
  );

  if (subTabs.length < 2) {
    return null;
  }

  return (
    <div className="border-b border-pa-border bg-pa-surface px-4 py-2">
      <div className="mx-auto flex max-w-lg gap-2 overflow-x-auto">
        {subTabs.map((sub) => {
          const active = isSubTabActive2026(pathname, sub);
          return (
            <Link
              key={sub.href}
              href={sub.href}
              className={cn(
                "shrink-0 rounded-pill px-3 py-1.5 pa26-micro font-semibold transition",
                active
                  ? "bg-sage-500 text-white dark:bg-sage-400"
                  : "bg-sage-50 text-sage-700 dark:bg-sage-700/30 dark:text-sage-300",
              )}
              aria-current={active ? "page" : undefined}
            >
              {sub.label}
              {sub.planned ? " · скоро" : ""}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
