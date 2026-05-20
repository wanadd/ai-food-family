"use client";

import { ChipSelect } from "@/components/onboarding/ChipSelect";
import { GOAL_OPTIONS } from "@/lib/onboarding/options";
import { MEMBER_RESTRICTION_OPTIONS } from "@/lib/family/options";
import type { FamilyRole, MemberDraft } from "@/lib/family/types";

type MemberFormProps = {
  draft: MemberDraft;
  onChange: (draft: MemberDraft) => void;
  allowRoleSelect?: boolean;
  submitLabel: string;
  onSubmit: () => void;
  onCancel?: () => void;
  loading?: boolean;
};

const ROLE_OPTIONS: { value: FamilyRole; label: string }[] = [
  { value: "adult", label: "Взрослый" },
  { value: "child", label: "Ребёнок" },
];

export function MemberForm({
  draft,
  onChange,
  allowRoleSelect = true,
  submitLabel,
  onSubmit,
  onCancel,
  loading = false,
}: MemberFormProps) {
  return (
    <div className="space-y-5 rounded-2xl border border-stone-200 bg-white p-5">
      <div>
        <label className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Имя
        </label>
        <input
          value={draft.display_name}
          onChange={(event) =>
            onChange({ ...draft, display_name: event.target.value })
          }
          placeholder="Например: Маша"
          className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none ring-emerald-500 focus:border-emerald-500 focus:ring-2"
        />
      </div>

      {allowRoleSelect ? (
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-stone-500">
            Роль
          </label>
          <div className="mt-2 flex gap-2">
            {ROLE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onChange({ ...draft, role: option.value })}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                  draft.role === option.value
                    ? "border-emerald-600 bg-emerald-50 text-emerald-900"
                    : "border-stone-200 text-stone-600"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Цели
        </p>
        <div className="mt-2">
          <ChipSelect
            options={GOAL_OPTIONS}
            value={draft.goals}
            onChange={(goals) => onChange({ ...draft, goals })}
          />
        </div>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">
          Ограничения и аллергии
        </p>
        <div className="mt-2">
          <ChipSelect
            options={MEMBER_RESTRICTION_OPTIONS}
            value={draft.restrictions}
            onChange={(restrictions) => onChange({ ...draft, restrictions })}
            exclusiveNone="none"
          />
        </div>
      </div>

      <div className="flex gap-3 pt-1">
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="flex-1 rounded-xl border border-stone-200 py-3 text-sm font-semibold text-stone-700"
          >
            Отмена
          </button>
        ) : null}
        <button
          type="button"
          onClick={onSubmit}
          disabled={loading || !draft.display_name.trim()}
          className="flex-[1.4] rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Сохранение…" : submitLabel}
        </button>
      </div>
    </div>
  );
}
