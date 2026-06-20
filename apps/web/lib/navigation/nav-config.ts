/**
 * Single source of truth for the app navigation (UX/UI Refinement V1).
 *
 * Bottom navigation (left → right):
 *   Меню · Покупки · ПланАм (центр, AI-хаб) · Здоровье · Профиль
 *
 * Внутренние вкладки (sub-tabs) описаны здесь, но монтируются в своих
 * разделах в Этапах 2–3 (через SegmentedTabs). В Этапе 1 они существуют как
 * скелет маршрутов с временными redirect().
 */

export type NavTabId = "menu" | "shopping" | "home" | "health" | "profile";

export type NavTab = {
  id: NavTabId;
  href: string;
  label: string;
  icon: string;
  /** Центральная вкладка (ПланАм) — главный AI-хаб, усиленный акцент. */
  isCenter?: boolean;
  /**
   * Префиксы маршрутов, активирующие вкладку. Учитывают старые маршруты,
   * которые ещё живы в Этапе 1 (например, /recipes, /pantry, /nutritionist).
   */
  matchPrefixes: string[];
};

export const NAV_TABS: NavTab[] = [
  {
    id: "menu",
    href: "/menu",
    label: "Меню",
    icon: "🍽",
    matchPrefixes: ["/menu", "/recipes"],
  },
  {
    id: "shopping",
    href: "/shopping",
    label: "Покупки",
    icon: "🛒",
    matchPrefixes: ["/shopping", "/pantry"],
  },
  {
    id: "home",
    href: "/",
    label: "ПланАм",
    icon: "✨",
    isCenter: true,
    matchPrefixes: ["/"],
  },
  {
    id: "health",
    href: "/health",
    label: "Здоровье",
    icon: "❤️",
    matchPrefixes: ["/health", "/nutritionist"],
  },
  {
    id: "profile",
    href: "/profile",
    label: "Профиль",
    icon: "👤",
    matchPrefixes: ["/profile"],
  },
];

export type SubTab = {
  href: string;
  label: string;
};

/** Внутренние вкладки раздела «Меню» (монтируются в Этапе 2). */
export const MENU_SUBTABS: SubTab[] = [
  { href: "/menu", label: "Моё меню" },
  { href: "/menu/recipes", label: "Рецепты" },
  { href: "/menu/favorites", label: "Избранное" },
  { href: "/menu/collections", label: "Коллекции" },
];

/**
 * Внутренние вкладки раздела «Покупки» (монтируются в Этапе 3).
 *
 * Покупки — будущий центр заказа продуктов. Здесь же в будущем появится
 * действие «Заказать продукты» (доставка). Доставка НЕ будет отдельной
 * нижней вкладкой и НЕ отдельным разделом — это часть Покупок.
 * Планируемая цепочка: Меню → список покупок → заказ → доставка → запасы.
 */
export const SHOPPING_SUBTABS: SubTab[] = [
  { href: "/shopping", label: "Покупки" },
  { href: "/shopping/pantry", label: "Запасы" },
  { href: "/shopping/leftovers", label: "Остатки" },
];

/** Маршруты без нижней навигации (системные / первый запуск). */
export const HIDDEN_NAV_PREFIXES = ["/onboarding", "/admin"];

/** Возвращает id активной вкладки для текущего пути. */
export function getActiveTabId(pathname: string): NavTabId | null {
  if (pathname === "/") {
    return "home";
  }
  for (const tab of NAV_TABS) {
    if (tab.id === "home") {
      continue;
    }
    const match = tab.matchPrefixes.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
    if (match) {
      return tab.id;
    }
  }
  return null;
}

/** Нужно ли скрывать нижнюю навигацию на этом маршруте. */
export function isNavHidden(pathname: string): boolean {
  return HIDDEN_NAV_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

/** Активна ли подвкладка (точное совпадение пути). */
export function isSubTabActive(pathname: string, subTab: SubTab): boolean {
  return pathname === subTab.href;
}
