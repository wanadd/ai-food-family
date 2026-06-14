import { describe, expect, it } from "vitest";

import {
  buildConsumptionMemberTargets,
  buildConsumptionSaveEntries,
  buildDefaultConsumptionDrafts,
  buildPersonalConsumptionPayload,
  canSaveConsumptionDrafts,
  consumptionSaveFooterHint,
  hasSaveableConsumptionDrafts,
  MEAL_CONSUMPTION_FORBIDDEN_PHRASES,
  MEAL_CONSUMPTION_PERSONAL_SAVE_HINT,
  MEAL_CONSUMPTION_PORTION_OPTIONS,
  MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
  MEAL_CONSUMPTION_SAVE_DISABLED_HINT,
  MEAL_CONSUMPTION_SAVING_LABEL,
  MEAL_CONSUMPTION_VIRTUAL_MEMBER_SAVE_HINT,
  MENU_TODAY_MARK_CONSUMPTION_BUTTON,
  mealConsumptionKey,
  resolveConsumptionFamilyId,
  resolveConsumptionTargets,
  shouldShowConsumptionMemberPicker,
} from "./meal-consumption-sheet";

describe("meal consumption sheet copy", () => {
  it("uses Отметить съеденное button label", () => {
    expect(MENU_TODAY_MARK_CONSUMPTION_BUTTON).toBe("Отметить съеденное");
  });

  it("does not include legacy summary phrases in active copy", () => {
    const combined = [
      MEAL_CONSUMPTION_PERSONAL_SAVE_HINT,
      MEAL_CONSUMPTION_VIRTUAL_MEMBER_SAVE_HINT,
      MEAL_CONSUMPTION_SAVE_BUTTON_LABEL,
      MEAL_CONSUMPTION_SAVING_LABEL,
    ].join(" ");

    for (const phrase of MEAL_CONSUMPTION_FORBIDDEN_PHRASES) {
      expect(combined).not.toContain(phrase);
    }
    expect(combined).not.toContain(MEAL_CONSUMPTION_SAVE_DISABLED_HINT);
  });
});

describe("consumption member picker", () => {
  const ivan = {
    id: 1,
    display_name: "Иван",
    is_you: true,
    is_virtual: false,
    user_id: 10,
  };
  const maria = {
    id: 2,
    display_name: "Мария",
    is_you: false,
    is_virtual: false,
    user_id: 11,
  };
  const child = {
    id: 3,
    display_name: "Петя",
    is_you: false,
    is_virtual: true,
    user_id: null,
  };

  it("hides picker for non-admin", () => {
    expect(shouldShowConsumptionMemberPicker([ivan, maria, child], false)).toBe(false);
    expect(buildConsumptionMemberTargets([ivan, maria], false)).toHaveLength(1);
  });

  it("admin picker shows only self and virtual members", () => {
    const targets = buildConsumptionMemberTargets([ivan, maria, child], true);
    expect(targets.map((t) => t.label)).toEqual(["Иван", "Петя"]);
    expect(targets.some((t) => t.id === "family")).toBe(false);
    expect(targets.some((t) => t.label === "Мария")).toBe(false);
  });

  it("admin without virtual members hides picker", () => {
    expect(shouldShowConsumptionMemberPicker([ivan, maria], true)).toBe(false);
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

  it("save enabled with selected meal regardless of family_id", () => {
    const drafts = buildDefaultConsumptionDrafts(meals);
    expect(hasSaveableConsumptionDrafts(drafts)).toBe(true);
    expect(
      canSaveConsumptionDrafts(drafts, { saving: false, loadingLogs: false }),
    ).toBe(true);
  });

  it("personal mode family_id is always null even with context family", () => {
    expect(resolveConsumptionFamilyId("personal", null, 5)).toBeNull();
    expect(resolveConsumptionFamilyId("family", 3, 5)).toBe(3);
    expect(resolveConsumptionFamilyId("family", null, 5)).toBe(5);
  });

  it("self target uses currentUserId when members list is empty", () => {
    expect(resolveConsumptionTargets("self", [], 42)).toEqual([
      { user_id: 42, family_member_id: null },
    ]);
  });

  it("personal payload uses null family_id", () => {
    const drafts = buildDefaultConsumptionDrafts(meals);
    const entries = buildConsumptionSaveEntries(
      meals,
      drafts,
      [{ user_id: 10, family_member_id: null }],
    );
    const payload = buildPersonalConsumptionPayload(
      {
        familyId: null,
        menuSelectionId: 123,
        dayIndex: 1,
        plannedDate: "2026-06-14",
      },
      entries,
    );
    expect(payload.family_id).toBeNull();
    expect(payload.entries[0]).toMatchObject({
      user_id: 10,
      family_member_id: null,
    });
  });

  it("virtual member payload uses family_member_id only", () => {
    const members = [
      { id: 1, display_name: "Я", is_you: true, is_virtual: false, user_id: 10 },
      { id: 3, display_name: "Петя", is_you: false, is_virtual: true, user_id: null },
    ];
    const targets = resolveConsumptionTargets(3, members);
    expect(targets).toEqual([{ user_id: null, family_member_id: 3 }]);
  });

  it("family target is rejected", () => {
    const members = [
      { id: 1, display_name: "Я", is_you: true, is_virtual: false, user_id: 10 },
      { id: 2, display_name: "Мария", is_you: false, is_virtual: false, user_id: 11 },
    ];
    expect(resolveConsumptionTargets("family", members)).toEqual([]);
  });

  it("footer hint for personal mode", () => {
    expect(consumptionSaveFooterHint(null, false, "self")).toBe(
      MEAL_CONSUMPTION_PERSONAL_SAVE_HINT,
    );
    expect(consumptionSaveFooterHint(null, false, "self")).not.toContain(
      MEAL_CONSUMPTION_SAVE_DISABLED_HINT,
    );
  });

  it("footer hint for admin virtual target", () => {
    expect(consumptionSaveFooterHint(1, true, 3)).toBe(
      MEAL_CONSUMPTION_VIRTUAL_MEMBER_SAVE_HINT,
    );
  });

  it("uses Russian portion labels", () => {
    expect(MEAL_CONSUMPTION_PORTION_OPTIONS.map((o) => o.label)).toEqual([
      "0,5",
      "1",
      "1,5",
      "2",
    ]);
  });

  it("self target does not set family_member_id", () => {
    const members = [
      { id: 1, display_name: "Я", is_you: true, is_virtual: false, user_id: 10 },
    ];
    expect(resolveConsumptionTargets("self", members)).toEqual([
      { user_id: 10, family_member_id: null },
    ]);
  });

  it("ate_out sends zero portion", () => {
    const drafts = buildDefaultConsumptionDrafts(meals);
    drafts[mealConsumptionKey("lunch", 0)].status = "ate_out";
    const entries = buildConsumptionSaveEntries(
      meals,
      drafts,
      [{ user_id: 10, family_member_id: null }],
    );
    expect(entries[0].portion_multiplier).toBe(0);
  });
});
