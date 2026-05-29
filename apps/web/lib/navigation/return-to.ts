export const RETURN_TO_PARAM = "returnTo";

const TAB_ROOTS = [
  "/menu",
  "/shopping",
  "/",
  "/health",
  "/profile",
];

export function withReturnTo(path: string, returnTo: string): string {
  const base = path.split("?")[0] ?? path;
  const params = new URLSearchParams(path.includes("?") ? path.split("?")[1] : "");
  params.set(RETURN_TO_PARAM, returnTo);
  return `${base}?${params.toString()}`;
}

export function sanitizeReturnTo(
  value: string | null | undefined,
  fallback = "/profile",
): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return fallback;
  }
  return value;
}

export function backLabelForReturnTo(returnTo: string): string {
  // /nutritionist оставлен для совместимости со старыми returnTo-значениями.
  if (returnTo.startsWith("/health") || returnTo.startsWith("/nutritionist"))
    return "Здоровье";
  if (returnTo.startsWith("/menu")) return "Меню";
  // Запасы и остатки теперь часть раздела «Покупки».
  if (returnTo.startsWith("/shopping") || returnTo.startsWith("/pantry"))
    return "Покупки";
  if (returnTo.startsWith("/profile")) return "Профиль";
  if (returnTo === "/") return "ПланАм";
  return "Назад";
}

export function isTabRoute(pathname: string): boolean {
  return TAB_ROOTS.some(
    (root) => pathname === root || (root !== "/" && pathname.startsWith(`${root}/`)),
  );
}
