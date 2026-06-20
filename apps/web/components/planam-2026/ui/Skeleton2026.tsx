import { cn } from "@/lib/planam/cn";

export type Skeleton2026Variant = "rect" | "text" | "circle";

export type Skeleton2026Props = {
  variant?: Skeleton2026Variant;
  className?: string;
  /** Used for rect aspect ratio, e.g. "4/3" */
  aspectRatio?: string;
};

export function Skeleton2026({
  variant = "rect",
  className,
  aspectRatio,
}: Skeleton2026Props) {
  return (
    <div
      aria-hidden
      className={cn(
        "animate-pulse bg-cream-deep dark:bg-graphite-700/40",
        variant === "rect" && "rounded-card w-full",
        variant === "text" && "h-4 w-full max-w-[12rem] rounded-pill",
        variant === "circle" && "size-12 rounded-full",
        className,
      )}
      style={variant === "rect" && aspectRatio ? { aspectRatio } : undefined}
    />
  );
}
