"use client";

import type { ReactNode } from "react";

type SheetProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
};

export function Sheet({ open, title, onClose, children }: SheetProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end">
      <button
        type="button"
        aria-label="Закрыть"
        className="absolute inset-0 bg-graphite-900/40"
        onClick={onClose}
      />
      <div className="relative max-h-[85vh] overflow-y-auto rounded-t-card bg-cream-surface px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-4 shadow-lift">
        <div className="mx-auto mb-3 h-1 w-10 rounded-pill bg-cream-border" />
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-bold text-graphite-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-control px-2 py-1 text-sm font-semibold text-graphite-500 hover:bg-cream-deep"
          >
            Закрыть
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
