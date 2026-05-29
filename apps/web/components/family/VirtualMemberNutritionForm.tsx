"use client";

import { useMemo, useState } from "react";

import { MultiSelectField } from "@/components/ui/MultiSelectField";
import {
  ageInputFromMonths,
  toAgeMonths,
  validateAgeMonths,
  type AgeUnit,
} from "@/lib/family/age";
import type { VirtualMemberDraft } from "@/lib/family/types";
import {
  ALLERGY_OPTIONS,
  ALLERGY_PRESET_VALUES,
  NUTRITION_GOAL_OPTIONS,
  RESTRICTION_OPTIONS,
  RESTRICTION_PRESET_VALUES,
  VIRTUAL_KIND_OPTIONS,
} from "@/lib/family/virtual-member-options";

type VirtualMemberNutritionFormProps = {
  draft: VirtualMemberDraft;
  onChange: (draft: VirtualMemberDraft) => void;
  submitLabel: string;
  onSubmit: () => void;
  onCancel: () => void;
  loading?: boolean;
  linkedAccount?: boolean;
  linkedName?: string;
  hideFooter?: boolean;
};

function mergeSelected(preset: string[], custom: string[]): string[] {
  return [...preset, ...custom.filter((c) => !preset.includes(c))];
}

function splitSelected(
  selected: string[],
  presetValues: Set<string>,
): { preset: string[]; custom: string[] } {
  const preset = selected.filter((v) => presetValues.has(v));
  const custom = selected.filter((v) => !presetValues.has(v));
  return { preset, custom };
}

