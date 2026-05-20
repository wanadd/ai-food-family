type TelegramWebApp = typeof import("@twa-dev/sdk").default;

let webAppPromise: Promise<TelegramWebApp> | null = null;

/** Safe access to @twa-dev/sdk — only on the client (avoids SSR window errors). */
export async function loadTelegramWebApp(): Promise<TelegramWebApp | null> {
  if (typeof window === "undefined") {
    return null;
  }

  if (!webAppPromise) {
    webAppPromise = import("@twa-dev/sdk").then((module) => module.default);
  }

  return webAppPromise;
}

export function getTelegramInitData(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const telegram = (
    window as Window & { Telegram?: { WebApp?: { initData?: string } } }
  ).Telegram?.WebApp;
  return telegram?.initData ?? "";
}
