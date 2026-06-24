import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  ACCOUNT_HUB_ITEMS_2026,
  getActiveTabId2026,
  getRouteMeta2026,
  isBottomNavHidden2026,
  isShellHeaderHidden2026,
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

  it("hides shell header on nested account forms", () => {
    expect(isShellHeaderHidden2026("/account")).toBe(true);
    expect(isShellHeaderHidden2026("/account/family")).toBe(true);
    expect(isShellHeaderHidden2026("/account/nutrition")).toBe(true);
    expect(isShellHeaderHidden2026("/account/notifications")).toBe(true);
    expect(isShellHeaderHidden2026("/account/settings")).toBe(true);
    expect(isShellHeaderHidden2026("/account/settings/support")).toBe(true);
    expect(isShellHeaderHidden2026("/plan/today")).toBe(true);
    expect(isShellHeaderHidden2026("/")).toBe(true);
  });

  it("keeps notification settings free of calendar CTAs", () => {
    const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
    const settingsSource = readFileSync(
      `${repoRoot}/components/notifications/NotificationSettingsForm.tsx`,
      "utf8",
    );
    const viewSource = readFileSync(
      `${repoRoot}/components/notifications/NotificationsView.tsx`,
      "utf8",
    );

    expect(settingsSource).not.toContain("Добавить в календарь");
    expect(settingsSource).not.toContain("downloadIcs");
    expect(settingsSource).not.toContain("buildIcsFile");
    expect(viewSource).not.toContain("Добавить в календарь");
    expect(viewSource).not.toContain("NOTIFICATION_SECTIONS");
  });

  it("renders compact notification toggles in care panel", () => {
    const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
    const source = readFileSync(
      `${repoRoot}/components/care/CareSettingsPanel.tsx`,
      "utf8",
    );

    expect(source).toContain("Что напоминать");
    expect(source).toContain("Покупки");
    expect(source).toContain("Готовка");
    expect(source).toContain("Тестовое уведомление");
    expect(source).not.toContain("examples:");
  });

  it("renders family layout with separated sections", () => {
    const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
    const source = readFileSync(
      `${repoRoot}/components/family/FamilyDashboard.tsx`,
      "utf8",
    );

    expect(source).toContain("Ваша семья");
    expect(source).toContain('data-testid="family-add-member"');
    expect(source).toContain("Участники");
    expect(source).toContain("MemberCard");
    expect(source).toMatch(/mt-4[\s\S]*family-add-member/);
    expect(source).toContain("mt-6 space-y-4");
  });

  it("renders nutrition as compact accordion dashboard", () => {
    const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
    const formSource = readFileSync(
      `${repoRoot}/components/nutrition-profile/NutritionProfileForm.tsx`,
      "utf8",
    );
    const optionsSource = readFileSync(
      `${repoRoot}/lib/onboarding/options.ts`,
      "utf8",
    );

    expect(formSource).toContain('useState<NutritionSectionId | null>(null)');
    expect(formSource).toContain("NutritionSection");
    expect(formSource).toContain("isDirty ?");
    expect(formSource).toContain('pa26-page-title mb-4">Питание');
    expect(optionsSource).toContain("Простые продукты");
    expect(optionsSource).not.toContain("₽ / день");
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