export function VirtualMemberNutritionForm({
  draft,
  onChange,
  submitLabel,
  onSubmit,
  onCancel,
  loading,
  linkedAccount,
  linkedName,
  hideFooter = false,
}: VirtualMemberNutritionFormProps) {
  const nutrition = draft.nutrition;
  const isChild = draft.virtual_kind === "child" || draft.role === "child";

  const initialAge = ageInputFromMonths(nutrition.age_months, isChild);
  const [ageAmount, setAgeAmount] = useState<number | "">(
    initialAge.amount ?? "",
  );
  const [ageUnit, setAgeUnit] = useState<AgeUnit>(initialAge.unit);
  const [ageError, setAgeError] = useState<string | null>(null);

  const allergySelected = useMemo(
    () => mergeSelected(nutrition.allergies, nutrition.custom_allergies),
    [nutrition.allergies, nutrition.custom_allergies],
  );
  const restrictionSelected = useMemo(
    () => mergeSelected(nutrition.restrictions, nutrition.custom_restrictions),
    [nutrition.restrictions, nutrition.custom_restrictions],
  );

  function syncAgeMonths(amount: number | "", unit: AgeUnit) {
    setAgeAmount(amount);
    setAgeUnit(unit);
    if (amount === "" || Number.isNaN(Number(amount))) {
      onChange({
        ...draft,
        nutrition: { ...nutrition, age_months: null },
      });
      setAgeError("Укажите возраст");
      return;
    }
    const months = toAgeMonths(Number(amount), unit);
    const err = validateAgeMonths(months, isChild);
    setAgeError(err);
    onChange({
      ...draft,
      nutrition: { ...nutrition, age_months: err ? null : months },
    });
  }

  const goalOk =
    nutrition.nutrition_goal &&
    (nutrition.nutrition_goal !== "other" ||
      (nutrition.custom_nutrition_goal || "").trim());

  return (
    <section className="space-y-3">
      <div className="pa-card p-4">
        <h3 className="text-base font-bold text-graphite-900">
          {linkedAccount ? linkedName ?? "Участник" : "Участник без аккаунта"}
        </h3>
        <p className="mt-1 text-xs text-graphite-500">
          {linkedAccount
            ? "Профиль с разрешения участника"
            : "Учтётся в семейном меню"}
        </p>

        {!linkedAccount ? (
          <div className="mt-4 space-y-3">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-graphite-700">
                Имя
              </span>
              <input
                value={draft.display_name}
                onChange={(e) =>
                  onChange({ ...draft, display_name: e.target.value })
                }
                placeholder="Маша, бабушка…"
                className="w-full rounded-control border border-cream-border px-4 py-3 text-base outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
              />
            </label>

            <div>
              <p className="mb-2 text-sm font-medium text-graphite-700">Кто это</p>
              <div className="flex flex-wrap gap-2">
                {VIRTUAL_KIND_OPTIONS.map((o) => (
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
                        ? "border-sage-500 bg-sage-50 text-sage-700"
                        : "border-cream-border text-graphite-700"
                    }`}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <div className="pa-card p-4">
        <p className="text-sm font-semibold text-graphite-800">Возраст и цель</p>

        <div className="mt-3 grid grid-cols-[1fr_auto] gap-2">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-graphite-600">
              Возраст
            </span>
            <input
              type="number"
              min={0}
              value={ageAmount}
              onChange={(e) => {
                const raw = e.target.value;
                syncAgeMonths(raw === "" ? "" : Number(raw), ageUnit);
              }}
              className="w-full rounded-control border border-cream-border px-4 py-3 text-base outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
            />
          </label>
          <label className="block min-w-[7.5rem]">
            <span className="mb-1 block text-xs font-medium text-graphite-600">
              Единица
            </span>
            <select
              value={ageUnit}
              onChange={(e) => {
                const unit = e.target.value as AgeUnit;
                syncAgeMonths(ageAmount, unit);
              }}
              className="w-full rounded-control border border-cream-border px-3 py-3 text-base outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
            >
              <option value="months">месяцев</option>
              <option value="years">лет</option>
            </select>
          </label>
        </div>
        {ageError ? (
          <p className="mt-1 text-xs text-red-600">{ageError}</p>
        ) : (
          <p className="mt-1 text-xs text-graphite-500">
            {isChild
              ? "До 2 лет удобнее указывать в месяцах"
              : "Возраст сохраняется точно для меню"}
          </p>
        )}

        <label className="mt-4 block">
          <span className="mb-1.5 block text-sm font-medium text-graphite-700">
            Цель питания
          </span>
          <select
            value={nutrition.nutrition_goal ?? ""}
            onChange={(e) =>
              onChange({
                ...draft,
                nutrition: {
                  ...nutrition,
                  nutrition_goal: e.target.value || null,
                },
              })
            }
            className="w-full rounded-control border border-cream-border px-4 py-3 text-base outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          >
            <option value="">Выберите цель</option>
            {NUTRITION_GOAL_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        {nutrition.nutrition_goal === "other" ? (
          <label className="mt-3 block">
            <span className="mb-1.5 block text-sm font-medium text-graphite-700">
              Своя цель
            </span>
            <input
              value={nutrition.custom_nutrition_goal ?? ""}
              onChange={(e) =>
                onChange({
                  ...draft,
                  nutrition: {
                    ...nutrition,
                    custom_nutrition_goal: e.target.value,
                  },
                })
              }
              placeholder="Опишите цель"
              className="w-full rounded-control border border-cream-border px-4 py-3 text-base outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
            />
          </label>
        ) : null}
      </div>

      <div className="pa-card p-4">
        <p className="mb-3 text-sm font-semibold text-graphite-800">
          Аллергии и ограничения
        </p>

        <MultiSelectField
          label="Аллергии"
          options={ALLERGY_OPTIONS}
          value={allergySelected}
          customValues={nutrition.custom_allergies}
          exclusiveNone="none"
          customPlaceholder="Добавить свою аллергию"
          hint="Можно выбрать несколько"
          onChange={(selected, custom) => {
            const { preset, custom: mergedCustom } = splitSelected(
              selected,
              ALLERGY_PRESET_VALUES,
            );
            onChange({
              ...draft,
              nutrition: {
                ...nutrition,
                allergies: preset,
                custom_allergies: Array.from(
                  new Set([...mergedCustom, ...custom]),
                ),
              },
            });
          }}
        />

        <div className="mt-4">
          <MultiSelectField
            label="Ограничения"
            options={RESTRICTION_OPTIONS}
            value={restrictionSelected}
            customValues={nutrition.custom_restrictions}
            exclusiveNone="none"
            customPlaceholder="Добавить своё ограничение"
            hint="Можно выбрать несколько"
            onChange={(selected, custom) => {
              const { preset, custom: mergedCustom } = splitSelected(
                selected,
                RESTRICTION_PRESET_VALUES,
              );
              onChange({
                ...draft,
                nutrition: {
                  ...nutrition,
                  restrictions: preset,
                  custom_restrictions: Array.from(
                    new Set([...mergedCustom, ...custom]),
                  ),
                },
              });
            }}
          />
        </div>
      </div>

      <div className="pa-card p-4">
        <p className="mb-3 text-sm font-semibold text-graphite-800">
          Вкусы и особенности
        </p>

        <label className="block">
          <span className="mb-1.5 block text-sm font-medium text-graphite-700">
            Любит
          </span>
          <textarea
            value={nutrition.favorite_foods}
            onChange={(e) =>
              onChange({
                ...draft,
                nutrition: { ...nutrition, favorite_foods: e.target.value },
              })
            }
            rows={2}
            placeholder="Например: каши, ягоды, супы"
            className="w-full resize-y rounded-control border border-cream-border px-4 py-3 text-sm outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          />
        </label>

        <label className="mt-3 block">
          <span className="mb-1.5 block text-sm font-medium text-graphite-700">
            Не любит
          </span>
          <textarea
            value={nutrition.disliked_foods}
            onChange={(e) =>
              onChange({
                ...draft,
                nutrition: { ...nutrition, disliked_foods: e.target.value },
              })
            }
            rows={2}
            placeholder="Например: рыбу, острое, брокколи"
            className="w-full resize-y rounded-control border border-cream-border px-4 py-3 text-sm outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          />
        </label>

        <label className="mt-3 block">
          <span className="mb-1.5 block text-sm font-medium text-graphite-700">
            Особенности питания
          </span>
          <textarea
            value={nutrition.notes}
            onChange={(e) =>
              onChange({
                ...draft,
                nutrition: { ...nutrition, notes: e.target.value },
              })
            }
            rows={2}
            placeholder="Например: мягкая пища, без острого, маленькие порции"
            className="w-full resize-y rounded-control border border-cream-border px-4 py-3 text-sm outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
          />
        </label>
      </div>

      {!linkedAccount ? (
        <div className="rounded-card border border-warm/30 bg-warm/10 p-4">
          {isChild ? (
            <label className="flex items-start gap-3 text-sm text-graphite-800">
              <input
                type="checkbox"
                checked={Boolean(draft.guardian_consent)}
                onChange={(e) =>
                  onChange({ ...draft, guardian_consent: e.target.checked })
                }
                className="mt-1"
              />
              <span>
                Я являюсь родителем либо законным представителем ребёнка или имею
                право добавлять эти данные
              </span>
            </label>
          ) : (
            <label className="flex items-start gap-3 text-sm text-graphite-800">
              <input
                type="checkbox"
                checked={Boolean(draft.data_consent)}
                onChange={(e) =>
                  onChange({ ...draft, data_consent: e.target.checked })
                }
                className="mt-1"
              />
              <span>
                Я получил согласие на внесение данных этого человека в семейный
                аккаунт
              </span>
            </label>
          )}
        </div>
      ) : null}

      {!hideFooter ? (
        <div className="flex gap-2 pb-2">
          <button
            type="button"
            onClick={onCancel}
            className="pa-btn-ghost flex-1"
          >
            Отмена
          </button>
          <button
            type="button"
            disabled={
              loading ||
              (!linkedAccount && !draft.display_name.trim()) ||
              !goalOk ||
              nutrition.age_months == null ||
              Boolean(ageError) ||
              (!linkedAccount &&
                (isChild ? !draft.guardian_consent : !draft.data_consent))
            }
            onClick={onSubmit}
            className="pa-btn-primary flex-1 disabled:opacity-50"
          >
            {loading ? "Сохранение…" : submitLabel}
          </button>
        </div>
      ) : null}
    </section>
  );
}
