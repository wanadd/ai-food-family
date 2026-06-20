export type TariffSlug =
  | "start_trial"
  | "personal_plus"
  | "pair"
  | "family"
  | "family_pro";

export type CapabilityKey =
  | "ai_inventory_menu"
  | "ai_leftovers_suggestions"
  | "health_extended"
  | "health_sport_mode"
  | "strict_diet_mode"
  | "external_food_ai_parse"
  | "voice_food_log"
  | "photo_food_log"
  | "ocr_receipts"
  | "family_profiles_limit"
  | "monthly_menu_depth";

const TARIFF_CAPABILITIES: Record<
  TariffSlug,
  Record<string, boolean | number>
> = {
  start_trial: {
    family_profiles_limit: 1,
    monthly_menu_depth: 7,
    ai_inventory_menu: false,
    ai_leftovers_suggestions: false,
    health_extended: false,
    health_sport_mode: false,
    strict_diet_mode: false,
    external_food_ai_parse: false,
    voice_food_log: false,
    photo_food_log: false,
    ocr_receipts: false,
  },
  personal_plus: {
    family_profiles_limit: 1,
    monthly_menu_depth: 30,
    ai_inventory_menu: true,
    ai_leftovers_suggestions: true,
    health_extended: true,
    health_sport_mode: false,
    strict_diet_mode: false,
    external_food_ai_parse: true,
    voice_food_log: true,
    photo_food_log: true,
    ocr_receipts: true,
  },
  pair: {
    family_profiles_limit: 3,
    monthly_menu_depth: 30,
    ai_inventory_menu: true,
    ai_leftovers_suggestions: true,
    health_extended: true,
    health_sport_mode: false,
    strict_diet_mode: false,
    external_food_ai_parse: true,
    voice_food_log: true,
    photo_food_log: true,
    ocr_receipts: true,
  },
  family: {
    family_profiles_limit: 5,
    monthly_menu_depth: 30,
    ai_inventory_menu: true,
    ai_leftovers_suggestions: true,
    health_extended: true,
    health_sport_mode: false,
    strict_diet_mode: false,
    external_food_ai_parse: true,
    voice_food_log: true,
    photo_food_log: true,
    ocr_receipts: true,
  },
  family_pro: {
    family_profiles_limit: 7,
    monthly_menu_depth: 30,
    ai_inventory_menu: true,
    ai_leftovers_suggestions: true,
    health_extended: true,
    health_sport_mode: true,
    strict_diet_mode: true,
    external_food_ai_parse: true,
    voice_food_log: true,
    photo_food_log: true,
    ocr_receipts: true,
  },
};

export function hasCapability(
  tariff: TariffSlug,
  capability: CapabilityKey,
): boolean {
  const value = TARIFF_CAPABILITIES[tariff]?.[capability];
  return value === true;
}

export function profileLimitForTariff(tariff: TariffSlug): number {
  const value = TARIFF_CAPABILITIES[tariff]?.family_profiles_limit;
  return typeof value === "number" ? value : 1;
}
