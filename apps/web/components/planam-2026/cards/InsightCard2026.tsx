import type { ReactNode } from "react";

import { cn } from "@/lib/planam/cn";

export type InsightCard2026Props = {
  children: ReactNode;
  emoji?: string;
  disclaimer?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
};

export function InsightCard2026({
  children,
  emoji,
  disclaimer,
  actionLabel,
  onAction,
  className,
}: InsightCard2026Props) {
  return (
    <div
      className={cn(
        "rounded-card bg-sage-50 p-4 dark:border dark:border-sage-200/30 dark:bg-sage-700/20",
        className,
      )}
    >
      <div className="flex gap-3">
        {emoji ? <span className="text-xl leading-none">{emoji}</span> : null}
        <div className="min-w-0 flex-1">
          <p className="pa26-body line-clamp-3">{children}</p>
          {actionLabel && onAction ? (
            <button
              type="button"
              onClick={onAction}
              className="mt-2 text-[13px] font-semibold text-sage-700 dark:text-sage-300"
            >
              {actionLabel}
            </button>
          ) : null}
          {disclaimer ? <p className="pa26-micro mt-2 text-pa-muted">{disclaimer}</p> : null}
        </div>
      </div>
    </div>
  );
}
