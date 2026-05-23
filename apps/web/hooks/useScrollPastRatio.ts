"use client";

import { useEffect, useState } from "react";

export function useScrollPastRatio(threshold = 0.3): boolean {
  const [past, setPast] = useState(false);

  useEffect(() => {
    function onScroll() {
      const el = document.documentElement;
      const max = el.scrollHeight - el.clientHeight;
      if (max <= 0) {
        setPast(false);
        return;
      }
      setPast(el.scrollTop / max >= threshold);
    }

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [threshold]);

  return past;
}
