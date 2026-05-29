import Link from "next/link";

type ProgressProLockedProps = {
  goalLabel: string | null;
};

export function ProgressProLocked({ goalLabel }: ProgressProLockedProps) {
  return (
    <div className="space-y-4">
      {goalLabel ? (
        <section className="pa-card p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
            Ваша цель
          </p>
          <p className="mt-1 text-lg font-bold text-graphite-900">{goalLabel}</p>
          <p className="mt-2 text-sm text-graphite-600">
            Базовая цель из профиля питания доступна всем тарифам.
          </p>
        </section>
      ) : null}

      <section className="pa-card border-sage-200 bg-sage-50/40 p-5">
        <div className="flex items-start gap-3">
          <span className="text-2xl" aria-hidden>
            ✨
          </span>
          <div>
            <p className="font-bold text-graphite-900">
              Прогресс, спорт и аналитика доступны в ПланАм PRO
            </p>
            <p className="mt-2 text-sm leading-relaxed text-graphite-600">
              Вес, замеры, КБЖУ, тренировки и семейный прогресс — для личного
              сопровождения целей.
            </p>
          </div>
        </div>
        <Link href="/subscription" className="pa-btn-primary mt-4 w-full">
          Узнать о PRO
        </Link>
      </section>
    </div>
  );
}
