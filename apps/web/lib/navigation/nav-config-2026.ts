/**
 * PLANAM 2026 — единый источник правды для навигации.
 * @see docs/PLANAM_UX_UI_2026_MASTER_SPEC.md §3
 * @see docs/SPRINT_1_COMPLETION_REPORT.md
 */

export type Nav2026TabId = "plan" | "shopping" | "planam" | "wellness" | "events";

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
  | "events"
  | "calendar-star"
  | "legal";

export type Nav2026Tab = {
  id: Nav2026TabId;
  href: string;
  label: string;
  icon: Nav2026IconId;
  matchPrefixes: string[];
  /** Центральная вкладка ПланАм (Sprint 1). */
  isCenter?: boolean;
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

/** Нижняя навигация: Меню · Покупки · ПланАм · Здоровье · События */
export const NAV_TABS_2026: Nav2026Tab[] = [
  {
    id: "plan",
    href: "/plan/today",
    label: "Меню",
    icon: "plan",
    matchPrefixes: ["/plan"],
  },
  {
    id: "shopping",
    href: "/shopping",
    label: "Покупки",
    icon: "shopping",
    matchPrefixes: ["/shopping", "/home/shopping"],
  },
  {
    id: "planam",
    href: "/",
    label: "ПланАм",
    icon: "home",
    matchPrefixes: ["/", "/home"],
    isCenter: true,
  },
  {
    id: "wellness",
    href: "/wellness",
    label: "Здоровье",
    icon: "wellness",
    matchPrefixes: ["/wellness"],
  },
  {
    id: "events",
    href: "/events",
    label: "События",
    icon: "events",
    matchPrefixes: ["/events"],
  },
];

/** Подраздел «План». */
export const PLAN_SUBTABS_2026: Nav2026SubTab[] = [
  { href: "/plan", label: "Неделя", icon: "plan" },
  { href: "/plan/today", label: "Сегодня", icon: "today" },
  { href: "/plan/recipes", label: "Рецепты", icon: "recipes" },
];

/** Подраздел «Дом» — доступ через главную, не через нижнюю навигацию. */
export const HOME_SUBTABS_2026: Nav2026SubTab[] = [
  { href: "/home/pantry", label: "Запасы", icon: "pantry" },
];

/** Подраздел «Забота» — единый scroll на /wellness; чат — кнопка на экране. */
export const WELLNESS_SUBTABS_2026: Nav2026SubTab[] = [
  { href: "/wellness", label: "Сегодня", icon: "wellness" },
];

/** Центр управления — Account Hub. */
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
    id: "theme",
    label: "Тема приложения",
    caption: "Светлая / Тёмная / Как в системе",
    href: "/account",
    icon: "theme",
    inline: "theme",
  },
  {
    id: "nutrition",
    label: "Питание",
    caption: "Цели и ограничения",
    href: "/account/nutrition",
    icon: "profile",
  },
  {
    id: "family",
    label: "Семья",
    caption: "Участники и роли",
    href: "/account/family",
    icon: "family",
  },
  {
    id: "subscription",
    label: "Подписка",
    caption: "Тариф и срок",
    href: "/account/subscription",
    icon: "subscription",
  },
  {
    id: "ams",
    label: "Амы",
    caption: "Баланс и история",
    href: "/account/ams",
    icon: "subscription",
  },
  {
    id: "notifications",
    label: "Уведомления",
    caption: "Напоминания и каналы",
    href: "/account/notifications",
    icon: "notifications",
  },
  {
    id: "settings",
    label: "Настройки",
    caption: "Аккаунт и приложение",
    href: "/account/settings",
    icon: "settings",
  },
];

