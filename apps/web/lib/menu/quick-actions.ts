import type { QuickActionId } from "@/lib/menu/overview-api";

export type QuickActionMeta = {
  id: QuickActionId;
  label: string;
  description: string;
  /**
   * Backend cost key in SubscriptionOverview.ama_costs. If unset, the
   * action is assumed free or server-decided and we show
   * «может потребовать Амы».
   */
  costKey?: string;
};

/**
 * Быстрые действия над активным меню. Общий источник для раздела «Меню»
 * (MenuHub) и для домашнего AI-хаба (PlanAmHome), чтобы не дублировать
 * метаданные и тексты подтверждений.
 */
export const QUICK_ACTIONS: QuickActionMeta[] = [
  {
    id: "cheaper",
    label: "Сделать дешевле",
    description:
      "ПланАм пересоберёт меню с акцентом на экономные блюда. Активный план изменится, список покупок пересчитается.",
  },
  {
    id: "more_pantry",
    label: "Использовать запасы",
    description:
      "ПланАм постарается использовать продукты, которые уже есть в запасах, и обновит список покупок.",
  },
  {
    id: "more_protein",
    label: "Больше белка",
    description:
      "ПланАм увеличит долю белковых блюд в плане. Покупки обновятся под новые ингредиенты.",
  },
  {
    id: "less_cooking_time",
    label: "Меньше времени на готовку",
    description:
      "ПланАм заменит длительные рецепты на более быстрые. Активный план и покупки обновятся.",
  },
  {
    id: "replace_dish",
    label: "Заменить блюдо",
    description:
      "Выберите блюдо в активном плане — ПланАм предложит альтернативу с учётом ваших ограничений.",
    costKey: "menu_replace_dish",
  },
];
