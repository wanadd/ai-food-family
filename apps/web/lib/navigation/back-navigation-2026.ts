/** Back navigation for nested UI 2026 screens (Telegram + browser). */

import { readReturnTo, RETURN_TO_PARAM } from "@/lib/navigation/return-to";

const MAIN_TAB_PATHS = new Set([
  "/",
  "/plan/today",
  "/shopping",
  "/home/shopping",
  "/wellness",
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
  if (pathname === "/" || pathname === "/account" || pathname === "/shopping") {
    return false;
  }
  if (pathname.startsWith("/onboarding") || pathname.startsWith("/admin")) {
    return false;
  }
  return true;
}

const RECIPE_COOK = /^\/plan\/recipes\/(\d+)\/cook/;

export function getBackFallback2026(pathname: string): string {
  const cookMatch = pathname.match(RECIPE_COOK);
  if (cookMatch?.[1]) {
    return `/plan/recipes/${cookMatch[1]}`;
  }
  if (RECIPE_DETAIL.test(pathname)) {
    return "/plan/recipes";
  }
  if (pathname.startsWith("/plan/")) {
    return "/plan/today";
  }
  if (pathname.startsWith("/wellness")) {
    return "/wellness";
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
  if (pathname.startsWith("/home/leftovers") || pathname.startsWith("/shopping/leftovers")) {
    return "/home/pantry";
  }
  if (pathname.startsWith("/home/pantry") || pathname.startsWith("/shopping/pantry")) {
    return "/home/shopping";
  }
  if (pathname.startsWith("/home/")) {
    return "/";
  }
  return "/";
}

export function resolveBackTarget2026(
  pathname: string,
  searchParams?: URLSearchParams | null,
): string {
  const explicit = searchParams?.get(RETURN_TO_PARAM);
  if (explicit) {
    return readReturnTo(searchParams, getBackFallback2026(pathname));
  }
  return getBackFallback2026(pathname);
}
