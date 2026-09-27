export type FoodSafetyState = "BLOCK" | "ESCALATE" | "UNKNOWN" | "WARN" | "SAFE";

export type FoodSafetyDecision = {
  decision: FoodSafetyState;
  person_id: string;
  food_identity_id: number | null;
  reason_codes: string[];
  evidence_claim_ids: string[];
};

export const FOOD_SAFETY_COPY: Record<FoodSafetyState, string> = {
  BLOCK: "Нельзя использовать для этого человека",
  ESCALATE: "Нужна дополнительная проверка",
  UNKNOWN: "Недостаточно данных для безопасного решения",
  WARN: "Есть предупреждение, проверьте детали",
  SAFE: "Разрешено по имеющимся данным",
};

/** The client renders the server decision; it never derives or downgrades it. */
export function foodSafetyPresentation(decision: FoodSafetyDecision) {
  return {
    state: decision.decision,
    label: FOOD_SAFETY_COPY[decision.decision],
    personId: decision.person_id,
    reasons: decision.reason_codes,
  };
}
