export const RETURN_TO_PARAM = "returnTo";

const TAB_ROOTS = [
  "/nutritionist",
  "/menu",
  "/shopping",
  "/pantry",
  "/",
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
  if (returnTo.startsWith("/nutritionist")) return "Нутрициолог";
  if (returnTo.startsWith("/menu")) return "Меню";
  if (returnTo.startsWith("/shopping")) return "Покупки";
  if (returnTo.startsWith("/pantry")) return "Запасы";
  if (returnTo.startsWith("/profile")) return "Профиль";
  if (returnTo === "/") return "ПланАм";
  return "Назад";
}

export function isTabRoute(pathname: string): boolean {
  return TAB_ROOTS.some(
    (root) => pathname === root || (root !== "/" && pathname.startsWith(`${root}/`)),
  );
}
