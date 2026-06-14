export const MENU_TODAY_MARK_CONSUMPTION_BUTTON = "Отметить съеденное";

export const MEAL_CONSUMPTION_SHEET_TITLE = "Что вы съели?";
export const MEAL_CONSUMPTION_SHEET_SUBTITLE =
  "Отметьте блюда и порции для себя или членов семьи";

export const MEAL_CONSUMPTION_MEMBER_PROMPT = "Кого отмечаем?";

export const MEAL_CONSUMPTION_SAVE_BUTTON_LABEL = "Сохранить отметки";

export const MEAL_CONSUMPTION_SAVE_DISABLED_HINT =
  "Сохранение будет доступно после настройки семейного учёта";

/** Must not appear in the consumption marking sheet. */
export const MEAL_CONSUMPTION_FORBIDDEN_PHRASES = [
  "Итог дня",
  "Результат дня",
  "Что приготовили?",
  "План на день и КБЖУ",
  "Показать итог дня",
] as const;

export const MEAL_CONSUMPTION_PORTION_OPTIONS = [0.5, 1, 1.5, 2] as const;

export type MealConsumptionStatus = "eaten" | "skipped" | "ate_out";

export const MEAL_CONSUMPTION_STATUS_OPTIONS: ReadonlyArray<{
  id: MealConsumptionStatus;
  label: string;
}> = [
  { id: "eaten", label: "Съел" },
  { id: "skipped", label: "Не ел" },
  { id: "ate_out", label: "Ел вне дома" },
];

export type ConsumptionTargetId = "self" | "family" | number;

export function formatConsumptionPortion(value: number): string {
  if (value === 0.5) {
    return "½";
  }
  return String(value);
}

type MemberPickerInput = {
  id: number;
  display_name: string;
  is_you: boolean;
};

/** Who can be marked in the consumption sheet (UI only). */
export function buildConsumptionMemberTargets(
  members: MemberPickerInput[],
  isAdmin: boolean,
): Array<{ id: ConsumptionTargetId; label: string }> {
  if (!isAdmin) {
    const self = members.find((m) => m.is_you);
    return [{ id: "self", label: self?.display_name?.trim() || "Я" }];
  }

  const targets: Array<{ id: ConsumptionTargetId; label: string }> = [];
  const self = members.find((m) => m.is_you);
  if (self) {
    targets.push({ id: "self", label: "Я" });
  }
  for (const member of members) {
    if (member.is_you) {
      continue;
    }
    targets.push({ id: member.id, label: member.display_name });
  }
  targets.push({ id: "family", label: "Вся семья" });
  return targets;
}

export function shouldShowConsumptionMemberPicker(
  members: MemberPickerInput[],
  isAdmin: boolean,
): boolean {
  return buildConsumptionMemberTargets(members, isAdmin).length > 1;
}
