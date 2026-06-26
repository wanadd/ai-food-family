import type { RetailPlanCode } from "@/lib/monetization/plan-catalog-2026";

export type PaywallReason =
  | "no_amas"
  | "low_amas"
  | "pro_feature"
  | "trial_ended"
  | "trial_ending";

export type PaywallOpenOptions = {
  reason: PaywallReason;
  returnTo?: string;
  suggestedPlanCode?: RetailPlanCode;
  featureLabel?: string;
};

export type PaywallCopy = {
  title: string;
  description: string;
  primaryCta: string;
  secondaryCta: string;
  amsLinkLabel?: string;
};

export function paywallCopy(
  reason: PaywallReason,
  featureLabel?: string,
): PaywallCopy {
  switch (reason) {
    case "no_amas":
      return {
        title: "Нужны Амы",
        description:
          "На балансе не хватает Амов для этого действия. Тариф и баланс управляются администратором.",
        primaryCta: "Понятно",
        secondaryCta: "Закрыть",
        amsLinkLabel: "Баланс и история",
      };
    case "low_amas":
      return {
        title: "Амов осталось мало",
        description:
          "Чтобы спокойно пользоваться AI — замены, вопросы, разбор чека — обратитесь к администратору.",
        primaryCta: "Понятно",
        secondaryCta: "Закрыть",
        amsLinkLabel: "Сколько осталось",
      };
    case "pro_feature":
      return {
        title: featureLabel
          ? `${featureLabel} — в PRO`
          : "Доступно в PRO",
        description:
          "Расширенные метрики и безлимитные генерации доступны в тарифе PRO. Для смены тарифа обратитесь к администратору.",
        primaryCta: "Понятно",
        secondaryCta: "Позже",
      };
    case "trial_ended":
      return {
        title: "Пробный период завершён",
        description:
          "Доступ к расширенным функциям ограничен. Для продления обратитесь к администратору.",
        primaryCta: "Понятно",
        secondaryCta: "Закрыть",
      };
    case "trial_ending":
      return {
        title: "Скоро конец пробного периода",
        description:
          "Пробный доступ скоро закончится. Для продления тарифа обратитесь к администратору.",
        primaryCta: "Понятно",
        secondaryCta: "Продолжить",
      };
    default:
      return {
        title: "Доступ ограничен",
        description: "Тариф управляется администратором. Обратитесь в поддержку при необходимости.",
        primaryCta: "Понятно",
        secondaryCta: "Закрыть",
      };
  }
}
