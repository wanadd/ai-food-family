"use client";

import { expiryLabel, expiryTone } from "@/lib/pantry/labels";
import type { PantryItem } from "@/lib/pantry/types";

const TONE_STYLES = {
  danger: "border-red-200 bg-red-50 text-red-800",
  warning: "border-warm/30 bg-warm/10 text-graphite-900",
  ok: "border-sage-200 bg-sage-50 text-sage-700",
};

type PantryItemCardProps = {
  item: PantryItem;
  onEdit: () => void;
  onDelete: () => void;
};

export function PantryItemCard({ item, onEdit, onDelete }: PantryItemCardProps) {
  const tone = expiryTone(item.days_until_expiry, item.is_expired);

  return (
    <article
      className={`pa-card p-4 ${
        item.is_expired ? "opacity-80" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3
            className={`font-semibold ${
              item.is_expired ? "text-graphite-400 line-through" : "text-graphite-900"
            }`}
          >
            {item.name}
          </h3>
          <p className="mt-1 text-sm text-graphite-500">{item.quantity}</p>
          <span
            className={`mt-3 inline-block rounded-pill border px-2.5 py-1 text-xs font-semibold ${TONE_STYLES[tone]}`}
          >
            {expiryLabel(item.days_until_expiry, item.is_expired)} · до{" "}
            {item.expires_at}
          </span>
          {item.added_by_name ? (
            <p className="mt-2 text-xs text-graphite-400">
              Добавил(а): {item.added_by_name}
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col gap-2">
          <button
            type="button"
            onClick={onEdit}
            className="pa-btn-ghost px-3 py-1.5 text-xs"
          >
            Изменить
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded-control border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50"
          >
            Удалить
          </button>
        </div>
      </div>
    </article>
  );
}
