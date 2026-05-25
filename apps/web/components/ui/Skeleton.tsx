import type { ReactNode } from "react";

/**
 * Structural skeleton primitives used while a tab is loading data.
 *
 * Design goals:
 *   - the user sees the page chrome immediately (header, bottom nav,
 *     mode banner) so the app does not feel like it froze;
 *   - the skeleton shape matches the upcoming content so the layout
 *     does not jump when real data lands;
 *   - no spinning indicator — only soft pulsing rectangles.
 *
 * Use these via the higher-level helpers below (SkeletonCard /
 * SkeletonList) when you just need a quick 2-3 cards placeholder.
 */

type BoxProps = {
  className?: string;
};

export function SkeletonBox({ className = "" }: BoxProps) {
  return (
    <div
      className={`animate-pulse rounded-md bg-stone-100 ${className}`}
      aria-hidden
    />
  );
}

type SkeletonLineProps = {
  className?: string;
  /** Tailwind width class like ``"w-1/2"`` or ``"w-32"``. */
  width?: string;
};

export function SkeletonLine({
  className = "",
  width = "w-full",
}: SkeletonLineProps) {
  return <SkeletonBox className={`h-3 ${width} ${className}`} />;
}

type SkeletonCardProps = {
  /** Optional title placeholder width (default ``"w-1/3"``). */
  titleWidth?: string;
  /** Number of body lines. */
  lines?: number;
  /** Show a CTA-shaped placeholder at the bottom. */
  withButton?: boolean;
  /** Extra class names for the outer card. */
  className?: string;
  children?: ReactNode;
};

/**
 * A single card-shaped placeholder: title, a few body lines, and an
 * optional button strip. Matches the visual weight of most planned
 * sections (one main idea + a CTA).
 */
export function SkeletonCard({
  titleWidth = "w-1/3",
  lines = 3,
  withButton = false,
  className = "",
  children,
}: SkeletonCardProps) {
  return (
    <section
      className={`rounded-2xl border border-stone-100 bg-white p-5 ${className}`}
      aria-busy="true"
      aria-live="polite"
    >
      <SkeletonLine width={titleWidth} className="h-4" />
      <div className="mt-4 space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <SkeletonLine
            key={i}
            width={i === lines - 1 ? "w-2/3" : "w-full"}
          />
        ))}
      </div>
      {withButton ? (
        <div className="mt-5">
          <SkeletonBox className="h-10 w-40 rounded-full" />
        </div>
      ) : null}
      {children}
    </section>
  );
}

type SkeletonListProps = {
  /** Number of card placeholders to render. */
  count?: number;
  /** Optional className for the wrapper. */
  className?: string;
};

export function SkeletonList({ count = 3, className = "" }: SkeletonListProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard
          key={i}
          titleWidth={i === 0 ? "w-1/3" : "w-1/4"}
          lines={i === 0 ? 3 : 2}
        />
      ))}
    </div>
  );
}
