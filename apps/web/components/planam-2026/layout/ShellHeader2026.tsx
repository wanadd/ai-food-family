"use client";

import { usePathname } from "next/navigation";

import { ScreenBack2026 } from "@/components/planam-2026/navigation/ScreenBack2026";
import {
  getScreenTitle2026,
  isImmersiveRecipeDetailPath,
  isNavHidden2026,
} from "@/lib/navigation/nav-config-2026";

export function ShellHeader2026() {
  const pathname = usePathname();

  if (
    isNavHidden2026(pathname) ||
    pathname === "/" ||
    pathname === "/wellness" ||
    isImmersiveRecipeDetailPath(pathname)
  ) {
    return null;
  }

  const title = getScreenTitle2026(pathname);

  return (
    <header className="sticky top-0 z-30 border-b border-pa-border bg-pa-surface/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-lg items-center gap-2 px-4 py-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <ScreenBack2026 />
        <h1 className="pa26-page-title min-w-0 flex-1 truncate">{title}</h1>
      </div>
    </header>
  );
}
