"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { isBottomNavHidden2026 } from "@/lib/navigation/nav-config-2026";
import { BOTTOM_NAV_OFFSET } from "@/lib/layout/constants";

type StickyBottomBarProps = {
  children: ReactNode;
};

/** Primary actions — fixed above bottom navigation. */
export function StickyBottomBar({ children }: StickyBottomBarProps) {
  const pathname = usePathname();
  const bottomNavHidden = isBottomNavHidden2026(pathname);

  return (
    <div
      className="fixed left-0 right-0 z-50 border-t border-pa-border bg-pa-surface/95 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 backdrop-blur-md"
      style={{ bottom: bottomNavHidden ? 0 : BOTTOM_NAV_OFFSET }}
    >
      <div className="mx-auto max-w-lg">{children}</div>
    </div>
  );
}
