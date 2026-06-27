export type CareModeOption = "off" | "minimal" | "normal" | "active";

export type NotificationTypeOption =
  | "menu"
  | "shopping"
  | "pantry"
  | "water"
  | "health"
  | "family";

export type NotificationSettings = {
  notifications_onboarded: boolean;
  care_mode: CareModeOption;
  enabled_notification_types: NotificationTypeOption[];
  buy_reminder_enabled: boolean;
  cook_reminder_enabled: boolean;
  cook_breakfast_enabled: boolean;
  cook_lunch_enabled: boolean;
  cook_dinner_enabled: boolean;
  buy_reminder_time: string;
  cook_reminder_time: string;
  cook_breakfast_time: string;
  cook_lunch_time: string;
  cook_dinner_time: string;
  timezone: string;
  updated_at: string | null;
};

export type NotificationSettingsUpdate = Partial<
  Pick<
    NotificationSettings,
    | "buy_reminder_enabled"
    | "cook_reminder_enabled"
    | "cook_breakfast_enabled"
    | "cook_lunch_enabled"
    | "cook_dinner_enabled"
    | "buy_reminder_time"
    | "cook_reminder_time"
    | "cook_breakfast_time"
    | "cook_lunch_time"
    | "cook_dinner_time"
    | "timezone"
  >
>;

export type NotificationOnboardingPayload = {
  care_mode: CareModeOption;
  enabled_notification_types: NotificationTypeOption[];
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  timezone?: string;
};
