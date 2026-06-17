/** Audit persona slugs — must match backend AUDIT_PERSONA_TELEGRAM_IDS. */

export const AUDIT_PERSONA_STORAGE_KEY = "planam.audit.persona";

export const AUDIT_PERSONAS = [
  "audit_new_user",
  "audit_personal_day5",
  "audit_family_admin",
  "audit_family_adult",
  "audit_family_child",
  "audit_athlete",
  "audit_strict_diet",
  "audit_healthy_eating",
  "audit_start_trial",
  "audit_personal_plus",
  "audit_pair",
  "audit_family",
  "audit_family_pro",
] as const;

export type AuditPersona = (typeof AUDIT_PERSONAS)[number];

export const DEFAULT_AUDIT_PERSONA: AuditPersona = "audit_personal_day5";

export const AUDIT_PERSONA_LABELS: Record<AuditPersona, string> = {
  audit_new_user: "Новый пользователь",
  audit_personal_day5: "Личный · день 5",
  audit_family_admin: "Семья · admin",
  audit_family_adult: "Семья · взрослый",
  audit_family_child: "Семья · ребёнок (virtual)",
  audit_athlete: "Спортсмен",
  audit_strict_diet: "Строгая диета",
  audit_healthy_eating: "Здоровое питание",
  audit_start_trial: "Тариф · Старт trial",
  audit_personal_plus: "Тариф · Личный Plus",
  audit_pair: "Тариф · Пара",
  audit_family: "Тариф · Семья",
  audit_family_pro: "Тариф · PRO",
};

export function isAuditPersona(value: string): value is AuditPersona {
  return (AUDIT_PERSONAS as readonly string[]).includes(value);
}
