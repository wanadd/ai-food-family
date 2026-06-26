import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { groupPantryItems } from "@/lib/dom/pantry-groups";
import { getBackFallback2026, shouldShowBack2026 } from "@/lib/navigation/back-navigation-2026";
import {
  buildPantryNameIndex,
  getIngredientPantryStatus,
  isIngredientInPantry,
} from "@/lib/pantry/pantry-ingredient-match";
import { formatProductQuantity } from "@/lib/planam/productTaxonomy";
import {
  computeShoppingFlowStatus,
  isBoughtToday,
} from "@/lib/shopping/shopping-flow-summary";
import { filterMissingIngredients } from "@/lib/shopping/add-missing-ingredients";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));

describe("shopping pantry sprint 1.8f", () => {
  it("shopping renders status strip and menu link", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/shopping/ShoppingV2.tsx`,
      "utf8",
    );
    expect(source).toContain('data-testid="shopping-status-strip"');
    expect(source).toContain('data-testid="shopping-menu-linked"');
    expect(source).toContain('data-testid="shopping-go-pantry"');
    expect(source).toContain("Куплено · добавлено в запасы");
    expect(source).toContain('data-testid="shopping-bought-today"');
  });

  it("shopping groups by category via groupShoppingItems", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/shopping/ShoppingV2.tsx`,
      "utf8",
    );
    expect(source).toContain("groupShoppingItems");
  });

  it("does not duplicate units in quantity display", () => {
    expect(formatProductQuantity({ quantity: "1 л", unit: "л" })).toBe("1 л");
    expect(formatProductQuantity({ amount: "200 г г" })).toBe("200 г");
  });

  it("pantry separates products and prepared dishes", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/home-domain/PantryV2.tsx`,
      "utf8",
    );
    expect(source).toContain("Готовая еда");
    expect(source).toContain('data-testid="pantry-product-groups"');
    expect(source).toContain("preparedDishes");
    expect(source).toContain('id: "prepared"');
  });

  it("pantry add has category fallback via detectProductCategory", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/home-domain/PantryV2.tsx`,
      "utf8",
    );
    expect(source).toContain("detectProductCategory");
    expect(source).toContain("SHOPPING_CATEGORIES_V1");
  });

  it("cook-from-stock block shows есть X из Y", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/home-domain/CookFromPantryBlockV2.tsx`,
      "utf8",
    );
    expect(source).toContain('data-testid="cook-from-pantry-block"');
    expect(source).toContain("Есть {r.have} из {r.total} ингредиентов");
    expect(source).toContain("Добавьте продукты в запасы");
  });

  it("recipe checklist can show pantry status", () => {
    const detail = readFileSync(
      `${repoRoot}/components/recipes-2026/RecipeDetail2026.tsx`,
      "utf8",
    );
    const checklist = readFileSync(
      `${repoRoot}/components/recipes-2026/RecipeIngredientsChecklist.tsx`,
      "utf8",
    );
    expect(detail).toContain("pantryNames");
    expect(detail).toContain('data-testid="recipe-add-missing-shopping"');
    expect(checklist).toContain("recipe-ingredient-pantry-");
  });

  it("conservative pantry ingredient matching avoids substring false positives", () => {
    const index = buildPantryNameIndex(["морковь"]);
    expect(isIngredientInPantry("морковь", index)).toBe(true);
    expect(isIngredientInPantry("сок морковный", index)).toBe(false);
    expect(getIngredientPantryStatus("лук", buildPantryNameIndex(["лука"]))).toBe(
      "home",
    );
  });

  it("filters missing ingredients for shopping CTA", () => {
    const missing = filterMissingIngredients(
      [
        { name: "Морковь", amount: "1 шт" },
        { name: "Лук", amount: "2 шт" },
      ],
      ["морковь"],
    );
    expect(missing).toHaveLength(1);
    expect(missing[0]?.name).toBe("Лук");
  });

  it("shopping flow status computes menu-linked counts", () => {
    const status = computeShoppingFlowStatus(
      {
        scope_mode: "personal",
        user_id: 1,
        family_id: null,
        menu_title: "Меню недели",
        items: [
          {
            id: "1",
            name: "Морковь",
            category: "овощи",
            quantity: "1",
            unit: "шт",
            amount: "1 шт",
            amounts: [],
            note: null,
            source: "menu",
            checked: false,
            checked_by_user_id: null,
            checked_by_name: null,
            checked_at: null,
            linked_pantry_item_id: null,
            added_to_pantry: false,
            created_by_user_id: null,
          },
        ],
        categories: [],
        total_count: 1,
        checked_count: 0,
        updated_at: "",
      },
      [{ id: 1, name: "Соль", category: "специи", quantity: "1", unit: "шт", amount: "1 шт", note: null, source: "manual", is_expired: false, expires_at: null, days_until_expiry: 99, created_at: "" }],
      [{ recipe_id: 1, title: "Суп", have: 5, total: 5, missing_ingredients: [], coverage_ratio: 1 }],
    );
    expect(status.toBuy).toBe(1);
    expect(status.atHome).toBe(1);
    expect(status.dishesCovered).toBe(1);
    expect(status.menuLinkedItems).toBe(1);
  });

  it("empty pantry cook block shows useful empty state", () => {
    const source = readFileSync(
      `${repoRoot}/components/planam-v2/home-domain/CookFromPantryBlockV2.tsx`,
      "utf8",
    );
    expect(source).toContain("подходящие рецепты");
  });

  it("/home/shopping root has no BackButton", () => {
    expect(shouldShowBack2026("/home/shopping")).toBe(false);
  });

  it("stock nested routes have correct BackButton fallbacks", () => {
    expect(getBackFallback2026("/home/pantry")).toBe("/home/shopping");
    expect(getBackFallback2026("/home/leftovers")).toBe("/home/pantry");
  });

  it("groups pantry items by category", () => {
    const groups = groupPantryItems(
      [
        {
          id: 1,
          name: "Морковь",
          category: "овощи",
          quantity: "1",
          unit: "кг",
          amount: "1 кг",
          note: null,
          source: "manual",
          is_expired: false,
          expires_at: null,
          days_until_expiry: 5,
          created_at: "",
        },
        {
          id: 2,
          name: "Лук",
          category: "овощи",
          quantity: "2",
          unit: "шт",
          amount: "2 шт",
          note: null,
          source: "manual",
          is_expired: false,
          expires_at: null,
          days_until_expiry: 5,
          created_at: "",
        },
      ],
      [],
    );
    expect(groups).toHaveLength(1);
    expect(groups[0]?.items).toHaveLength(2);
  });

  it("isBoughtToday respects checked_at date", () => {
    const today = new Date().toISOString();
    expect(isBoughtToday(today)).toBe(true);
    expect(isBoughtToday("2020-01-01T12:00:00.000Z")).toBe(false);
  });
});
