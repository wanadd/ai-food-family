"use client";

import type { ReactNode } from "react";

import {
  ScreenBackNav,
  type ScreenBackConfig,
} from "@/components/layout/ScreenBackNav";

type ScreenLayoutProps = {
  title: string;
  subtitle?: string;
  back?: ScreenBackConfig;
  children: ReactNode;
  footer?: ReactNode;
  headerExtra?: ReactNode;
  contentClassName?: string;
};

export function ScreenLayout({
  title,
  subtitle,
  back,
  children,
  footer,
  headerExtra,
  contentClassName = "",
}: ScreenLayoutProps) {
  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-100 bg-white px-4 pb-3 pt-7 sm:px-5">
        <div className="mx-auto max-w-lg">
          {back ? <ScreenBackNav back={back} className="mb-2" /> : null}
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="text-2xl font-bold text-stone-900">{title}</h1>
              {subtitle ? (
                <p className="mt-1 text-sm text-stone-500">{subtitle}</p>
              ) : null}
            </div>
            {headerExtra}
          </div>
        </div>
      </header>

      <main
        className={`mx-auto max-w-lg px-4 py-4 sm:px-5 ${
          footer ? "pb-[calc(8.5rem+env(safe-area-inset-bottom,0px))]" : ""
        } ${contentClassName}`}
      >
        {children}
      </main>

      {footer}
    </div>
  );
}
