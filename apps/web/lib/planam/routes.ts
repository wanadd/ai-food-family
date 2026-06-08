/**
 * PLANAM V1 — единый реестр актуальных маршрутов.
 *
 * Чтобы компоненты не хардкодили старые пути в разных местах, импортируйте
 * canonical-маршрут отсюда:
 *
 *   import { PLANAM_ROUTES, recipeDetailPath } from "@/lib/planam/routes";
 *   router.push(PLANAM_ROUTES.shopping);
 *
 * Источник истины по навигации (вкладки, redirect-карты, заголовки) —
 * `lib/navigation/nav-config-2026.ts` и `lib/navigation/route-migration-2026.ts`.
 * Этот файл — короткий, не-зависимый список canonical-путей + хелперы, на которые
 * можно ссылаться из тестов и компонентов без подтягивания тяжёлых модулей.
 *
 * @see reports/ui_2026_consolidation_audit.md
 * @see reports/planam_project_consolidation_audit.md
 */

/** Активные (canonical) маршруты PLANAM 2026. */
export const PLANAM_ROUTES = {
  home: "/",
  planToday: "/plan/today",
  planWeek: "/plan",
  planGenerate: "/plan/generate",
  planFavorites: "/plan/favorites",
  planCollections: "/plan/collections",
  recipes: "/plan/recipes",
  wellnessProgress: "/wellness/progress",
  shopping: "/shopping",
  pantry: "/home/pantry",
  /** Cook from pantry stock at home (not meal portions). */
  homeLeftovers: "/home/leftovers",
  /** Legacy alias — still served, prefer homeLeftovers in new UI. */
  leftovers: "/shopping/leftovers",
  wellness: "/wellness",
  wellnessChat: "/wellness/chat",
  notifications: "/account/notifications",
  account: "/account",
  accountNutrition: "/account/nutrition",
  accountFamily: "/account/family",
  accountSettings: "/account/settings",
  subscription: "/account/subscription",
  ams: "/account/ams",
  onboarding: "/onboarding",
} as const;

export type PlanamRouteKey = keyof typeof PLANAM_ROUTES;
export type PlanamRoute = (typeof PLANAM_ROUTES)[PlanamRouteKey];

/** Detail-маршрут рецепта (canonical 2026). */
export function recipeDetailPath(id: number | string): string {
  return `${PLANAM_ROUTES.recipes}/${id}`;
}

/** Маршрут оформления подписки. */
export function subscriptionCheckoutPath(): string {
  return `${PLANAM_ROUTES.subscription}/checkout`;
}

/**
 * Deprecated маршруты, которые сейчас работают только как redirect.
 * Новый код НЕ должен ссылаться на них напрямую — используйте PLANAM_ROUTES.
 * Список используется тестами и project health-аудитом.
 */
export const DEPRECATED_REDIRECT_ROUTES: readonly string[] = [
  "/home",
  "/menu",
  "/menu/current",
  "/menu/generate",
  "/menu/recipes",
  "/recipes",
  "/pantry",
  "/health",
  "/health/today",
  "/health/chat",
  "/health/care",
  "/nutritionist",
  "/nutritionist/chat",
  "/nutritionist/care",
  "/progress",
  "/profile",
  "/profile/nutrition",
  "/family",
  "/notifications",
  "/settings",
  "/subscription",
] as const;

/** Набор всех canonical href для проверок «ссылка ведёт на активный маршрут». */
export const ACTIVE_ROUTE_SET: ReadonlySet<string> = new Set(
  Object.values(PLANAM_ROUTES),
);

/** True, если путь — известный deprecated redirect. */
export function isDeprecatedRoute(pathname: string): boolean {
  return DEPRECATED_REDIRECT_ROUTES.includes(pathname);
}
