/** Back navigation for nested UI 2026 screens (Telegram + browser). */

const MAIN_TAB_PATHS = new Set([
  "/",
  "/plan/today",
  "/home/shopping",
  "/account",
]);

const RECIPE_DETAIL = /^\/plan\/recipes\/\d+/;

export function isMainTabPath2026(pathname: string): boolean {
  if (MAIN_TAB_PATHS.has(pathname)) {
    return true;
  }
  if (pathname === "/shopping") {
    return true;
  }
  return false;
}

export function shouldShowBack2026(pathname: string): boolean {
  if (isMainTabPath2026(pathname)) {
    return false;
  }
  if (pathname.startsWith("/onboarding") || pathname.startsWith("/admin")) {
    return false;
  }
  return true;
}

export function getBackFallback2026(pathname: string): string {
  if (RECIPE_DETAIL.test(pathname)) {
    return "/plan/recipes";
  }
  if (pathname.startsWith("/plan/")) {
    return "/plan/today";
  }
  if (pathname.startsWith("/wellness")) {
    return "/";
  }
  if (
    pathname.startsWith("/account") ||
    pathname.startsWith("/profile") ||
    pathname.startsWith("/family") ||
    pathname.startsWith("/notifications") ||
    pathname.startsWith("/settings") ||
    pathname.startsWith("/subscription")
  ) {
    return "/account";
  }
  if (pathname.startsWith("/home/")) {
    return "/";
  }
  return "/";
}
