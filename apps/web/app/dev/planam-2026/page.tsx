"use client";

import { useState } from "react";

import {
  ActionCard2026,
  BottomSheet2026,
  Button2026,
  Card2026,
  EmptyState2026,
  HeroCard2026,
  InsightCard2026,
  MetricCard2026,
  Skeleton2026,
  ThemeToggle2026,
} from "@/components/planam-2026";

export default function Planam2026DevPreviewPage() {
  const [sheetOpen, setSheetOpen] = useState(false);

  return (
    <main className="mx-auto max-w-lg px-4 pb-12 pt-6">
      <p className="pa26-micro mb-1 text-warm">Internal · Sprint 1</p>
      <h1 className="pa26-hero">PLANAM 2026</h1>
      <p className="pa26-body mt-2 text-pa-muted">
        Preview дизайн-системы. Не связан с production-навигацией.
      </p>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Тема</h2>
        <ThemeToggle2026 />
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Кнопки</h2>
        <div className="flex flex-col gap-2">
          <Button2026 variant="primary">Primary</Button2026>
          <Button2026 variant="secondary">Secondary</Button2026>
          <Button2026 variant="ghost">Ghost</Button2026>
          <Button2026 variant="danger">Danger</Button2026>
          <Button2026 variant="primary" size="compact">
            Compact
          </Button2026>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Card</h2>
        <Card2026>
          <p className="pa26-body">Базовая карточка на semantic tokens.</p>
        </Card2026>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Hero Card</h2>
        <div className="flex gap-3 overflow-x-auto pb-2">
          <HeroCard2026
            title="Куриный суп"
            caption="Обед · 420 ккал"
            aspect="4:3"
            ctaLabel="Открыть"
            onCta={() => undefined}
          />
          <HeroCard2026 title="Загрузка…" loading aspect="4:3" />
        </div>
      </section>

      <section className="mt-8 flex flex-col gap-2">
        <h2 className="pa26-section-title mb-1">Action Card</h2>
        <ActionCard2026
          title="Список покупок"
          caption="5 из 12 куплено"
          icon={<span aria-hidden>✓</span>}
          onClick={() => undefined}
        />
        <ActionCard2026
          title="Кладовая"
          caption="Молоко · 2 дня"
          icon={<span aria-hidden>🫙</span>}
        />
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Insight Card</h2>
        <InsightCard2026
          emoji="💡"
          disclaimer="Рекомендация, не медицинское назначение"
        >
          Сегодня добавьте овощи к ужину — так проще держать баланс КБЖУ.
        </InsightCard2026>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Metric Card</h2>
        <div className="flex gap-2">
          <MetricCard2026 label="Вода" value="1.2 л" progress={60} />
          <MetricCard2026 label="Ккал" value="1840" locked />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Bottom Sheet</h2>
        <Button2026 variant="secondary" onClick={() => setSheetOpen(true)}>
          Открыть sheet
        </Button2026>
        <BottomSheet2026
          open={sheetOpen}
          title="Пример sheet"
          onClose={() => setSheetOpen(false)}
          footer={
            <div className="flex gap-2">
              <Button2026 variant="ghost" className="flex-1" onClick={() => setSheetOpen(false)}>
                Позже
              </Button2026>
              <Button2026 variant="primary" className="flex-1" onClick={() => setSheetOpen(false)}>
                Готово
              </Button2026>
            </div>
          }
        >
          <p className="pa26-body text-pa-muted">
            Контент bottom sheet с sticky footer по Design System 2026.
          </p>
        </BottomSheet2026>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Empty State</h2>
        <Card2026 padding="none">
          <EmptyState2026
            icon={<span aria-hidden>🍽</span>}
            title="Пока нет меню"
            description="Сгенерируйте план на неделю — и блюда появятся здесь."
            actionLabel="Создать меню"
            onAction={() => undefined}
          />
        </Card2026>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Skeleton</h2>
        <div className="space-y-2">
          <Skeleton2026 variant="rect" aspectRatio="16/9" className="h-auto" />
          <Skeleton2026 variant="text" />
          <Skeleton2026 variant="circle" />
        </div>
      </section>
    </main>
  );
}
