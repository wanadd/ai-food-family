/**
 * PLANAM 2026 — единый источник правды для навигации.
 * @see docs/PLANAM_UX_UI_2026_MASTER_SPEC.md §3
 * @see docs/SPRINT_1_COMPLETION_REPORT.md
 */

export type Nav2026TabId = "plan" | "home" | "wellness" | "account";

export type Nav2026IconId =
  | "plan"
  | "home"
  | "wellness"
  | "account"
  | "shopping"
  | "pantry"
  | "recipes"
  | "today"
  | "settings"
  | "family"
  | "subscription"
  | "notifications"
  | "profile"
  | "theme"
  | "legal";

export type Nav2026Tab = {
  id: Nav2026TabId;
  href: string;
  label: string;
  icon: Nav2026IconId;
  /** Центральная вкладка «Дом». */
  isCenter?: boolean;
  matchPrefixes: string[];
};

export type Nav2026SubTab = {
  href: string;
  label: string;
  icon?: Nav2026IconId;
  /** Sprint 3+ — экран ещё не реализован. */
  planned?: boolean;
};

export type Nav2026RouteMeta = {
  href: string;
  title: string;
  tabId?: Nav2026TabId;
  sectionId?: string;
  planned?: boolean;
};

/** Нижняя навигация: План · Дом (центр) · Забота · Профиль */
export const NAV_TABS_2026: Nav2026Tab[] = [
  {
    id: "plan",
    href: "/plan",
    label: "План",
    icon: "plan",
    matchPrefixes: ["/plan"],
  },
  {
    id: "home",
    href: "/",
    label: "Дом",
    icon: "home",
    isCenter: true,
    matchPrefixes: ["/", "/home"],
  },
  {
    id: "wellness",
    href: "/wellness",
    label: "Забота",
    icon: "wellness",
    matchPrefixes: ["/wellness"],
  },
  {
    id: "account",
    href: "/account",
    label: "Профиль",
    icon: "account",
    matchPrefixes: ["/account"],
  },
];

/** Подраздел «План». */
export const PLAN_SUBTABS_2026: Nav2026SubTab[] = [
  { href: "/plan", label: "Неделя", icon: "plan" },
  { href: "/plan/today", label: "Сегодня", icon: "today" },
  { href: "/plan/recipes", label: "Рецепты", icon: "recipes" },
];

/** Подраздел «Дом». */
export const HOME_SUBTABS_2026: Nav2026SubTab[] = [
  { href: "/", label: "Сводка", icon: "home" },
  { href: "/home", label: "Дом", icon: "home" },
  { href: "/home/shopping", label: "Покупки", icon: "shopping" },
  { href: "/home/pantry", label: "Запасы", icon: "pantry" },
];

/** Подраздел «Забота» (будущие маршруты). */
export const WELLNESS_SUBTABS_2026: Nav2026SubTab[] = [
  { href: "/wellness", label: "Забота", icon: "wellness" },
  { href: "/wellness/chat", label: "Чат", icon: "wellness", planned: true },
  { href: "/wellness/progress", label: "Прогресс", icon: "wellness", planned: true },
];

/** Центр управления — Account Hub (Sprint 2: ссылки на legacy). */
export type AccountHubItem = {
  id: string;
  label: string;
  caption?: string;
  href: string;
  icon: Nav2026IconId;
  /** Встроенный блок (тема), без перехода. */
  inline?: "theme";
};

export const ACCOUNT_HUB_ITEMS_2026: AccountHubItem[] = [
  {
    id: "profile",
    label: "Профиль",
    caption: "Имя, телефон, аватар",
    href: "/profile",
    icon: "profile",
  },
  {
    id: "family",
    label: "Семья",
    caption: "Участники и роли",
    href: "/family",
    icon: "family",
  },
  {
    id: "subscription",
    label: "Подписка",
    caption: "Тариф и Амы",
    href: "/subscription",
    icon: "subscription",
  },
  {
    id: "notifications",
    label: "Уведомления",
    caption: "Напоминания и каналы",
    href: "/notifications",
    icon: "notifications",
  },
  {
    id: "settings",
    label: "Настройки",
    caption: "Аккаунт и приложение",
    href: "/settings",
    icon: "settings",
  },
  {
    id: "theme",
    label: "Оформление",
    caption: "Светлая · тёмная · система",
    href: "/account",
    icon: "theme",
    inline: "theme",
  },
];

