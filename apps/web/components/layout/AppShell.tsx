"use client";

import type { ReactNode } from "react";

import { DevModeBanner } from "@/components/dev/DevModeBanner";
import { BottomNav } from "@/components/layout/BottomNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <DevModeBanner />
      <div className="pb-[calc(4.75rem+env(safe-area-inset-bottom,0px))]">
        {children}
      </div>
      <BottomNav />
    </>
  );
}
