export type EventStatus = "DRAFT" | "OPEN" | "PLANNING" | "READY" | "ACTIVE" | "COMPLETED" | "CANCELLED";
export type EventFoodState = "NOT_PROVIDED" | "UNKNOWN" | "KNOWN_NONE" | "KNOWN_PRESENT";

export type EventParticipant = {
  participant_id: string;
  person_id: string | null;
  participant_kind: "ORGANIZER" | "PERSON" | "GUEST" | "DEPENDENT";
  display_name: string;
  age_group: "ADULT" | "CHILD" | "UNKNOWN";
  attendance_status: "PENDING" | "ACCEPTED" | "DECLINED";
  food_profile: { knowledge_state: EventFoodState; restrictions: Array<Record<string, unknown>> };
};

export type EventReadModel = {
  event_id: string;
  organizer_person_id: string;
  household_id: string | null;
  title: string;
  event_type: string;
  starts_at: string;
  ends_at: string | null;
  collaboration_mode: string;
  status: EventStatus;
  version: number;
  headcount: { expected: number; confirmed: number };
  food_profile_completeness: { accepted: number; known: number; state: "COMPLETE" | "INCOMPLETE" };
  participants: EventParticipant[];
};

export type EventCollection = { items: EventReadModel[] };
export type EventMenu = { event_id: string; revision: { revision_id: string; revision_number: number; lifecycle_status: string } | null; items: Array<{ menu_item_id: string; slot_key: string; state: "ASSIGNED" | "EMPTY"; recipe_version_id: string | null; servings: number | null; safety_state: "SAFE" | "BLOCK" | "ESCALATE" | "WARN" | "UNKNOWN" }> };
export type EventShopping = { event_id: string; shopping_list_id: string | null; items: Array<{ demand_id: string; display_text: string; quantity: number | null; unit: string | null; uncertainty: "UNKNOWN" | "KNOWN"; state: "NEEDED" | "CHECKED" | "PURCHASED"; source_kind?: string }> };
export type EventInvitation = { invitation_id: string; status: string; token: string | null; invitation_url: string | null; expires_at?: string | null; retry?: boolean };
