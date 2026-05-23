import Link from "next/link";

type ProgressProLockedProps = {
  goalLabel: string | null;
};

export function ProgressProLocked({ goalLabel }: ProgressProLockedProps) {
  return (
    <div className="space-y-4">
      {goalLabel ? (
        <section className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">
            Ваша цель
          </p>
          <p className="mt-1 text-lg font-bold text-stone-900">{goalLabel}</p>
          <p className="mt-2 text-sm text-stone-600">
            Базовая цель из профиля питания доступна всем тарифам.
          </p>
        </section>
      ) : null}

      <section className="rounded-2xl border border-stone-200 bg-stone-50/90 p-5">
        <div className="flex items-start gap-3">
          <span className="text-2xl" aria-hidden>
            ✨
          </span>
          <div>
            <p className="font-bold text-stone-900">
              Прогресс, спорт и аналитика доступны в ПланАм PRO
            </p>
            <p className="mt-2 text-sm leading-relaxed text-stone-600">
              Вес, замеры, КБЖУ, тренировки и семейный прогресс — для личного
              сопровождения целей.
            </p>
          </div>
        </div>
        <Link
          href="/subscription"
          className="mt-4 flex min-h-[44px] items-center justify-center rounded-xl bg-emerald-600 text-sm font-semibold text-white"
        >
          Узнать о PRO
        </Link>
      </section>
    </div>
  );
}
