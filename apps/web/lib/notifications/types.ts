export type NotificationSettings = {
  buy_reminder_enabled: boolean;
  cook_reminder_enabled: boolean;
  buy_reminder_time: string;
  cook_reminder_time: string;
  timezone: string;
  updated_at: string | null;
};

export type NotificationSettingsUpdate = Partial<
  Pick<
    NotificationSettings,
    | "buy_reminder_enabled"
    | "cook_reminder_enabled"
    | "buy_reminder_time"
    | "cook_reminder_time"
    | "timezone"
  >
>;
