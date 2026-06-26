export const RETURN_TO_PARAM = "returnTo";

const TAB_ROOTS_2026 = [
  "/plan/today",
  "/home/shopping",
  "/wellness",
  "/account",
  "/",
];

const TAB_ROOTS_LEGACY = [
  "/menu",
  "/shopping",
  "/",
  "/health",
  "/profile",
];

export function withReturnTo(path: string, returnTo: string): string {
  const [base, query = ""] = path.split("?");
  const params = new URLSearchParams(query);
  params.set(RETURN_TO_PARAM, returnTo);
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

export function sanitizeReturnTo(
  value: string | null | undefined,
  fallback = "/account",
): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return fallback;
  }
  return value;
}

export function readReturnTo(
  searchParams: URLSearchParams | null | undefined,
  fallback: string,
): string {
  if (!searchParams) {
    return fallback;
  }
  return sanitizeReturnTo(searchParams.get(RETURN_TO_PARAM), fallback);
}

export function backLabelForReturnTo(returnTo: string): string {
  if (returnTo.startsWith("/wellness") || returnTo.startsWith("/health")) {
    return "Здоровье";
  }
  if (returnTo.startsWith("/plan/today") || returnTo.startsWith("/menu/current")) {
    return "Сегодня";
  }
  if (returnTo.startsWith("/plan/recipes") || returnTo.startsWith("/menu/recipes")) {
    return "Рецепты";
  }
  if (returnTo.startsWith("/plan")) {
    return "План";
  }
  if (
    returnTo.startsWith("/home/shopping") ||
    returnTo.startsWith("/shopping") ||
    returnTo.startsWith("/pantry") ||
    returnTo.startsWith("/home/pantry")
  ) {
    return "Покупки";
  }
  if (returnTo.startsWith("/home/leftovers")) {
    return "Запасы";
  }
  if (returnTo.startsWith("/account") || returnTo.startsWith("/profile")) {
    return "Профиль";
  }
  if (returnTo === "/") {
    return "Главная";
  }
  return "Назад";
}

export function isTabRoute(pathname: string): boolean {
  const roots = [...TAB_ROOTS_2026, ...TAB_ROOTS_LEGACY];
  return roots.some(
    (root) => pathname === root || (root !== "/" && pathname.startsWith(`${root}/`)),
  );
}
