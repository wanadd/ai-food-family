export type AdminSummary = {
  total_users: number;
  users_today: number;
  total_families: number;
  active_subscriptions: number;
  ams_used_total: number;
  ai_requests_total: number;
  ai_estimated_cost_usd: number;
  errors_last_24h: number;
};

export type AdminUserRow = {
  id: number;
  display_name: string;
  telegram_id: number;
  username: string | null;
  created_at: string;
  plan_code: string;
  plan_status: string;
  ama_balance: number;
  menu_count: number;
  last_activity_at: string;
};

export type AdminFamilyRow = {
  id: number;
  name: string;
  member_count: number;
  plan_code: string;
  admin_name: string;
  admin_user_id: number | null;
  created_at: string;
};

export type AdminSubscriptionRow = {
  id: number;
  user_id: number;
  user_name: string;
  telegram_id: number;
  plan_code: string;
  status: string;
  started_at: string;
  trial_ends_at: string | null;
  current_period_ends_at: string | null;
  menu_generations_used: number;
};

export type AdminAiUsageRow = {
  id: number;
  action_type: string;
  user_id: number;
  user_name: string;
  family_id: number | null;
  ams_spent: number;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  estimated_cost: number | null;
  created_at: string;
};

export type AdminBackupRow = {
  id: string;
  path: string;
  created_at: string;
  size_bytes: number;
  has_database: boolean;
  has_env: boolean;
};

export type AdminPlanOption = {
  code: string;
  name: string;
  price_rub: number;
  monthly_ams: number;
};

export type AdminGrantResponse = {
  user_id: number;
  message: string;
};
