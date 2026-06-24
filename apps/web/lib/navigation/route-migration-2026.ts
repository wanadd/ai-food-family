/**
 * Карта миграции legacy → PLANAM 2026.
 * Редиректы **не включены** по умолчанию.
 *
 * Включение: NEXT_PUBLIC_PLANAM_UI_2026=true
 *            NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true
 *
 * @see docs/PLANAM_UX_UI_2026_MASTER_SPEC.md — Grace redirects
 */

export type RouteMigrationEntry = {
  /** Legacy path (prefix or exact). */
  from: string;
  /** Target 2026 path. */
  to: string;
  /** Exact match only (default: prefix match). */
  exact?: boolean;
  note?: string;
};

export const ROUTE_MIGRATION_2026: RouteMigrationEntry[] = [
  // Exact /menu/* rules must precede the /menu prefix rule.
  { from: "/menu/current", to: "/plan/today", exact: true, note: "Today meals" },
  { from: "/menu/recipes", to: "/plan/recipes", exact: true },
  { from: "/menu/generate", to: "/plan/generate", exact: true, note: "Sprint 4+" },
  { from: "/menu/favorites", to: "/plan/favorites", exact: true, note: "Sprint 5+" },
  { from: "/menu/collections", to: "/plan/collections", exact: true, note: "Sprint 5+" },
  {
    from: "/menu/event",
    to: "/plan/generate",
    exact: true,
    note: "Event planner → plan generate",
  },
  {
    from: "/menu/settings",
    to: "/account/settings",
    exact: true,
    note: "Menu settings → account settings",
  },
  { from: "/menu", to: "/plan", note: "Menu hub → Plan week" },
  { from: "/recipes", to: "/plan/recipes", note: "Legacy recipes list" },
  { from: "/subscription", to: "/account/subscription", exact: true },
  { from: "/shopping", to: "/home/shopping", exact: true },
  { from: "/shopping/pantry", to: "/home/pantry", exact: true },
  { from: "/pantry", to: "/home/pantry", exact: true },
  { from: "/health", to: "/wellness", exact: true },
  { from: "/health/today", to: "/wellness", exact: true, note: "Merged scroll" },
  { from: "/health/chat", to: "/wellness/chat", exact: true, note: "Sprint 7+" },
  { from: "/nutritionist", to: "/wellness/chat", note: "Legacy nutritionist" },
  { from: "/progress", to: "/wellness/progress", exact: true, note: "Sprint 7+" },
  { from: "/profile", to: "/account", note: "Profile → account hub" },
  { from: "/family", to: "/account/family", exact: true },
  { from: "/notifications", to: "/account/notifications", exact: true },
  { from: "/settings", to: "/account/settings", note: "Settings → account settings" },
];

export function resolveMigrationTarget(pathname: string): string | null {
  for (const entry of ROUTE_MIGRATION_2026) {
    if (entry.exact) {
      if (pathname === entry.from) {
        return entry.to;
      }
      continue;
    }
    if (pathname === entry.from || pathname.startsWith(`${entry.from}/`)) {
      if (pathname === entry.from) {
        return entry.to;
      }
      const suffix = pathname.slice(entry.from.length);
      return `${entry.to}${suffix}`;
    }
  }
  return null;
}
