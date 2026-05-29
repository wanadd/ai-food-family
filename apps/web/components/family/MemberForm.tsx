"use client";

import { ChipSelect } from "@/components/onboarding/ChipSelect";
import { GOAL_OPTIONS } from "@/lib/onboarding/options";
import { MEMBER_RESTRICTION_OPTIONS } from "@/lib/family/options";
import type { FamilyRole, MemberDraft } from "@/lib/family/types";

const INPUT_CLS =
  "mt-2 w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-sm text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200";

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
    <div className="pa-card space-y-5 p-5">
      <div>
        <label className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
          Имя
        </label>
        <input
          value={draft.display_name}
          onChange={(event) =>
            onChange({ ...draft, display_name: event.target.value })
          }
          placeholder="Например: Маша"
          className={INPUT_CLS}
        />
      </div>

      {allowRoleSelect ? (
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
            Роль
          </label>
          <div className="mt-2 flex gap-2">
            {ROLE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onChange({ ...draft, role: option.value })}
                className={`rounded-pill border px-4 py-2 text-sm font-medium transition ${
                  draft.role === option.value
                    ? "border-sage-500 bg-sage-50 text-sage-700"
                    : "border-cream-border text-graphite-600"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
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
        <p className="text-xs font-semibold uppercase tracking-wide text-graphite-500">
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
            className="pa-btn-ghost flex-1"
          >
            Отмена
          </button>
        ) : null}
        <button
          type="button"
          onClick={onSubmit}
          disabled={loading || !draft.display_name.trim()}
          className="pa-btn-primary flex-[1.4] disabled:opacity-50"
        >
          {loading ? "Сохранение…" : submitLabel}
        </button>
      </div>
    </div>
  );
}
