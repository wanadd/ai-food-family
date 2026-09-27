import type { PlatformAdapter, PlatformCapability } from "./adapter";

export const webPlatformAdapter: PlatformAdapter = {
  clientType: "web",
  capabilities: new Set<PlatformCapability>([
    "viewport",
    "safe_area",
    "back",
    "theme",
    "share",
    "deep_link",
    "file_picker",
    "external_browser",
  ]),
  requestFullscreen: async () => false,
  share: async (data) => {
    if (typeof navigator !== "undefined" && typeof navigator.share === "function") {
      await navigator.share(data);
      return true;
    }
    if (typeof navigator !== "undefined" && navigator.clipboard && data.url) {
      await navigator.clipboard.writeText(data.url);
      return true;
    }
    return false;
  },
  close: () => undefined,
  back: () => {
    if (typeof window !== "undefined") window.history.back();
  },
};
