"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/planam/cn";

export type Button2026Variant = "primary" | "secondary" | "ghost" | "danger";
export type Button2026Size = "default" | "wide" | "compact";

export type Button2026Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Button2026Variant;
  size?: Button2026Size;
  loading?: boolean;
  children: ReactNode;
};

const variantClasses: Record<Button2026Variant, string> = {
  primary:
    "bg-sage-500 text-white shadow-soft hover:bg-sage-600 active:scale-[0.99] disabled:opacity-40 dark:bg-sage-500 dark:hover:bg-sage-400 dark:shadow-none",
  secondary:
    "border border-sage-200 bg-pa-surface text-sage-700 hover:bg-sage-50 active:scale-[0.99] disabled:opacity-40 dark:border-pa-border dark:bg-pa-elevated dark:text-sage-300 dark:hover:bg-pa-elevated/40",
  ghost:
    "bg-transparent text-sage-700 hover:bg-sage-50 active:scale-[0.99] disabled:opacity-40 dark:text-sage-300 dark:hover:bg-pa-elevated/40",
  danger:
    "bg-transparent text-pa-error hover:bg-pa-error/10 active:scale-[0.99] disabled:opacity-40 border border-transparent hover:border-pa-error/30",
};

const sizeClasses: Record<Button2026Size, string> = {
  default: "min-h-[44px] px-4 text-[15px] font-semibold leading-[22px]",
  wide: "min-h-[44px] w-full px-6 text-[15px] font-semibold leading-[22px]",
  compact: "min-h-[36px] px-3 text-[13px] font-semibold leading-[18px]",
};

export function Button2026({
  variant = "primary",
  size = "default",
  loading = false,
  disabled,
  className,
  children,
  ...rest
}: Button2026Props) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center rounded-control transition",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...rest}
    >
      {loading ? "…" : children}
    </button>
  );
}
