/**
 * SSOT for retail plan UX labels (Старт · Пара · Семья · PRO).
 * Server codes: personal · shared · family · pro · trial
 * @see docs/PLANAM_2026_PRODUCT_BLUEPRINT.md §8
 */

export type RetailPlanCode = "personal" | "shared" | "family" | "pro";

export type PlanCatalogEntry = {
  code: RetailPlanCode;
  /** Product name in UI (Blueprint ladder). */
  displayName: string;
  audience: string;
  tagline: string;
  benefits: string[];
  recommendedForWho?: ("solo" | "couple" | "family")[];
  isPro?: boolean;
};

/** Order on subscription hub (excludes trial). */
export const RETAIL_PLAN_ORDER: RetailPlanCode[] = [
  "personal",
  "shared",
  "family",
  "pro",
];

export const PLAN_CATALOG_2026: Record<RetailPlanCode, PlanCatalogEntry> = {
  personal: {
    code: "personal",
    displayName: "Старт",
    audience: "Один человек",
    tagline: "Полный цикл питания для себя",
    benefits: [
      "Меню на неделю с фото блюд",
      "Список покупок и запасы",
      "Базовый нутрициолог и советы",
      "Амы на AI-действия каждый месяц",
    ],
    recommendedForWho: ["solo"],
  },
  shared: {
    code: "shared",
    displayName: "Пара",
    audience: "Двое",
    tagline: "Общий план и покупки вдвоём",
    benefits: [
      "До 3 профилей",
      "Семейный режим и общие списки",
      "Меню с учётом двоих",
      "Больше генераций и Амов",
    ],
    recommendedForWho: ["couple"],
  },
  family: {
    code: "family",
    displayName: "Семья",
    audience: "Дом и дети",
    tagline: "Питание всего дома в одном месте",
    benefits: [
      "До 6 профилей",
      "Виртуальные участники без Telegram",
      "Роли и семейные уведомления",
      "Максимум генераций в линейке",
    ],
    recommendedForWho: ["family"],
  },
  pro: {
    code: "pro",
    displayName: "PRO",
    audience: "Максимум возможностей",
    tagline: "Прогресс, спорт и расширенный AI",
    benefits: [
      "Безлимитные генерации меню",
      "КБЖУ, цели и прогресс веса",
      "Расширенный нутрициолог",
      "OCR чеков, голос, AI-забота",
    ],
    isPro: true,
  },
};

const CODE_ALIASES: Record<string, RetailPlanCode | "trial"> = {
  personal: "personal",
  shared: "shared",
  family: "family",
  pro: "pro",
  trial: "trial",
};

export function isRetailPlanCode(code: string): code is RetailPlanCode {
  return code in PLAN_CATALOG_2026;
}

export function planDisplayName(
  planCode: string,
  apiName?: string | null,
): string {
  if (planCode === "start" || planCode === "trial" || planCode === "free" || planCode === "demo") {
    return "Старт";
  }
  const key = CODE_ALIASES[planCode];
  if (key && key !== "trial" && key in PLAN_CATALOG_2026) {
    return PLAN_CATALOG_2026[key].displayName;
  }
  return apiName?.trim() || planCode;
}

export function catalogEntryForCode(
  planCode: string,
): PlanCatalogEntry | null {
  if (isRetailPlanCode(planCode)) {
    return PLAN_CATALOG_2026[planCode];
  }
  return null;
}

export function sortRetailPlans<T extends { code: string }>(plans: T[]): T[] {
  const order = new Map(RETAIL_PLAN_ORDER.map((c, i) => [c, i]));
  return [...plans].sort(
    (a, b) => (order.get(a.code as RetailPlanCode) ?? 99) - (order.get(b.code as RetailPlanCode) ?? 99),
  );
}

export function filterRetailPlans<T extends { code: string }>(plans: T[]): T[] {
  return plans.filter((p) => isRetailPlanCode(p.code));
}

export function planTierRank(planCode: string): number {
  const idx = RETAIL_PLAN_ORDER.indexOf(planCode as RetailPlanCode);
  return idx >= 0 ? idx : -1;
}

export function isDowngradePlan(currentCode: string, targetCode: string): boolean {
  const current = planTierRank(currentCode);
  const target = planTierRank(targetCode);
  if (current < 0 || target < 0) return false;
  return target < current;
}
