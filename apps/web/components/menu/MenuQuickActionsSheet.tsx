"use client";

import Link from "next/link";

import { Sheet } from "@/components/ui/Sheet";
import { QUICK_ACTIONS, type QuickActionMeta } from "@/lib/menu/quick-actions";

type MenuQuickActionsSheetProps = {
  open: boolean;
  onClose: () => void;
  onPick: (action: QuickActionMeta) => void;
  busy?: boolean;
};

/**
 * Лист «Настроить меню» (ONE SCREEN UX): быстрые действия над активным планом
 * вынесены с первого экрана сюда. ПланАм подстроит меню и список покупок под
 * выбранную опцию. Параметры меню — отдельным подэкраном.
 */
export function MenuQuickActionsSheet({
  open,
  onClose,
  onPick,
  busy = false,
}: MenuQuickActionsSheetProps) {
  return (
    <Sheet open={open} title="Настроить меню" onClose={onClose}>
      <p className="mb-3 text-sm text-graphite-500">
        Это предложения — выбор за вами. Меню и список покупок подстроятся.
      </p>
      <div className="grid grid-cols-2 gap-2">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.id}
            type="button"
            disabled={busy}
            onClick={() => onPick(action)}
            className="pa-card min-h-[56px] px-3 py-2.5 text-left text-sm font-semibold text-graphite-900 disabled:opacity-50"
          >
            {action.label}
          </button>
        ))}
      </div>
      <Link
        href="/menu/settings"
        className="mt-4 block text-center text-sm font-semibold text-sage-700"
      >
        Параметры меню →
      </Link>
    </Sheet>
  );
}
