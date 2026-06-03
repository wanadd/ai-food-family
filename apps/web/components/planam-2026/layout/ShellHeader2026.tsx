"use client";

import { usePathname } from "next/navigation";

import { getScreenTitle2026, isNavHidden2026 } from "@/lib/navigation/nav-config-2026";

export function ShellHeader2026() {
  const pathname = usePathname();

  if (
    isNavHidden2026(pathname) ||
    pathname === "/" ||
    pathname.startsWith("/plan/recipes/")
  ) {
    return null;
  }

  const title = getScreenTitle2026(pathname);

  return (
    <header className="sticky top-0 z-30 border-b border-pa-border bg-pa-surface/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-lg items-center px-4 py-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <h1 className="pa26-page-title truncate">{title}</h1>
      </div>
    </header>
  );
}
