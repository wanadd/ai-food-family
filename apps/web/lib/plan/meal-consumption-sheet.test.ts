import { describe, expect, it } from "vitest";

import {
  applyConsumptionLogsToDrafts,
  buildConsumptionSaveEntries,
  buildDefaultConsumptionDrafts,
  hasSaveableConsumptionDrafts,
  MEAL_CONSUMPTION_FORBIDDEN_PHRASES,
  MEAL_CONSUMPTION_PORTION_OPTIONS,
  MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
  MEAL_CONSUMPTION_SAVE_ERROR,
  MEAL_CONSUMPTION_SAVING_LABEL,
  MEAL_CONSUMPTION_PERMISSION_ERROR,
  MEAL_CONSUMPTION_SHEET_SUBTITLE,
  MEAL_CONSUMPTION_SHEET_TITLE,
  MENU_TODAY_MARK_CONSUMPTION_BUTTON,
  mealConsumptionKey,
  resolveConsumptionTargets,
  shouldShowConsumptionMemberPicker,
} from "./meal-consumption-sheet";
import {
  mealConsumptionErrorMessage,
  MEAL_CONSUMPTION_PERMISSION_ERROR as API_PERMISSION_ERROR,
} from "./meal-consumption-api";

describe("meal consumption sheet copy", () => {
  it("uses Отметить съеденное button label", () => {
    expect(MENU_TODAY_MARK_CONSUMPTION_BUTTON).toBe("Отметить съеденное");
    expect(MENU_TODAY_MARK_CONSUMPTION_BUTTON).not.toBe("Показать итог дня");
  });

  it("uses Что вы съели? sheet title", () => {
    expect(MEAL_CONSUMPTION_SHEET_TITLE).toBe("Что вы съели?");
  });

  it("exposes save button and loading labels", () => {
    expect(MEAL_CONSUMPTION_SAVE_BUTTON_LABEL).toBe("Сохранить отметки");
    expect(MEAL_CONSUMPTION_SAVING_LABEL).toBe("Сохраняем...");
  });

  it("does not include legacy summary phrases", () => {
    const combined = [
      MEAL_CONSUMPTION_SHEET_TITLE,
      MEAL_CONSUMPTION_SHEET_SUBTITLE,
      MENU_TODAY_MARK_CONSUMPTION_BUTTON,
      MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
      MEAL_CONSUMPTION_SAVE_ERROR,
      MEAL_CONSUMPTION_SAVING_LABEL,
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
  const ivan = { id: 1, display_name: "Иван", is_you: true, user_id: 10 };
  const maria = { id: 2, display_name: "Мария", is_you: false, user_id: 11 };

  it("hides picker for non-admin (single self target)", () => {
    expect(shouldShowConsumptionMemberPicker([ivan, maria], false)).toBe(false);
  });

  it("shows picker for family admin with members", () => {
    expect(shouldShowConsumptionMemberPicker([ivan, maria], true)).toBe(true);
  });
});

describe("consumption save helpers", () => {
  const meals = [
    {
      meal_type: "lunch",
      recipe_id: 256,
      recipe_title: "Суп",
      mealIndex: 0,
    },
  ];

  it("save button active when meal included", () => {
    const drafts = buildDefaultConsumptionDrafts(meals);
    expect(hasSaveableConsumptionDrafts(drafts)).toBe(true);
    drafts[mealConsumptionKey("lunch", 0)].included = false;
    expect(hasSaveableConsumptionDrafts(drafts)).toBe(false);
  });

  it("builds bulk entries for self target", () => {
    const drafts = buildDefaultConsumptionDrafts(meals);
    const entries = buildConsumptionSaveEntries(
      meals,
      drafts,
      [{ user_id: 10, family_member_id: 1 }],
    );
    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      user_id: 10,
      meal_type: "lunch",
      status: "eaten",
      portion_multiplier: 1,
    });
  });

  it("ate_out sends zero portion in payload", () => {
    const drafts = buildDefaultConsumptionDrafts(meals);
    drafts[mealConsumptionKey("lunch", 0)].status = "ate_out";
    const entries = buildConsumptionSaveEntries(
      meals,
      drafts,
      [{ user_id: 10, family_member_id: 1 }],
    );
    expect(entries[0].portion_multiplier).toBe(0);
  });

  it("expands family target to all members", () => {
    const members = [
      { id: 1, display_name: "Я", is_you: true, user_id: 10 },
      { id: 2, display_name: "Мария", is_you: false, user_id: 11 },
    ];
    const targets = resolveConsumptionTargets("family", members);
    expect(targets).toHaveLength(2);
  });

  it("restores saved logs into drafts", () => {
    const logs = [
      {
        user_id: 10,
        family_member_id: 1,
        meal_type: "lunch",
        recipe_id: 256,
        status: "eaten",
        portion_multiplier: 1.5,
      },
    ];
    const drafts = applyConsumptionLogsToDrafts(
      meals,
      logs,
      { user_id: 10, family_member_id: 1 },
    );
    expect(drafts[mealConsumptionKey("lunch", 0)]).toMatchObject({
      included: true,
      portion: 1.5,
      status: "eaten",
    });
  });

  it("maps permission error message", () => {
    expect(
      mealConsumptionErrorMessage(new Error("Нет прав отмечать питание за этого участника")),
    ).toBe(API_PERMISSION_ERROR);
    expect(MEAL_CONSUMPTION_PERMISSION_ERROR).toBe(API_PERMISSION_ERROR);
  });

  it("maps generic save error", () => {
    expect(mealConsumptionErrorMessage(new Error("500"))).toBe(
      MEAL_CONSUMPTION_SAVE_ERROR,
    );
  });
});
