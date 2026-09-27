export type W6Completeness = "COMPLETE" | "PARTIAL" | "UNKNOWN";

export type CookingSessionV2 = {
  cooking_session_id: string;
  household_id: string;
  recipe_version_id: string | null;
  plan_slot_id: string | null;
  state: "STARTED" | "COMPLETED" | "CANCELLED";
  prepared_food: { prepared_food_id: string; yield_quantity: number | null; yield_unit: string | null; yield_servings: number | null; state: string } | null;
};

export type ConsumptionEventV2 = {
  consumption_event_id: string;
  person_id: string;
  state: "CONFIRMED" | "CORRECTED" | "RETRACTED";
  portion_state: "KNOWN" | "UNKNOWN" | "ESTIMATED";
  items: Array<{ display_text: string | null; quantity: number | null; unit: string | null; nutrition: Record<string, unknown> }>;
};

export type HealthProjectionV2 = {
  projection_id: string;
  date: string;
  completeness: W6Completeness;
  planned: Record<string, unknown>;
  actual: Record<string, unknown>;
  deviation: Record<string, unknown>;
  safety_status: string;
};
