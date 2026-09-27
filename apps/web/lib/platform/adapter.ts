export type PlatformType = "telegram" | "web" | "max" | "android" | "ios";

export type PlatformCapability =
  | "auth_bootstrap"
  | "viewport"
  | "safe_area"
  | "fullscreen"
  | "back"
  | "theme"
  | "haptics"
  | "share"
  | "deep_link"
  | "camera"
  | "file_picker"
  | "notifications"
  | "push"
  | "payments"
  | "external_browser";

export type PlatformAdapter = {
  readonly clientType: PlatformType;
  readonly capabilities: ReadonlySet<PlatformCapability>;
  requestFullscreen: () => Promise<boolean>;
  close: () => void;
  back: () => void;
};

export function setViewportHeight() {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  const height = window.visualViewport?.height ?? window.innerHeight;
  document.documentElement.style.setProperty("--planam-viewport-height", `${height}px`);
}

export function installViewportListener(): () => void {
  if (typeof window === "undefined") return () => {};
  setViewportHeight();
  const viewport = window.visualViewport;
  viewport?.addEventListener("resize", setViewportHeight);
  window.addEventListener("resize", setViewportHeight);
  return () => {
    viewport?.removeEventListener("resize", setViewportHeight);
    window.removeEventListener("resize", setViewportHeight);
  };
}
