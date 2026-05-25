import { getStoredDevInitData } from "@/lib/dev-auth";

/**
 * Minimal typed view of `window.Telegram.WebApp` we actually use.
 *
 * Inside a real Telegram Mini App WebView the Telegram client injects
 * the `Telegram.WebApp` global natively — no external script and no
 * SDK chunk are required. Reading it synchronously removes one external
 * CDN hit (telegram.org/js/telegram-web-app.js) and one dynamic import
 * (@twa-dev/sdk) from the startup critical path.
 */
export type TelegramWebApp = {
  initData: string;
  platform: string;
  colorScheme: string;
  themeParams: {
    bg_color?: string;
    text_color?: string;
    button_color?: string;
    button_text_color?: string;
  };
  ready: () => void;
  expand: () => void;
};

type TelegramGlobal = Window & {
  Telegram?: { WebApp?: TelegramWebApp };
};

/**
 * Synchronously read `window.Telegram.WebApp` if it is already present.
 * Returns null on the server or when running outside Telegram (dev / web).
 */
export function readTelegramWebApp(): TelegramWebApp | null {
  if (typeof window === "undefined") return null;
  return (window as TelegramGlobal).Telegram?.WebApp ?? null;
}

/**
 * Some Telegram clients inject `window.Telegram.WebApp` a frame or two
 * after page load. To avoid races we poll a few times with a short
 * delay. Resolves to null if the global never appears (i.e. user opened
 * the app outside Telegram — dev / preview / direct browser).
 */
export async function loadTelegramWebApp(): Promise<TelegramWebApp | null> {
  if (typeof window === "undefined") return null;

  const direct = readTelegramWebApp();
  if (direct) return direct;

  const tries = 5;
  const delayMs = 50;
  for (let attempt = 0; attempt < tries; attempt += 1) {
    await new Promise((resolve) => {
      setTimeout(resolve, delayMs);
    });
    const wa = readTelegramWebApp();
    if (wa) return wa;
  }
  return null;
}

export function getTelegramInitData(): string {
  if (typeof window === "undefined") return "";
  const telegramInit = readTelegramWebApp()?.initData ?? "";
  if (telegramInit.length > 0) return telegramInit;
  return getStoredDevInitData();
}
