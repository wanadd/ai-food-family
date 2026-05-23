"use client";

import { ChipSelect } from "@/components/onboarding/ChipSelect";
import { OptionCards } from "@/components/onboarding/OptionCards";
import { TextAreaField } from "@/components/onboarding/TextAreaField";
import { NumberInput } from "@/components/nutrition-profile/NumberInput";
import {
  ALLERGY_OPTIONS,
  DIET_OPTIONS,
  NUTRITION_GOAL_OPTIONS,
} from "@/lib/nutrition-profile/options";
import type { VirtualMemberDraft } from "@/lib/family/types";

const KIND_OPTIONS = [
  { value: "child", label: "Ребёнок" },
  { value: "elder", label: "Пожилой родственник" },
  { value: "other", label: "Другой" },
];

type VirtualMemberNutritionFormProps = {
  draft: VirtualMemberDraft;
  onChange: (draft: VirtualMemberDraft) => void;
  submitLabel: string;
  onSubmit: () => void;
  onCancel: () => void;
  loading?: boolean;
  /** Редактирование участника с Telegram (только питание). */
  linkedAccount?: boolean;
  linkedName?: string;
};

export function VirtualMemberNutritionForm({
  draft,
  onChange,
  submitLabel,
  onSubmit,
  onCancel,
  loading,
  linkedAccount,
  linkedName,
}: VirtualMemberNutritionFormProps) {
  const nutrition = draft.nutrition;

  return (
    <section className="rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
      <h3 className="text-base font-bold text-stone-900">
        {linkedAccount ? linkedName ?? "Участник" : "Без аккаунта"}
      </h3>
      <p className="mt-1 text-sm text-stone-500">
        {linkedAccount
          ? "Профиль участника с его разрешения"
          : "Профиль учтётся в семейном меню"}
      </p>

      <div className="mt-4 space-y-4">
        {!linkedAccount ? (
          <>
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-stone-700">
                Имя
              </span>
              <input
                value={draft.display_name}
                onChange={(e) =>
                  onChange({ ...draft, display_name: e.target.value })
                }
                placeholder="Маша, бабушка…"
                className="w-full rounded-xl border border-stone-200 px-4 py-3 text-base outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500"
              />
            </label>

            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Кто это</p>
              <div className="flex flex-wrap gap-2">
                {KIND_OPTIONS.map((o) => (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() =>
                      onChange({
                        ...draft,
                        virtual_kind: o.value,
                        role: o.value === "child" ? "child" : "adult",
                      })
                    }
                    className={`rounded-full border px-3 py-2 text-sm font-medium ${
                      draft.virtual_kind === o.value
                        ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                        : "border-stone-200 text-stone-700"
                    }`}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
          </>
        ) : null}

        <NumberInput
          label="Возраст"
          value={nutrition.age}
          onChange={(age) =>
            onChange({
              ...draft,
              nutrition: { ...nutrition, age },
            })
          }
          min={1}
          max={120}
        />

        <div>
          <p className="mb-2 text-sm font-medium text-stone-700">Цель питания</p>
          <OptionCards
            options={NUTRITION_GOAL_OPTIONS}
            value={nutrition.nutrition_goal}
            onChange={(nutrition_goal) =>
              onChange({
                ...draft,
                nutrition: { ...nutrition, nutrition_goal },
              })
            }
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-stone-700">Аллергии</p>
          <ChipSelect
            options={ALLERGY_OPTIONS}
            value={nutrition.allergies}
            onChange={(allergies) =>
              onChange({ ...draft, nutrition: { ...nutrition, allergies } })
            }
            exclusiveNone="none"
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-stone-700">Ограничения</p>
          <ChipSelect
            options={DIET_OPTIONS}
            value={nutrition.diets}
            onChange={(diets) =>
              onChange({ ...draft, nutrition: { ...nutrition, diets } })
            }
            exclusiveNone="none"
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-stone-700">Любит</p>
          <TextAreaField
            value={nutrition.favorite_foods}
            onChange={(favorite_foods) =>
              onChange({
                ...draft,
                nutrition: { ...nutrition, favorite_foods },
              })
            }
            placeholder="Что включать в меню чаще"
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-stone-700">Не любит</p>
          <TextAreaField
            value={nutrition.disliked_foods}
            onChange={(disliked_foods) =>
              onChange({
                ...draft,
                nutrition: { ...nutrition, disliked_foods },
              })
            }
            placeholder="Чего избегать"
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-stone-700">
            Особенности питания
          </p>
          <TextAreaField
            value={nutrition.notes}
            onChange={(notes) =>
              onChange({ ...draft, nutrition: { ...nutrition, notes } })
            }
            placeholder="Например: мягкая пища, без острого…"
          />
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 rounded-xl border border-stone-200 py-3 text-sm font-semibold text-stone-700"
        >
          Отмена
        </button>
        <button
          type="button"
          disabled={
            loading ||
            (!linkedAccount && !draft.display_name.trim()) ||
            !nutrition.nutrition_goal
          }
          onClick={onSubmit}
          className="flex-1 rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Сохранение…" : submitLabel}
        </button>
      </div>
    </section>
  );
}
