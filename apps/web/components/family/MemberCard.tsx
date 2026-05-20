"use client";

import { RoleBadge } from "@/components/family/RoleBadge";
import { labelsFor } from "@/lib/family/labels";
import type { FamilyMember } from "@/lib/family/types";

type MemberCardProps = {
  member: FamilyMember;
  canManage: boolean;
  onEdit: () => void;
  onDelete: () => void;
};

export function MemberCard({
  member,
  canManage,
  onEdit,
  onDelete,
}: MemberCardProps) {
  return (
    <article className="rounded-2xl border border-stone-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-stone-900">
              {member.display_name}
            </h3>
            <RoleBadge role={member.role} />
            {member.is_you ? (
              <span className="text-xs text-stone-400">это вы</span>
            ) : null}
          </div>
        </div>
        {canManage ? (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onEdit}
              className="text-xs font-semibold text-emerald-700"
            >
              Изменить
            </button>
            {member.role !== "admin" ? (
              <button
                type="button"
                onClick={onDelete}
                className="text-xs font-semibold text-red-600"
              >
                Удалить
              </button>
            ) : null}
          </div>
        ) : null}
      </div>

      <dl className="mt-4 space-y-2 text-sm">
        <div>
          <dt className="text-xs uppercase tracking-wide text-stone-400">Цели</dt>
          <dd className="mt-0.5 text-stone-700">{labelsFor(member.goals)}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-stone-400">
            Ограничения
          </dt>
          <dd className="mt-0.5 text-stone-700">
            {labelsFor(member.restrictions)}
          </dd>
        </div>
      </dl>
    </article>
  );
}
