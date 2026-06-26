import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { normalizePantryMatchKey, PANTRY_SYNONYMS } from "@/lib/pantry/pantry-synonyms";
import { isIngredientInPantry, buildPantryNameIndex } from "@/lib/pantry/pantry-ingredient-match";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));

describe("sprint 1.8g admin hotfix", () => {
  it("subscription hub has no user tariff switching CTA", () => {
    const source = readFileSync(
      `${repoRoot}/components/monetization-2026/SubscriptionHub2026.tsx`,
      "utf8",
    );
    expect(source).not.toContain("subscription-upgrade-cta");
    expect(source).not.toContain("handleUpgrade");
    expect(source).toContain("только через администратора");
  });

  it("admin user detail has separate dangerous actions", () => {
    const source = readFileSync(
      `${repoRoot}/components/admin/AdminUserDetailPage.tsx`,
      "utf8",
    );
    expect(source).toContain("Заблокировать");
    expect(source).toContain("Разблокировать");
    expect(source).toContain("Очистить данные");
    expect(source).toContain("Сбросить как нового");
    expect(source).toContain("Удалить навсегда");
    expect(source).toContain("В архив");
    expect(source).toContain("/restore");
  });

  it("home has no duplicate 2x2 CTA grid", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/home/HomeV2.tsx`,
      "utf8",
    );
    expect(source).not.toContain('aria-label="Быстрые действия"');
    expect(source).toContain('aria-label="Статусы дня"');
  });

  it("shopping menu linked is collapsed by default", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/shopping/ShoppingV2.tsx`,
      "utf8",
    );
    expect(source).toContain("menuLinkedOpen");
    expect(source).toContain("Показать блюда");
    expect(source).toContain("shopping-sync-from-menu-sticky");
    expect(source).toContain("shopping-add-open-top");
    expect(source).not.toContain('data-testid="shopping-add-open"');
  });

  it("pantry has single add and sticky cook CTA", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/home-domain/PantryV2.tsx`,
      "utf8",
    );
    const addMatches = source.match(/Добавить продукт/g) ?? [];
    expect(addMatches.length).toBeLessThanOrEqual(3);
    expect(source).toContain("pantry-cook-from-available");
  });

  it("menu delete clears action query param", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/menu/MenuTodayV2.tsx`,
      "utf8",
    );
    expect(source).toContain('params.delete("action")');
    expect(source).toContain("deleteBusy");
  });

  it("recipe add shopping shows count toast", () => {
    const source = readFileSync(
      `${repoRoot}/components/recipes-2026/RecipeDetail2026.tsx`,
      "utf8",
    );
    expect(source).toContain("товаров добавлено в покупки");
  });

  it("blocked screen uses restricted title", () => {
    const source = readFileSync(
      `${repoRoot}/components/auth/TelegramRequiredScreen.tsx`,
      "utf8",
    );
    expect(source).toContain("Доступ ограничен");
  });

  it("paywall sheet has no checkout or plan switch", () => {
    const source = readFileSync(
      `${repoRoot}/components/monetization-2026/PaywallSheet2026.tsx`,
      "utf8",
    );
    expect(source).not.toContain("subscriptionCheckoutPath");
    expect(source).not.toContain("Сравнить тарифы");
    expect(source).toContain("Ваш тариф");
  });

  it("legacy subscription dashboard has no plan select button", () => {
    const source = readFileSync(
      `${repoRoot}/components/subscription/SubscriptionDashboard.tsx`,
      "utf8",
    );
    expect(source).not.toContain("Выбрать тариф");
    expect(source).not.toContain("selectPlanStub");
    expect(source).toContain("администратором");
  });

  it("admin users list shows status badge", () => {
    const source = readFileSync(
      `${repoRoot}/components/admin/AdminDashboard.tsx`,
      "utf8",
    );
    expect(source).toContain("Blocked");
    expect(source).toContain("Trial");
  });

  it("checkout stub has no self-service plan select", () => {
    const source = readFileSync(
      `${repoRoot}/components/monetization-2026/PaymentStub2026.tsx`,
      "utf8",
    );
    expect(source).not.toContain("selectPlanStub");
    expect(source).toContain("администратором");
  });

  it("account hub has no free or closed testing badges", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-2026/account/AccountHub2026.tsx`,
      "utf8",
    );
    expect(source).not.toContain("Free");
    expect(source).not.toContain("Закрытое тестирование");
  });

  it("about page has no closed testing badge", () => {
    const source = readFileSync(
      `${repoRoot}/app/settings/about/page.tsx`,
      "utf8",
    );
    expect(source).not.toContain("Закрытое тестирование");
  });

  it("plan display maps start legacy codes to Старт", async () => {
    const { planDisplayName } = await import("@/lib/monetization/plan-catalog-2026");
    expect(planDisplayName("start")).toBe("Старт");
    expect(planDisplayName("trial")).toBe("Старт");
    expect(planDisplayName("free")).toBe("Старт");
  });

  it("admin user detail has restore and start 7 days", () => {
    const source = readFileSync(
      `${repoRoot}/components/admin/AdminUserDetailPage.tsx`,
      "utf8",
    );
    expect(source).toContain("Восстановить из архива");
    expect(source).toContain("Старт 7 дней");
    expect(source).toContain('plan_code: "start"');
  });

  it("pantry synonyms normalize картошка to картофель", () => {
    expect(PANTRY_SYNONYMS["картошка"]).toBe("картофель");
    expect(normalizePantryMatchKey("Картошка")).toBe("картофель");
    const index = buildPantryNameIndex(["картошка"]);
    expect(isIngredientInPantry("картофель", index)).toBe(true);
  });
});
