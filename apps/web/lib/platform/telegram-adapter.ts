import { readTelegramWebApp } from "@/lib/telegram-webapp";
import type { PlatformAdapter, PlatformCapability } from "./adapter";

export function createTelegramPlatformAdapter(): PlatformAdapter | null {
  const webApp = readTelegramWebApp();
  if (!webApp) return null;
  return {
    clientType: "telegram",
    capabilities: new Set<PlatformCapability>([
      "auth_bootstrap",
      "viewport",
      "safe_area",
      "fullscreen",
      "back",
      "theme",
      "share",
      "deep_link",
      "file_picker",
      "notifications",
      "external_browser",
    ]),
    requestFullscreen: async () => {
      const request = (webApp as TelegramWebAppWithFullscreen).requestFullscreen;
      if (typeof request !== "function") return false;
      try {
        await Promise.resolve(request.call(webApp));
        return true;
      } catch {
        return false;
      }
    },
    close: () => webApp.close?.(),
    back: () => undefined,
  };
}

type TelegramWebAppWithFullscreen = {
  requestFullscreen?: () => void | Promise<void>;
};
