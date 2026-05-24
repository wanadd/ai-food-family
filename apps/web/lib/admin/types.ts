export interface AdminSummary {
  total_users: number;
  users_today: number;
  active_today: number;
  active_7d: number;
  total_families: number;
  active_subscriptions: number;
  free_users: number;
  total_ams_balance: number;
  ams_used_total: number;
  ai_requests_total: number;
  ai_estimated_cost_usd: number;
  openai_cost_today_usd: number;
  openai_cost_month_usd: number;
  errors_last_24h: number;
}

export interface AdminUserRow {
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
  family_name?: string | null;
  is_blocked?: boolean;
  status?: string;
}

export interface AdminFamilyRow {
  id: number;
  name: string;
  member_count: number;
  plan_code: string;
  admin_name: string;
  admin_user_id: number | null;
  created_at: string;
  ama_balance?: number;
  openai_cost_usd?: number;
  is_blocked?: boolean;
}

export interface AdminSubscriptionRow {
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
}

export interface AdminAiUsageRow {
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
}

export interface AdminPlanOption {
  code: string;
  name: string;
  price_rub: number;
  monthly_ams: number;
}

export interface AdminGrantResponse {
  user_id?: number;
  family_id?: number;
  message: string;
}

export interface AdminBackupRow {
  id: string;
  path: string;
  created_at: string;
  size_bytes: number;
  has_database: boolean;
  has_env: boolean;
}

export interface AdminOpenAiStats {
  period: string;
  requests: number;
  openai_cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  ams_spent: number;
  menu_generations: number;
  avg_request_cost_usd: number;
  avg_menu_cost_usd: number;
  avg_user_cost_usd: number;
  avg_family_cost_usd: number;
  categories: {
    category: string;
    requests: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    openai_cost_usd: number;
    ams_spent: number;
    avg_cost_usd: number;
  }[];
}

export interface AdminAmsSummary {
  credited_total: number;
  debited_total: number;
  user_balance_total: number;
  family_balance_total: number;
  spent_today: number;
  spent_month: number;
}

export interface AdminAmaTransactionRow {
  id: number;
  created_at: string;
  user_id: number | null;
  family_id: number | null;
  amount: number;
  reason: string;
  type: string;
}

export interface AdminErrorRow {
  id: number;
  error_type: string;
  user_id: number | null;
  family_id: number | null;
  endpoint: string | null;
  message: string;
  status: number | null;
  created_at: string;
}

export type AdminTab =
  | "summary"
  | "users"
  | "families"
  | "subscriptions"
  | "ams";
