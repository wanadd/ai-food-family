"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/planam/cn";

export type BottomSheet2026Props = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
};

export function BottomSheet2026({
  open,
  title,
  onClose,
  children,
  footer,
}: BottomSheet2026Props) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end">
      <button
        type="button"
        aria-label="Закрыть"
        className="absolute inset-0 bg-graphite-900/40 dark:bg-black/60"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative flex max-h-[85vh] flex-col rounded-t-card border-t border-pa-border",
          "bg-pa-elevated shadow-lift",
        )}
      >
        <div className="px-5 pt-4">
          <div className="mx-auto mb-3 h-1 w-10 rounded-pill bg-pa-border" />
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="pa26-page-title">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="rounded-control px-2 py-1 text-[13px] font-semibold text-pa-muted hover:bg-sage-50 dark:hover:bg-white/5"
            >
              Закрыть
            </button>
          </div>
        </div>
        <div className="max-h-[60vh] overflow-y-auto px-5 pb-4">{children}</div>
        {footer ? (
          <div className="border-t border-pa-border px-5 py-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}
