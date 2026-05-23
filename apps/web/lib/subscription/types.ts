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
};
