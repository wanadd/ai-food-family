import { describe, expect, it } from "vitest";

import {
  buildConsumptionMemberTargets,
  MEAL_CONSUMPTION_FORBIDDEN_PHRASES,
  MEAL_CONSUMPTION_PORTION_OPTIONS,
  MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
  MEAL_CONSUMPTION_SAVE_DISABLED_HINT,
  MEAL_CONSUMPTION_SHEET_SUBTITLE,
  MEAL_CONSUMPTION_SHEET_TITLE,
  MENU_TODAY_MARK_CONSUMPTION_BUTTON,
  shouldShowConsumptionMemberPicker,
} from "./meal-consumption-sheet";

describe("meal consumption sheet copy", () => {
  it("uses Отметить съеденное button label", () => {
    expect(MENU_TODAY_MARK_CONSUMPTION_BUTTON).toBe("Отметить съеденное");
    expect(MENU_TODAY_MARK_CONSUMPTION_BUTTON).not.toBe("Показать итог дня");
  });

  it("uses Что вы съели? sheet title", () => {
    expect(MEAL_CONSUMPTION_SHEET_TITLE).toBe("Что вы съели?");
  });

  it("exposes sticky footer copy", () => {
    expect(MEAL_CONSUMPTION_SAVE_BUTTON_LABEL).toBe("Сохранить отметки");
    expect(MEAL_CONSUMPTION_SAVE_DISABLED_HINT).toBe(
      "Сохранение будет доступно после настройки семейного учёта",
    );
  });

  it("does not include legacy summary phrases", () => {
    const combined = [
      MEAL_CONSUMPTION_SHEET_TITLE,
      MEAL_CONSUMPTION_SHEET_SUBTITLE,
      MENU_TODAY_MARK_CONSUMPTION_BUTTON,
      MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
      MEAL_CONSUMPTION_SAVE_DISABLED_HINT,
    ].join(" ");

    for (const phrase of MEAL_CONSUMPTION_FORBIDDEN_PHRASES) {
      expect(combined).not.toContain(phrase);
    }
  });

  it("avoids cooking-oriented question in subtitle", () => {
    expect(MEAL_CONSUMPTION_SHEET_SUBTITLE).not.toContain("приготовили");
    expect(MEAL_CONSUMPTION_SHEET_SUBTITLE).toContain("блюда");
  });

  it("uses Russian portion labels with comma decimal", () => {
    expect(MEAL_CONSUMPTION_PORTION_OPTIONS.map((o) => o.label)).toEqual([
      "0,5",
      "1",
      "1,5",
      "2",
    ]);
    expect(MEAL_CONSUMPTION_PORTION_OPTIONS.map((o) => o.value)).toEqual([
      0.5, 1, 1.5, 2,
    ]);
    const labels = MEAL_CONSUMPTION_PORTION_OPTIONS.map((o) => o.label).join(" ");
    expect(labels).not.toContain("½");
    expect(labels).not.toContain("1.5");
    expect(labels).not.toContain("0.5");
    expect(labels).not.toContain("2.0");
  });
});

describe("consumption member picker", () => {
  const ivan = { id: 1, display_name: "Иван", is_you: true };
  const maria = { id: 2, display_name: "Мария", is_you: false };

  it("hides picker for non-admin (single self target)", () => {
    expect(shouldShowConsumptionMemberPicker([ivan, maria], false)).toBe(false);
    expect(buildConsumptionMemberTargets([ivan, maria], false)).toHaveLength(1);
  });

  it("shows picker for family admin with members", () => {
    expect(shouldShowConsumptionMemberPicker([ivan, maria], true)).toBe(true);
    const targets = buildConsumptionMemberTargets([ivan, maria], true);
    expect(targets.map((t) => t.label)).toEqual(["Я", "Мария", "Вся семья"]);
  });

  it("hides picker in personal mode (no members)", () => {
    expect(shouldShowConsumptionMemberPicker([], false)).toBe(false);
  });

  it("shows picker for admin even when alone in family", () => {
    expect(shouldShowConsumptionMemberPicker([ivan], true)).toBe(true);
    expect(buildConsumptionMemberTargets([ivan], true).map((t) => t.label)).toEqual([
      "Я",
      "Вся семья",
    ]);
  });
});
