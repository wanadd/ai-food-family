"use client";

import type { ReactNode } from "react";

import { BOTTOM_NAV_OFFSET } from "@/lib/layout/constants";

type StickyBottomBarProps = {
  children: ReactNode;
};

/** Primary actions — fixed above bottom navigation. */
export function StickyBottomBar({ children }: StickyBottomBarProps) {
  return (
    <div
      className="fixed left-0 right-0 z-50 border-t border-cream-border bg-cream-surface/95 px-4 py-3 backdrop-blur-md"
      style={{ bottom: BOTTOM_NAV_OFFSET }}
    >
      <div className="mx-auto max-w-lg">{children}</div>
    </div>
  );
}
