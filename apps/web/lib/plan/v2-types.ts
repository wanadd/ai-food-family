export type PlanningOwnerScope = "PERSON" | "HOUSEHOLD";
export type PlanningSlotState = "ASSIGNED" | "EMPTY" | "FREE" | "CANCELLED";

export type PlanningSlot = {
  slot_id: string;
  slot_key: string;
  date: string;
  meal_type: string;
  state: PlanningSlotState;
  recipe_version_id: string | null;
  safety_state: "SAFE" | "WARN" | "UNKNOWN" | "ESCALATE" | null;
  manual: boolean;
  origin: string | null;
  participants: Array<{ person_id: string; state: string }>;
  portions: Array<{ person_id: string; value: number | null; unit: string | null; source: string }>;
};

export type PlanningReadModel = {
  plan_id: string;
  owner_scope: PlanningOwnerScope;
  person_id: string | null;
  household_id: string | null;
  active_revision: {
    revision_id: string;
    number: number;
    status: string;
    source: string;
    safety: { states?: string[]; aggregate?: string };
  } | null;
  slots: PlanningSlot[];
};

export type PlanningSlotInput = {
  slot_key: string;
  planned_date: string;
  meal_type: string;
  state?: PlanningSlotState;
  recipe_version_id?: string | null;
  participants?: Array<{ person_id: string; state?: string }>;
  portions?: Array<{ person_id: string; value?: number | null; unit?: string | null; source?: string }>;
};
