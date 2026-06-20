import { getStoredDevInitData } from "@/lib/dev-auth";

/**
 * Minimal typed view of `window.Telegram.WebApp` we actually use.
 *
 * Inside most Telegram clients (mobile + recent Desktop / macOS) the
 * `Telegram.WebApp` global is injected natively before our script runs,
 * so we can read it synchronously. On older clients, on Web-K / Web-A,
 * and during some flaky network conditions the global appears a few
 * frames later — or only after the official telegram-web-app.js loader
 * runs. To stay safe we keep a fallback that:
 *
 *   1. tries `window.Telegram?.WebApp` directly,
 *   2. polls briefly (a few frames) in case the client is still wiring it,
 *   3. injects `<script src="https://telegram.org/js/telegram-web-app.js">`
 *      once if the global is still missing and waits for `onload`,
 *   4. polls again, and finally returns null (user is outside Telegram).
 *
 * Returning null is the explicit signal for the dev-fallback path
 * (localhost / browser preview / dev login).
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

const TELEGRAM_WEB_APP_SRC = "https://telegram.org/js/telegram-web-app.js";
const FAST_POLL_TRIES = 5; // ~5 * 50 = 250ms
const FAST_POLL_DELAY_MS = 50;
const SCRIPT_LOAD_TIMEOUT_MS = 4000;
const POST_SCRIPT_POLL_TRIES = 10; // ~10 * 50 = 500ms after script loads
const POST_SCRIPT_POLL_DELAY_MS = 50;

const isDev =
  typeof process !== "undefined" && process.env?.NODE_ENV !== "production";

function debugLog(message: string, extra?: unknown) {
  if (!isDev) return;
  if (typeof console === "undefined") return;
  if (extra !== undefined) {
    console.warn(`[PlanAm/Telegram] ${message}`, extra);
  } else {
    console.warn(`[PlanAm/Telegram] ${message}`);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function readTelegramWebApp(): TelegramWebApp | null {
  if (typeof window === "undefined") return null;
  return (window as TelegramGlobal).Telegram?.WebApp ?? null;
}

/**
 * Ensure the external telegram-web-app.js loader script exists in the
 * document, and resolve once it has finished loading (or quickly fail
 * out if the network is down). Idempotent: only injects once per page.
 */
let scriptLoadPromise: Promise<boolean> | null = null;

function ensureTelegramScript(): Promise<boolean> {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return Promise.resolve(false);
  }
  if (scriptLoadPromise) return scriptLoadPromise;

  scriptLoadPromise = new Promise<boolean>((resolve) => {
    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${TELEGRAM_WEB_APP_SRC}"]`,
    );
    if (existing) {
      // Already in DOM (might still be loading) — wait for its load event
      // or short-circuit if WebApp is already present.
      if (readTelegramWebApp()) {
        resolve(true);
        return;
      }
      const timer = window.setTimeout(() => resolve(false), SCRIPT_LOAD_TIMEOUT_MS);
      existing.addEventListener(
        "load",
        () => {
          window.clearTimeout(timer);
          resolve(true);
        },
        { once: true },
      );
      existing.addEventListener(
        "error",
        () => {
          window.clearTimeout(timer);
          resolve(false);
        },
        { once: true },
      );
      return;
    }

    const script = document.createElement("script");
    script.src = TELEGRAM_WEB_APP_SRC;
    script.async = true;
    const timer = window.setTimeout(() => {
      debugLog("telegram-web-app.js load timeout");
      resolve(false);
    }, SCRIPT_LOAD_TIMEOUT_MS);
    script.addEventListener(
      "load",
      () => {
        window.clearTimeout(timer);
        resolve(true);
      },
      { once: true },
    );
    script.addEventListener(
      "error",
      () => {
        window.clearTimeout(timer);
        debugLog("telegram-web-app.js failed to load");
        resolve(false);
      },
      { once: true },
    );
    document.head.appendChild(script);
  });

  return scriptLoadPromise;
}

/**
 * Resolve to a working TelegramWebApp instance or null.
 *
 * Strategy (in order of cheapest → most expensive):
 *   1. sync read of window.Telegram.WebApp
 *   2. short poll (~250ms) in case the client is wiring it up
 *   3. inject the official telegram-web-app.js loader, wait for onload
 *   4. second poll (~500ms) to give the SDK time to populate the global
 *   5. give up → null (caller falls back to dev login / TelegramRequired)
 */
export async function loadTelegramWebApp(): Promise<TelegramWebApp | null> {
  if (typeof window === "undefined") return null;

  const direct = readTelegramWebApp();
  if (direct?.initData) return direct;

  // Step 2 — quick poll: many clients populate WebApp 1-2 frames late.
  for (let i = 0; i < FAST_POLL_TRIES; i += 1) {
    await sleep(FAST_POLL_DELAY_MS);
    const wa = readTelegramWebApp();
    if (wa?.initData) return wa;
  }

  // Step 3 — fall back to the official loader. We need this for cases
  // where the host client does NOT pre-inject Telegram.WebApp (some
  // older Desktop builds, Web-K/Web-A in certain modes, custom hosts).
  debugLog("WebApp not present after fast poll, injecting loader script");
  const scriptOk = await ensureTelegramScript();
  if (!scriptOk) {
    debugLog("loader script never finished — proceeding without WebApp");
    return readTelegramWebApp();
  }

  // Step 4 — second poll: even after the script's onload event fires,
  // some clients take another tick to populate initData.
  for (let i = 0; i < POST_SCRIPT_POLL_TRIES; i += 1) {
    const wa = readTelegramWebApp();
    if (wa?.initData) return wa;
    await sleep(POST_SCRIPT_POLL_DELAY_MS);
  }

  // Last attempt: even an empty-initData WebApp object can still be
  // useful for theming hooks (.platform / .themeParams). The caller
  // checks initData length before assuming the user is authed.
  const final = readTelegramWebApp();
  if (!final) {
    debugLog("WebApp still missing after loader + poll");
  } else if (!final.initData) {
    debugLog("WebApp present but initData is empty");
  }
  return final;
}

export function getTelegramInitData(): string {
  if (typeof window === "undefined") return "";
  const telegramInit = readTelegramWebApp()?.initData ?? "";
  if (telegramInit.length > 0) return telegramInit;
  return getStoredDevInitData();
}
