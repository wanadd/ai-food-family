"use client";

import type { ReactNode } from "react";

import { BottomNav } from "@/components/layout/BottomNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="pb-[calc(5.5rem+env(safe-area-inset-bottom,0px))]">
        {children}
      </div>
      <BottomNav />
    </>
  );
}
