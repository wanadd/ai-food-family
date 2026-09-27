export type HouseholdOption = {
  household_id: string;
  name: string | null;
  status: string;
  role: string | null;
};

export type PersonOption = {
  person_id: string;
  display_name: string | null;
  membership_id?: string;
  role?: string | null;
};

export type EffectiveEntitlement = {
  capability: string;
  allowed: boolean;
  limit: number | null;
  used: number;
  remaining: number | null;
  source: string | null;
};

export type HouseholdScope = {
  householdId: string | null;
  personId: string | null;
};

export function selectHousehold(
  households: HouseholdOption[],
  requestedId: string | null | undefined,
): HouseholdOption | null {
  if (requestedId) {
    const requested = households.find((household) => household.household_id === requestedId);
    if (requested) return requested;
  }
  return households[0] ?? null;
}

export function recoverScope(
  households: HouseholdOption[],
  requested: HouseholdScope,
): HouseholdScope {
  const household = selectHousehold(households, requested.householdId);
  return {
    householdId: household?.household_id ?? null,
    personId: requested.personId ?? null,
  };
}

export function hasEntitlement(
  entitlements: EffectiveEntitlement[],
  capability: string,
): boolean {
  return entitlements.some((item) => item.capability === capability && item.allowed);
}

export function displayScopeLabel(
  households: HouseholdOption[],
  scope: HouseholdScope,
): string {
  if (!scope.householdId) return "Личный режим";
  return selectHousehold(households, scope.householdId)?.name ?? "Семья";
}
