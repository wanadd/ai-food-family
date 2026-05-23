export type SubscriptionPlanInfo = {
  code: string;
  name: string;
  price_rub: number;
  max_profiles: number;
  monthly_menu_generations: number | null;
  monthly_ams: number;
  features: Record<string, boolean | string>;
  is_current: boolean;
};

export type AmaTransactionItem = {
  id: number;
  user_name: string;
  amount: number;
  reason: string;
  reason_label: string;
  created_at: string;
};

export type SubscriptionOverview = {
  plan_code: string;
  plan_name: string;
  status: string;
  price_rub: number;
  trial_ends_at: string | null;
  current_period_ends_at: string | null;
  menu_generations_used: number;
  menu_generations_limit: number | null;
  menu_generations_remaining: number | null;
  ama_balance: number;
  ai_actions_enabled: boolean;
  trial_days_left: number | null;
  plans: SubscriptionPlanInfo[];
  ama_costs: Record<string, number>;
  is_family_billing?: boolean;
  family_name?: string | null;
  is_family_admin?: boolean;
  can_spend_ama?: boolean;
  ama_transactions?: AmaTransactionItem[];
};
