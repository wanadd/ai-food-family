import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/planam/cn";

export type Card2026Elevation = "default" | "elevated";

export type Card2026Props = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  elevation?: Card2026Elevation;
  padding?: "none" | "md";
};

export function Card2026({
  children,
  elevation = "default",
  padding = "md",
  className,
  ...rest
}: Card2026Props) {
  return (
    <div
      className={cn(
        "rounded-card border border-pa-border bg-pa-surface",
        elevation === "default" && "shadow-soft dark:shadow-none",
        elevation === "elevated" && "bg-pa-elevated shadow-lift dark:shadow-none",
        padding === "md" && "p-4",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
