"use client";

import {
  displayScopeLabel,
  hasEntitlement,
  selectHousehold,
  type EffectiveEntitlement,
  type HouseholdOption,
  type HouseholdScope,
  type PersonOption,
} from "@/lib/v2/household-scope";

type Props = {
  households: HouseholdOption[];
  people?: PersonOption[];
  scope: HouseholdScope;
  entitlements?: EffectiveEntitlement[];
  loading?: boolean;
  forbidden?: boolean;
  error?: string | null;
  onScopeChange: (scope: HouseholdScope) => void;
};

export function HouseholdScopeV2({
  households,
  people = [],
  scope,
  entitlements = [],
  loading = false,
  forbidden = false,
  error = null,
  onScopeChange,
}: Props) {
  if (loading) {
    return <div className="min-h-12 animate-pulse rounded-xl bg-pa-surface" aria-label="Загрузка контекста" />;
  }
  if (forbidden) {
    return <p role="alert" className="text-sm text-pa-muted">Нет доступа к выбранному контексту.</p>;
  }
  if (error) {
    return <p role="alert" className="text-sm text-pa-muted">Не удалось загрузить контекст.</p>;
  }

  const selected = selectHousehold(households, scope.householdId);
  const currentPerson = people.find((person) => person.person_id === scope.personId);

  return (
    <section aria-label="Контекст PLANAM" className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-pa-muted" htmlFor="v2-household-scope">
        {displayScopeLabel(households, scope)}
      </label>
      <select
        id="v2-household-scope"
        value={selected?.household_id ?? ""}
        onChange={(event) => onScopeChange({ householdId: event.target.value || null, personId: null })}
        className="min-h-11 w-full rounded-xl border border-pa-border bg-pa-surface px-3 text-sm text-pa-foreground"
      >
        <option value="">Личный режим</option>
        {households.map((household) => (
          <option key={household.household_id} value={household.household_id}>
            {household.name || "Семья"}
          </option>
        ))}
      </select>
      {selected && people.length > 0 ? (
        <select
          aria-label="Участник"
          value={currentPerson?.person_id ?? ""}
          onChange={(event) => onScopeChange({ householdId: selected.household_id, personId: event.target.value || null })}
          className="min-h-11 w-full rounded-xl border border-pa-border bg-pa-surface px-3 text-sm text-pa-foreground"
        >
          <option value="">Мой профиль</option>
          {people.map((person) => (
            <option key={person.person_id} value={person.person_id}>
              {person.display_name || "Участник"}
            </option>
          ))}
        </select>
      ) : null}
      {entitlements.length > 0 && !hasEntitlement(entitlements, "core.household.manage") ? (
        <p className="text-xs text-pa-muted">Управление участниками доступно по разрешению household.</p>
      ) : null}
    </section>
  );
}
