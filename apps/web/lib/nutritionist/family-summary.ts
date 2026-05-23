import type { Family } from "@/lib/family/types";

export type FamilyNutritionSummary = {
  memberCount: number;
  profilesComplete: number;
  goalLines: string[];
};

export function buildFamilySummary(family: Family): FamilyNutritionSummary {
  const members = family.members ?? [];
  const profilesComplete = members.filter(
    (m) => m.nutrition_profile_complete,
  ).length;

  const goalLines = members
    .map((m) => {
      const goal = m.nutrition_goal_label;
      if (!goal) return null;
      return `${m.display_name}: ${goal}`;
    })
    .filter((line): line is string => Boolean(line))
    .slice(0, 4);

  return {
    memberCount: family.members_count ?? members.length,
    profilesComplete,
    goalLines,
  };
}
