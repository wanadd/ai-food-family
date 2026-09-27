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
  close: () => undefined,
  back: () => {
    if (typeof window !== "undefined") window.history.back();
  },
};
