"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { BottomNavigation2026 } from "@/components/planam-2026/navigation/BottomNavigation2026";
import { SectionSubTabs2026 } from "@/components/planam-2026/navigation/SectionSubTabs2026";
import { TelegramBackBridge2026 } from "@/components/planam-2026/navigation/TelegramBackBridge2026";
import { ShellHeader2026 } from "@/components/planam-2026/layout/ShellHeader2026";
import { isBottomNavHidden2026 } from "@/lib/navigation/nav-config-2026";
import { BOTTOM_NAV_OFFSET_2026 } from "@/lib/planam/layout-constants-2026";

export function AppShell2026({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const bottomNavHidden = isBottomNavHidden2026(pathname);

  return (
    <div className="flex min-h-dvh flex-col bg-pa-canvas text-pa-foreground">
      <TelegramBackBridge2026 />
      <ShellHeader2026 />
      <SectionSubTabs2026 />
      <main
        className="min-h-0 flex-1"
        style={{ paddingBottom: bottomNavHidden ? 0 : BOTTOM_NAV_OFFSET_2026 }}
      >
        {children}
      </main>
      <BottomNavigation2026 />
    </div>
  );
}