/** Все зарегистрированные маршруты 2026 (заголовки экранов). */
export const ROUTES_2026: Nav2026RouteMeta[] = [
  { href: "/", title: "Дом", tabId: "home", sectionId: "home" },
  { href: "/home", title: "Дом", tabId: "home", sectionId: "home" },
  { href: "/home/shopping", title: "Список покупок", tabId: "home", sectionId: "shopping" },
  { href: "/home/pantry", title: "Запасы", tabId: "home", sectionId: "pantry" },
  { href: "/plan", title: "План на неделю", tabId: "plan", sectionId: "plan" },
  { href: "/plan/today", title: "Сегодня", tabId: "plan", sectionId: "today" },
  { href: "/plan/recipes", title: "Рецепты", tabId: "plan", sectionId: "recipes" },
  { href: "/wellness", title: "Забота", tabId: "wellness", sectionId: "wellness" },
  { href: "/account", title: "Профиль", tabId: "account", sectionId: "account" },
];

/** Legacy маршруты, активирующие вкладку «Профиль». */
export const ACCOUNT_LEGACY_PREFIXES_2026 = [
  "/profile",
  "/family",
  "/subscription",
  "/notifications",
  "/settings",
];

/** Маршруты без нижней навигации. */
export const HIDDEN_NAV_PREFIXES_2026 = ["/onboarding", "/admin", "/dev"];

/** Immersive recipe detail — full-bleed hero. */
export function isImmersiveRecipeDetailPath(pathname: string): boolean {
  return /^\/plan\/recipes\/\d+/.test(pathname);
}

/** Legacy fallback при выключенном UI 2026 (для guard на новых URL). */
export const LEGACY_FALLBACK_BY_2026_PATH: Record<string, string> = {
  "/": "/",
  "/home": "/",
  "/home/shopping": "/shopping",
  "/home/pantry": "/shopping/pantry",
  "/plan": "/menu",
  "/plan/today": "/menu/current",
  "/plan/recipes": "/menu/recipes",
  "/wellness": "/health",
  "/account": "/profile",
};

export function getActiveTabId2026(pathname: string): Nav2026TabId | null {
  if (pathname === "/") {
    return "home";
  }
  if (pathname === "/home" || pathname.startsWith("/home/")) {
    return "home";
  }
  if (pathname === "/plan" || pathname.startsWith("/plan/")) {
    return "plan";
  }
  if (pathname === "/wellness" || pathname.startsWith("/wellness/")) {
    return "wellness";
  }
  if (pathname === "/account" || pathname.startsWith("/account/")) {
    return "account";
  }
  const accountLegacy = ACCOUNT_LEGACY_PREFIXES_2026.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
  if (accountLegacy) {
    return "account";
  }
  return null;
}

export function isNavHidden2026(pathname: string): boolean {
  return HIDDEN_NAV_PREFIXES_2026.some((prefix) => pathname.startsWith(prefix));
}

export function getRouteMeta2026(pathname: string): Nav2026RouteMeta | null {
  const exact = ROUTES_2026.find((r) => r.href === pathname);
  if (exact) {
    return exact;
  }
  const byPrefix = [...ROUTES_2026]
    .filter((r) => r.href !== "/" && pathname.startsWith(`${r.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0];
  return byPrefix ?? null;
}

const LEGACY_SCREEN_TITLES: Record<string, string> = {
  "/profile": "Профиль",
  "/family": "Семья",
  "/subscription": "Подписка",
  "/notifications": "Уведомления",
  "/settings": "Настройки",
};

export function getScreenTitle2026(pathname: string): string {
  if (/^\/plan\/recipes\/\d+/.test(pathname)) {
    return "Рецепт";
  }
  const meta = getRouteMeta2026(pathname);
  if (meta) {
    return meta.title;
  }
  for (const [prefix, title] of Object.entries(LEGACY_SCREEN_TITLES)) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      return title;
    }
  }
  return "ПланАм";
}

export function getSubTabsForTab2026(tabId: Nav2026TabId): Nav2026SubTab[] {
  switch (tabId) {
    case "plan":
      return PLAN_SUBTABS_2026;
    case "home":
      return HOME_SUBTABS_2026;
    case "wellness":
      return WELLNESS_SUBTABS_2026;
    default:
      return [];
  }
}

export function isSubTabActive2026(pathname: string, subTab: Nav2026SubTab): boolean {
  if (subTab.href === "/") {
    return pathname === "/" || pathname === "/home";
  }
  return pathname === subTab.href;
}
