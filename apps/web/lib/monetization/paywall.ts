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
          "На балансе не хватает Амов для этого действия. Выберите тариф с большим пакетом или дождитесь пополнения по подписке.",
        primaryCta: "Выбрать тариф",
        secondaryCta: "Не сейчас",
        amsLinkLabel: "Баланс и история",
      };
    case "low_amas":
      return {
        title: "Амов осталось мало",
        description:
          "Чтобы спокойно пользоваться AI — замены, вопросы, разбор чека — посмотрите тарифы или баланс.",
        primaryCta: "Тарифы",
        secondaryCta: "Понятно",
        amsLinkLabel: "Сколько осталось",
      };
    case "pro_feature":
      return {
        title: featureLabel
          ? `${featureLabel} — в PRO`
          : "Доступно в PRO",
        description:
          "Прогресс, расширенные метрики и безлимитные генерации — в тарифе PRO. Остальной план остаётся с вами.",
        primaryCta: "Узнать про PRO",
        secondaryCta: "Позже",
      };
    case "trial_ended":
      return {
        title: "Пробный период завершён",
        description:
          "Сохраните ритм: меню, покупки и советы продолжат работать на выбранном тарифе.",
        primaryCta: "Сохранить ритм",
        secondaryCta: "Позже",
      };
    case "trial_ending":
      return {
        title: "Скоро конец пробного периода",
        description:
          "3 дня знакомства с ПланАм — без давления. Выберите тариф, когда будете готовы.",
        primaryCta: "Посмотреть тарифы",
        secondaryCta: "Продолжить пробный",
      };
    default:
      return {
        title: "Нужен тариф",
        description: "Выберите подходящий план в аккаунте.",
        primaryCta: "Тарифы",
        secondaryCta: "Закрыть",
      };
  }
}
