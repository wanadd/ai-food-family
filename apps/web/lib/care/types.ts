export type CareLevel = "minimal" | "standard" | "active";

export type CareNotificationType =
  | "water"
  | "protein"
  | "menu"
  | "shopping"
  | "pantry"
  | "progress"
  | "family"
  | "pro";

export type CareSettings = {
  water_enabled: boolean;
  protein_enabled: boolean;
  menu_enabled: boolean;
  shopping_enabled: boolean;
  pantry_enabled: boolean;
  progress_enabled: boolean;
  family_enabled: boolean;
  pro_enabled: boolean;
  care_level: CareLevel;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  timezone: string | null;
  has_pro_plan: boolean;
  updated_at: string | null;
};

export type CareSettingsUpdate = Partial<
  Omit<CareSettings, "has_pro_plan" | "updated_at">
>;

export type CareNotification = {
  id: number;
  type: string;
  title: string;
  message: string;
  status: string;
  sent_at: string | null;
  created_at: string;
};

export type TestCareResponse = {
  ok: boolean;
  message: string;
  notification_id: number | null;
};
