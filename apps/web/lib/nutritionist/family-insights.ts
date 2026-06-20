import type { Family, FamilyMember } from "@/lib/family/types";

export type FamilyMemberInsight = {
  name: string;
  line: string;
};

function insightForMember(member: FamilyMember): string {
  if (!member.nutrition_profile_complete) {
    return "можно дополнить профиль питания";
  }

  const goal = member.nutrition_goal_label?.toLowerCase() ?? "";

  if (member.is_virtual && member.virtual_kind === "child") {
    return "питание подобрано по возрасту";
  }

  if (member.is_virtual && member.virtual_kind === "elder") {
    return "учтены ограничения";
  }

  if (goal.includes("похуд")) {
    return "идёт по плану";
  }

  if (goal.includes("набор") || goal.includes("спорт")) {
    return "можно добавить белка";
  }

  const vn = member.virtual_nutrition;
  if (vn?.disliked_foods?.toLowerCase().includes("рыб")) {
    return "избегает рыбу — ПланАм учтёт";
  }

  if (vn && (vn.allergies?.length ?? 0) > 1) {
    return "учтены аллергии";
  }

  return "идёт по плану";
}

export function buildFamilyMemberInsights(
  family: Family,
): FamilyMemberInsight[] {
  return (family.members ?? [])
    .filter((m) => !m.is_you)
    .map((member) => ({
      name: member.display_name,
      line: insightForMember(member),
    }));
}
