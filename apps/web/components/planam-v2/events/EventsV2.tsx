"use client";

import { useRouter } from "next/navigation";

import { V2Button, V2Card } from "@/components/planam-v2/ui/V2Primitives";

const EVENT_PREVIEWS = [
  {
    id: "kids-party",
    emoji: "🎂",
    title: "Детский праздник",
    caption: "Меню для гостей и сладкий стол",
  },
  {
    id: "guests",
    emoji: "✨",
    title: "Гости / праздник",
    caption: "Общий план и список покупок",
  },
  {
    id: "fasting",
    emoji: "🌿",
    title: "Постное меню",
    caption: "Сезонные блюда без запретных продуктов",
  },
  {
    id: "picnic",
    emoji: "🏕",
    title: "Дача / пикник",
    caption: "Простые блюда и перекусы",
  },
  {
    id: "sport-week",
    emoji: "💪",
    title: "Спорт-неделя / диета",
    caption: "КБЖУ и режим на 7 дней",
  },
];

export function EventsV2() {
  const router = useRouter();

  return (
    <div className="space-y-4 px-4 pb-6 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <header>
        <h1 className="pa26-page-title">События</h1>
        <p className="pa26-micro mt-0.5 text-pa-muted">
          Меню для гостей, праздников, постов и особых дней
        </p>
      </header>

      <V2Card className="border-dashed border-sage-300 bg-sage-50/40 dark:border-sage-600/40 dark:bg-sage-700/10">
        <p className="pa26-body text-pa-muted">
          Скоро PLANAM поможет собрать меню, покупки и план готовки для особых дней.
        </p>
        <V2Button className="mt-3" variant="secondary" disabled>
          Создать событие
        </V2Button>
      </V2Card>

      <div className="space-y-2">
        {EVENT_PREVIEWS.map((item) => (
          <button
            key={item.id}
            type="button"
            disabled
            className="flex w-full items-start gap-3 rounded-card border border-pa-border bg-pa-surface p-3.5 text-left opacity-80"
          >
            <span className="text-xl" aria-hidden>
              {item.emoji}
            </span>
            <span className="min-w-0">
              <span className="pa26-card-title block">{item.title}</span>
              <span className="pa26-caption text-pa-muted">{item.caption}</span>
            </span>
          </button>
        ))}
      </div>

      <V2Button variant="ghost" onClick={() => router.push("/")}>
        На главную
      </V2Button>
    </div>
  );
}
