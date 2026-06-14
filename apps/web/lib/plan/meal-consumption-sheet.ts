export const MENU_TODAY_MARK_CONSUMPTION_BUTTON = "Отметить съеденное";

export const MEAL_CONSUMPTION_SHEET_TITLE = "Что вы съели?";
export const MEAL_CONSUMPTION_SHEET_SUBTITLE =
  "Отметьте блюда и порции для себя или членов семьи";

export const MEAL_CONSUMPTION_MEMBER_PROMPT = "Кого отмечаем?";

export const MEAL_CONSUMPTION_SAVE_BUTTON_LABEL = "Сохранить отметки";

export const MEAL_CONSUMPTION_SAVE_DISABLED_HINT =
  "Сохранение будет доступно после настройки семейного учёта";

export const MEAL_CONSUMPTION_SAVING_LABEL = "Сохраняем...";

export const MEAL_CONSUMPTION_SAVED_TOAST = "Отметки сохранены";

export const MEAL_CONSUMPTION_SAVE_ERROR =
  "Не удалось сохранить отметки. Попробуйте ещё раз.";

export const MEAL_CONSUMPTION_PERMISSION_ERROR =
  "Нет прав отмечать питание за этого участника";

/** Must not appear in the consumption marking sheet. */
export const MEAL_CONSUMPTION_FORBIDDEN_PHRASES = [
  "Итог дня",
  "Результат дня",
  "Что приготовили?",
  "План на день и КБЖУ",
  "Показать итог дня",
] as const;

export const MEAL_CONSUMPTION_PORTION_OPTIONS = [
  { value: 0.5, label: "0,5" },
  { value: 1, label: "1" },
  { value: 1.5, label: "1,5" },
  { value: 2, label: "2" },
] as const;

export type MealConsumptionPortionValue =
  (typeof MEAL_CONSUMPTION_PORTION_OPTIONS)[number]["value"];

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

export type ConsumptionMemberRef = {
  user_id: number | null;
  family_member_id: number | null;
};

type MemberForResolve = MemberPickerInput & {
  user_id?: number | null;
};

export function resolveConsumptionTargets(
  targetId: ConsumptionTargetId,
  members: MemberForResolve[],
): ConsumptionMemberRef[] {
  if (targetId === "family") {
    return members.map((m) => ({
      user_id: m.user_id ?? null,
      family_member_id: m.id,
    }));
  }
  if (targetId === "self") {
    const self = members.find((m) => m.is_you);
    if (!self) {
      return [{ user_id: null, family_member_id: null }];
    }
    return [
      {
        user_id: self.user_id ?? null,
        family_member_id: self.id,
      },
    ];
  }
  const member = members.find((m) => m.id === targetId);
  if (!member) {
    return [];
  }
  return [
    {
      user_id: member.user_id ?? null,
      family_member_id: member.id,
    },
  ];
}

export type ConsumptionMealInput = {
  meal_type: string;
  recipe_id?: number | null;
  recipe_title: string;
  mealIndex: number;
};

export type ConsumptionDraft = {
  included: boolean;
  portion: MealConsumptionPortionValue;
  status: MealConsumptionStatus;
};

export function mealConsumptionKey(mealType: string, mealIndex: number): string {
  return `${mealType}-${mealIndex}`;
}

export function buildDefaultConsumptionDrafts(
  meals: Array<{ meal_type: string; mealIndex: number }>,
): Record<string, ConsumptionDraft> {
  const drafts: Record<string, ConsumptionDraft> = {};
  for (const meal of meals) {
    drafts[mealConsumptionKey(meal.meal_type, meal.mealIndex)] = {
      included: true,
      portion: 1,
      status: "eaten",
    };
  }
  return drafts;
}

export function hasSaveableConsumptionDrafts(
  drafts: Record<string, ConsumptionDraft>,
): boolean {
  return Object.values(drafts).some((d) => d.included);
}

export function buildConsumptionSaveEntries(
  meals: ConsumptionMealInput[],
  drafts: Record<string, ConsumptionDraft>,
  targets: ConsumptionMemberRef[],
): Array<{
  user_id?: number | null;
  family_member_id?: number | null;
  meal_type: string;
  recipe_id?: number | null;
  recipe_title: string;
  status: MealConsumptionStatus;
  portion_multiplier: number;
}> {
  const entries: Array<{
    user_id?: number | null;
    family_member_id?: number | null;
    meal_type: string;
    recipe_id?: number | null;
    recipe_title: string;
    status: MealConsumptionStatus;
    portion_multiplier: number;
  }> = [];

  for (const target of targets) {
    for (const meal of meals) {
      const key = mealConsumptionKey(meal.meal_type, meal.mealIndex);
      const draft = drafts[key];
      if (!draft?.included) {
        continue;
      }
      const portion =
        draft.status === "ate_out" ? 0 : draft.portion;
      entries.push({
        user_id: target.user_id,
        family_member_id: target.family_member_id,
        meal_type: meal.meal_type,
        recipe_id: meal.recipe_id ?? null,
        recipe_title: meal.recipe_title,
        status: draft.status,
        portion_multiplier: portion,
      });
    }
  }

  return entries;
}

export type ConsumptionLogLike = {
  user_id: number | null;
  family_member_id?: number | null;
  meal_type: string | null;
  recipe_id: number | null;
  status: string;
  portion_multiplier: number;
};

export function applyConsumptionLogsToDrafts(
  meals: ConsumptionMealInput[],
  logs: ConsumptionLogLike[],
  target: ConsumptionMemberRef,
  defaults: ConsumptionDraft = { included: true, portion: 1, status: "eaten" },
): Record<string, ConsumptionDraft> {
  const drafts: Record<string, ConsumptionDraft> = {};
  for (const meal of meals) {
    drafts[mealConsumptionKey(meal.meal_type, meal.mealIndex)] = { ...defaults };
  }

  for (const log of logs) {
    const matchesTarget =
      (target.user_id != null && log.user_id === target.user_id) ||
      (target.family_member_id != null &&
        log.family_member_id === target.family_member_id);
    if (!matchesTarget || !log.meal_type) {
      continue;
    }
    const meal = meals.find(
      (m) =>
        m.meal_type === log.meal_type &&
        (log.recipe_id == null || m.recipe_id === log.recipe_id),
    );
    if (!meal) {
      continue;
    }
    const key = mealConsumptionKey(meal.meal_type, meal.mealIndex);
    const status = log.status as MealConsumptionStatus;
    const portion =
      status === "ate_out"
        ? 1
        : (MEAL_CONSUMPTION_PORTION_OPTIONS.find((o) => o.value === log.portion_multiplier)
            ?.value ?? 1);
    drafts[key] = {
      included: true,
      portion,
      status: status === "unknown" ? "eaten" : status,
    };
  }

  return drafts;
}