/** Все зарегистрированные маршруты 2026 (заголовки экранов). */
export const ROUTES_2026: Nav2026RouteMeta[] = [
  { href: "/", title: "Дом", sectionId: "home" },
  { href: "/home", title: "Дом", sectionId: "home" },
  { href: "/shopping", title: "Список покупок", tabId: "shopping", sectionId: "shopping" },
  { href: "/home/shopping", title: "Список покупок", tabId: "shopping", sectionId: "shopping" },
  { href: "/home/pantry", title: "Запасы", sectionId: "pantry" },
  {
    href: "/home/leftovers",
    title: "Из того, что есть дома",
    sectionId: "leftovers",
  },
  { href: "/plan", title: "План питания", tabId: "plan", sectionId: "plan" },
  { href: "/plan/today", title: "Меню", tabId: "plan", sectionId: "today" },
  { href: "/plan/recipes", title: "Рецепты", tabId: "plan", sectionId: "recipes" },
  { href: "/wellness", title: "Здоровье", tabId: "wellness", sectionId: "wellness" },
  { href: "/wellness/chat", title: "AI помощник", sectionId: "wellness-chat" },
  { href: "/events", title: "События", tabId: "events", sectionId: "events" },
  { href: "/account", title: "Профиль", sectionId: "account" },
  {
    href: "/account/subscription",
    title: "Подписка",
    sectionId: "subscription",
  },
  { href: "/account/ams", title: "Амы", sectionId: "ams" },
  { href: "/account/family", title: "Семья", sectionId: "family" },
  {
    href: "/account/notifications",
    title: "Уведомления",
    sectionId: "notifications",
  },
  { href: "/account/settings", title: "Настройки", sectionId: "settings" },
  { href: "/account/nutrition", title: "Питание", sectionId: "nutrition" },
  { href: "/account/settings/account", title: "Аккаунт" },
  { href: "/account/settings/documents", title: "Документы" },
  {
    href: "/account/settings/delete-data",
    title: "Удалить данные",
  },
  { href: "/account/settings/support", title: "Поддержка" },
  { href: "/account/settings/about", title: "О приложении" },
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

export function isShellHeaderHidden2026(pathname: string): boolean {
  if (isImmersiveRecipeDetailPath(pathname)) {
    return true;
  }
  return (
    pathname === "/" ||
    pathname === "/wellness" ||
    pathname === "/account" ||
    pathname === "/plan/today" ||
    pathname === "/plan/recipes" ||
    pathname === "/events"
  );
}

/** Legacy fallback при выключенном UI 2026 (для guard на новых URL). */
export const LEGACY_FALLBACK_BY_2026_PATH: Record<string, string> = {
  "/": "/",
  "/home": "/",
  "/home/shopping": "/shopping",
  "/home/pantry": "/shopping/pantry",
  "/plan": "/menu",
  "/plan/today": "/menu/current",
  "/plan/generate": "/menu/generate",
  "/plan/recipes": "/menu/recipes",
  "/wellness": "/health",
  "/events": "/menu/event",
  "/account": "/profile",
  "/account/subscription": "/subscription",
  "/account/ams": "/subscription",
  "/account/subscription/checkout": "/subscription",
  "/account/family": "/family",
  "/account/notifications": "/notifications",
  "/account/settings": "/settings",
  "/account/nutrition": "/profile/nutrition",
  "/account/settings/account": "/settings/account",
  "/account/settings/documents": "/settings/documents",
  "/account/settings/delete-data": "/settings/delete-data",
  "/account/settings/support": "/settings/support",
  "/account/settings/about": "/settings/about",
};

export function getActiveTabId2026(pathname: string): Nav2026TabId | null {
  if (pathname === "/" || pathname === "/home") {
    return "planam";
  }
  if (
    pathname === "/home/shopping" ||
    pathname === "/shopping" ||
    pathname.startsWith("/shopping/")
  ) {
    return "shopping";
  }
  if (pathname === "/wellness" || pathname.startsWith("/wellness/")) {
    return "wellness";
  }
  if (pathname === "/events" || pathname.startsWith("/events/")) {
    return "events";
  }
  if (pathname === "/plan" || pathname.startsWith("/plan/")) {
    return "plan";
  }
  if (pathname === "/account" || pathname.startsWith("/account/")) {
    return null;
  }
  const accountLegacy = ACCOUNT_LEGACY_PREFIXES_2026.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
  if (accountLegacy) {
    return null;
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
    case "shopping":
    case "planam":
    case "wellness":
    case "events":
      return [];
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
