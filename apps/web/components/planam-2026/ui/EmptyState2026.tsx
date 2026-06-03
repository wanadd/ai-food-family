import type { ReactNode } from "react";

import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { cn } from "@/lib/planam/cn";

export type EmptyState2026Props = {
  title: string;
  description?: string;
  icon?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
};

export function EmptyState2026({
  title,
  description,
  icon,
  actionLabel,
  onAction,
  className,
}: EmptyState2026Props) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3 px-6 py-10 text-center",
        className,
      )}
    >
      {icon ? (
        <div className="flex size-14 items-center justify-center rounded-card bg-sage-50 text-2xl dark:bg-sage-700/20">
          {icon}
        </div>
      ) : null}
      <h3 className="pa26-section-title">{title}</h3>
      {description ? (
        <p className="pa26-body max-w-[280px] text-pa-muted">{description}</p>
      ) : null}
      {actionLabel && onAction ? (
        <Button2026 variant="primary" onClick={onAction} className="mt-2">
          {actionLabel}
        </Button2026>
      ) : null}
    </div>
  );
}
