"use client";

import { useState } from "react";

export function AdminConfirmDialog({
  title,
  description,
  confirmLabel = "Подтвердить",
  cancelLabel = "Отмена",
  danger = false,
  onConfirm,
  triggerLabel,
}: {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void | Promise<void>;
  triggerLabel: string;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`rounded-lg px-3 py-2 text-sm font-medium ${
          danger
            ? "bg-red-600 text-white"
            : "bg-stone-800 text-white"
        }`}
      >
        {triggerLabel}
      </button>
    );
  }

  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm">
      <p className="font-semibold text-red-950">{title}</p>
      <p className="mt-1 text-red-900/80">{description}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await onConfirm();
              setOpen(false);
            } finally {
              setBusy(false);
            }
          }}
          className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
        >
          {confirmLabel}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => setOpen(false)}
          className="rounded-lg border border-stone-300 bg-white px-3 py-1.5 text-xs text-stone-700"
        >
          {cancelLabel}
        </button>
      </div>
    </div>
  );
}
