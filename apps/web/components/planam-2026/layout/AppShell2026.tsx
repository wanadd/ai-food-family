"use client";

import type { ReactNode } from "react";

import { BottomNavigation2026 } from "@/components/planam-2026/navigation/BottomNavigation2026";
import { SectionSubTabs2026 } from "@/components/planam-2026/navigation/SectionSubTabs2026";
import { ShellHeader2026 } from "@/components/planam-2026/layout/ShellHeader2026";
import { BOTTOM_NAV_OFFSET_2026 } from "@/lib/planam/layout-constants-2026";

export function AppShell2026({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-pa-canvas text-pa-foreground">
      <ShellHeader2026 />
      <SectionSubTabs2026 />
      <div style={{ paddingBottom: BOTTOM_NAV_OFFSET_2026 }}>{children}</div>
      <BottomNavigation2026 />
    </div>
  );
}
