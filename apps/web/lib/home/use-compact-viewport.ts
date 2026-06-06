"use client";

import { useEffect, useState } from "react";

const COMPACT_HEIGHT_PX = 700;

/** True when viewport height < 700px (Sprint 1 compact Hero). */
export function useCompactViewport(): boolean {
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    const update = () => {
      setCompact(window.innerHeight < COMPACT_HEIGHT_PX);
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  return compact;
}
