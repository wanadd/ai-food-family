import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  ACCOUNT_HUB_ITEMS_2026,
  getActiveTabId2026,
  getRouteMeta2026,
  isBottomNavHidden2026,
  NAV_TABS_2026,
} from "./nav-config-2026";
import { resolveMigrationTarget } from "./route-migration-2026";

describe("account surfaces 2026 navigation", () => {
  it("keeps canonical bottom nav unchanged and events hidden", () => {
    expect(NAV_TABS_2026.map((tab) => tab.href)).toEqual([
      "/plan/today",
      "/home/shopping",
      "/",
      "/wellness",
    ]);
    expect(NAV_TABS_2026.some((tab) => tab.href === "/events")).toBe(false);
    expect(getActiveTabId2026("/events")).toBe("events");
  });

  it("keeps account settings routes canonical", () => {
    expect(getRouteMeta2026("/account")?.title).toBe("Профиль");
    expect(getRouteMeta2026("/account/family")?.title).toBe("Семья");
    expect(getRouteMeta2026("/account/notifications")?.title).toBe(
      "Уведомления",
    );
    expect(getRouteMeta2026("/account/settings/documents")?.title).toBe(
      "Документы",
    );
    expect(getRouteMeta2026("/account/settings/support")?.title).toBe(
      "Поддержка",
    );
    expect(getRouteMeta2026("/account/settings/about")?.title).toBe(
      "О приложении",
    );
  });

  it("hides bottom nav on deep account forms only", () => {
    expect(isBottomNavHidden2026("/")).toBe(false);
    expect(isBottomNavHidden2026("/plan/today")).toBe(false);
    expect(isBottomNavHidden2026("/home/shopping")).toBe(false);
    expect(isBottomNavHidden2026("/wellness")).toBe(false);
    expect(isBottomNavHidden2026("/account")).toBe(false);
    expect(isBottomNavHidden2026("/account/family")).toBe(true);
    expect(isBottomNavHidden2026("/account/nutrition")).toBe(true);
    expect(isBottomNavHidden2026("/account/notifications")).toBe(true);
    expect(isBottomNavHidden2026("/account/settings")).toBe(true);
    expect(isBottomNavHidden2026("/account/settings/support")).toBe(true);
  });

  it("keeps notification settings free of calendar CTAs", () => {
    const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
    const source = readFileSync(
      `${repoRoot}/components/notifications/NotificationSettingsForm.tsx`,
      "utf8",
    );

    expect(source).not.toContain("Добавить в календарь");
    expect(source).not.toContain("downloadIcs");
    expect(source).not.toContain("buildIcsFile");
  });

  it("keeps legacy redirects on account stack", () => {
    expect(resolveMigrationTarget("/profile")).toBe("/account");
    expect(resolveMigrationTarget("/settings")).toBe("/account/settings");
    expect(resolveMigrationTarget("/notifications")).toBe("/account/notifications");
  });

  it("links account hub cards to nested account surfaces", () => {
    const hrefs = ACCOUNT_HUB_ITEMS_2026.map((item) => item.href);
    expect(hrefs).toContain("/account/family");
    expect(hrefs).toContain("/account/nutrition");
    expect(hrefs).toContain("/account/notifications");
    expect(hrefs).toContain("/account/settings");
  });
});
