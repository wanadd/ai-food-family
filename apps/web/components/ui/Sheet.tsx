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
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />
      <div className="relative max-h-[85vh] overflow-y-auto rounded-t-2xl bg-white px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-4 shadow-xl">
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-stone-200" />
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-bold text-stone-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-sm font-semibold text-stone-500 hover:bg-stone-100"
          >
            Закрыть
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
