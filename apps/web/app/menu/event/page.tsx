"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { useTelegram } from "@/components/TelegramProvider";
import {
  createEventPlan,
  createEventShoppingList,
  type EventPlanDetail,
} from "@/lib/event-plan/api";

const EVENT_TYPES = [
  { value: "holiday_dinner", label: "Праздничный ужин" },
  { value: "birthday", label: "День рождения" },
  { value: "bbq", label: "Барбекю" },
  { value: "kids_party", label: "Детский праздник" },
  { value: "picnic", label: "Пикник" },
  { value: "fasting", label: "Постное мероприятие" },
  { value: "custom", label: "Свой сценарий" },
];

export default function EventPlanWizardPage() {
  const { initData } = useTelegram();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [eventType, setEventType] = useState("birthday");
  const [guests, setGuests] = useState(6);
  const [budget, setBudget] = useState("medium");
  const [religious, setReligious] = useState("none");
  const [fasting, setFasting] = useState("none");
  const [drinks, setDrinks] = useState("non_alcoholic");
  const [alcohol, setAlcohol] = useState(false);
  const [plan, setPlan] = useState<EventPlanDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    if (!initData) return;
    setLoading(true);
    setError(null);
    try {
      const result = await createEventPlan(initData, {
        event_type: eventType,
        guests_count: guests,
        budget,
        religious_restriction: religious,
        fasting_mode: fasting,
        drink_menu_mode: drinks,
        alcohol_enabled: alcohol,
      });
      setPlan(result);
      setStep(7);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка создания плана");
    } finally {
      setLoading(false);
    }
  }

  async function handleShopping() {
    if (!initData || !plan) return;
    setLoading(true);
    try {
      await createEventShoppingList(initData, plan.id);
      router.push("/shopping");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  if (!initData) {
    return (
      <ScreenLayout title="Event Plan" back={{ label: "Меню", href: "/menu" }}>
        <p className="text-sm text-graphite-600">Доступно в Telegram Mini App.</p>
      </ScreenLayout>
    );
  }

  if (plan && step >= 7) {
    return (
      <ScreenLayout title={plan.title} back={{ label: "Меню", href: "/menu" }}>
        <p className="text-sm text-graphite-600">{plan.nutrition_note}</p>
        <p className="mt-2 text-sm font-semibold text-graphite-800">
          Гостей: {plan.guests_count}
          {plan.estimated_cost_rub
            ? ` · ~${plan.estimated_cost_rub} ₽`
            : null}
        </p>
        <ul className="mt-4 space-y-2">
          {plan.dishes.map((d) => (
            <li key={d.recipe_id} className="pa-card p-3 text-sm">
              {d.title}
            </li>
          ))}
        </ul>
        <button
          type="button"
          disabled={loading}
          onClick={() => void handleShopping()}
          className="pa-btn-primary mt-6 w-full py-3 text-sm"
        >
          Создать список покупок
        </button>
        <Link href="/menu" className="mt-4 block text-center text-sm text-sage-700">
          ← К меню
        </Link>
      </ScreenLayout>
    );
  }

  return (
    <ScreenLayout
      title="Создать событие"
      subtitle={`Шаг ${step + 1} из 7`}
      back={{ label: "Меню", href: "/menu" }}
    >
      {error ? (
        <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : null}

      {step === 0 ? (
        <div className="space-y-2">
          {EVENT_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => setEventType(t.value)}
              className={`w-full rounded-control px-4 py-3 text-left text-sm font-semibold ${
                eventType === t.value
                  ? "bg-sage-600 text-white"
                  : "bg-cream-surface ring-1 ring-cream-border text-graphite-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      ) : null}

      {step === 1 ? (
        <label className="block">
          <span className="text-sm font-semibold">Количество гостей</span>
          <input
            type="number"
            min={1}
            max={100}
            value={guests}
            onChange={(e) => setGuests(Number(e.target.value))}
            className="mt-2 w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          />
        </label>
      ) : null}

      {step === 2 ? (
        <select
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
          className="w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
        >
          <option value="low">Эконом</option>
          <option value="medium">Средний</option>
          <option value="high">Щедрый</option>
        </select>
      ) : null}

      {step === 3 ? (
        <input
          type="text"
          placeholder="Тематика (необязательно)"
          className="w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
        />
      ) : null}

      {step === 4 ? (
        <div className="space-y-3">
          <select
            value={religious}
            onChange={(e) => setReligious(e.target.value)}
            className="w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-sm text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          >
            <option value="none">Религия: не учитывать</option>
            <option value="orthodox">Православие</option>
            <option value="islam">Ислам</option>
            <option value="judaism">Иудаизм</option>
            <option value="hinduism">Индуизм</option>
            <option value="other">Другое</option>
          </select>
          <select
            value={fasting}
            onChange={(e) => setFasting(e.target.value)}
            className="w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-sm text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          >
            <option value="none">Пост: нет</option>
            <option value="great_lent">Великий пост</option>
            <option value="ramadan">Рамадан</option>
            <option value="custom">Свой режим</option>
          </select>
        </div>
      ) : null}

      {step === 5 ? (
        <div className="space-y-3">
          <select
            value={drinks}
            onChange={(e) => setDrinks(e.target.value)}
            className="w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-sm text-graphite-900 focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          >
            <option value="none">Без напитков</option>
            <option value="non_alcoholic">Только безалкогольные</option>
            <option value="cocktail">Коктейльная карта</option>
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={alcohol}
              onChange={(e) => setAlcohol(e.target.checked)}
            />
            Алкоголь (явное включение)
          </label>
        </div>
      ) : null}

      {step === 6 ? (
        <p className="text-sm text-graphite-600">
          ПланАм подберёт блюда из базы рецептов, пересчитает порции на {guests}{" "}
          гостей и сформирует покупки с учётом запасов.
        </p>
      ) : null}

      <div className="mt-8 flex gap-2">
        {step > 0 ? (
          <button
            type="button"
            onClick={() => setStep((s) => s - 1)}
            className="flex-1 pa-btn py-3 text-sm"
          >
            Назад
          </button>
        ) : null}
        {step < 6 ? (
          <button
            type="button"
            onClick={() => setStep((s) => s + 1)}
            className="flex-1 pa-btn-primary py-3 text-sm"
          >
            Далее
          </button>
        ) : (
          <button
            type="button"
            disabled={loading}
            onClick={() => void handleCreate()}
            className="flex-1 pa-btn-primary py-3 text-sm disabled:opacity-50"
          >
            {loading ? "…" : "Создать план"}
          </button>
        )}
      </div>
    </ScreenLayout>
  );
}
