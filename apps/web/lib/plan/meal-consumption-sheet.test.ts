import { describe, expect, it } from "vitest";

import {
  MEAL_CONSUMPTION_FORBIDDEN_PHRASES,
  MEAL_CONSUMPTION_SHEET_SUBTITLE,
  MEAL_CONSUMPTION_SHEET_TITLE,
  MENU_TODAY_MARK_CONSUMPTION_BUTTON,
} from "./meal-consumption-sheet";

describe("meal consumption sheet copy", () => {
  it("uses Отметить съеденное button label", () => {
    expect(MENU_TODAY_MARK_CONSUMPTION_BUTTON).toBe("Отметить съеденное");
    expect(MENU_TODAY_MARK_CONSUMPTION_BUTTON).not.toBe("Показать итог дня");
  });

  it("uses Что вы съели? sheet title", () => {
    expect(MEAL_CONSUMPTION_SHEET_TITLE).toBe("Что вы съели?");
  });

  it("does not include legacy summary phrases", () => {
    const combined = [
      MEAL_CONSUMPTION_SHEET_TITLE,
      MEAL_CONSUMPTION_SHEET_SUBTITLE,
      MENU_TODAY_MARK_CONSUMPTION_BUTTON,
    ].join(" ");

    for (const phrase of MEAL_CONSUMPTION_FORBIDDEN_PHRASES) {
      expect(combined).not.toContain(phrase);
    }
  });

  it("avoids cooking-oriented question in subtitle", () => {
    expect(MEAL_CONSUMPTION_SHEET_SUBTITLE).not.toContain("приготовили");
    expect(MEAL_CONSUMPTION_SHEET_SUBTITLE).toContain("блюда");
  });
});
