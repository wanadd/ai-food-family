"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { usePathname } from "next/navigation";

import { useScrollPastRatio } from "@/hooks/useScrollPastRatio";
import { FLOATING_BACK_OFFSET } from "@/lib/layout/constants";
import { isTabRoute } from "@/lib/navigation/return-to";

export type ScreenBackConfig = {
  label: string;
  href?: string;
  onClick?: () => void;
};

type ScreenBackNavProps = {
  back: ScreenBackConfig;
  className?: string;
  showFloating?: boolean;
};

export function ScreenBackNav({
  back,
  className = "",
  showFloating = false,
}: ScreenBackNavProps) {
  const router = useRouter();
  const pathname = usePathname();
  const scrolled = useScrollPastRatio(0.3);
  const allowFloating = showFloating && !isTabRoute(pathname);

  function goBack() {
    if (back.onClick) {
      back.onClick();
      return;
    }
    if (back.href) {
      router.push(back.href);
    }
  }

  const linkClass =
    "inline-flex items-center gap-1 text-sm font-semibold text-emerald-700 transition hover:text-emerald-800";

  const topNav =
    back.href && !back.onClick ? (
      <Link href={back.href} className={linkClass}>
        ← {back.label}
      </Link>
    ) : (
      <button type="button" onClick={goBack} className={linkClass}>
        ← {back.label}
      </button>
    );

  return (
    <>
      <div className={className}>{topNav}</div>
      {allowFloating && scrolled ? (
        <button
          type="button"
          onClick={goBack}
          className="fixed right-4 z-50 flex min-h-[44px] items-center gap-1.5 rounded-full border border-stone-200 bg-white/95 px-4 py-2.5 text-sm font-semibold text-emerald-800 shadow-lg backdrop-blur-md active:scale-[0.98]"
          style={{ bottom: FLOATING_BACK_OFFSET }}
          aria-label={`Вернуться: ${back.label}`}
        >
          <span aria-hidden>◀</span>
          {back.label}
        </button>
      ) : null}
    </>
  );
}
