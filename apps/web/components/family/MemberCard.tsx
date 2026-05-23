"use client";

import Link from "next/link";

import type { FamilyMember } from "@/lib/family/types";

type MemberCardProps = {
  member: FamilyMember;
  isAdmin: boolean;
  onEditNutrition?: () => void;
  onDelete?: () => void;
};

export function MemberCard({
  member,
  isAdmin,
  onEditNutrition,
  onDelete,
}: MemberCardProps) {
  const typeLabel =
    member.member_type === "virtual" ? "Без аккаунта" : "Аккаунт Telegram";
  const profileStatus = member.nutrition_profile_complete
    ? "Заполнен"
    : "Не заполнен";
  const statusColor = member.nutrition_profile_complete
    ? "bg-emerald-100 text-emerald-800"
    : "bg-amber-100 text-amber-900";

  return (
    <article className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-bold text-stone-900">
            {member.display_name}
            {member.is_you ? (
              <span className="ml-1.5 text-sm font-medium text-stone-400">
                (вы)
              </span>
            ) : null}
          </h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-medium text-stone-700">
              {typeLabel}
            </span>
            <span className="rounded-full bg-violet-100 px-2.5 py-0.5 text-xs font-medium text-violet-800">
              {member.role_label}
            </span>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}
            >
              Профиль: {profileStatus}
            </span>
          </div>
        </div>
      </div>

      <dl className="mt-3 space-y-1.5 text-sm">
        <div className="flex justify-between gap-2">
          <dt className="text-stone-500">Цель питания</dt>
          <dd className="text-right font-medium text-stone-800">
            {member.nutrition_goal_label ?? "—"}
          </dd>
        </div>
        {member.is_virtual && member.virtual_kind ? (
          <div className="flex justify-between gap-2">
            <dt className="text-stone-500">Кто</dt>
            <dd className="text-right text-stone-800">
              {member.virtual_kind === "child"
                ? "Ребёнок"
                : member.virtual_kind === "elder"
                  ? "Пожилой родственник"
                  : "Другой"}
            </dd>
          </div>
        ) : null}
        {!member.is_virtual &&
        member.nutrition_summary &&
        !member.is_you ? (
          <p className="rounded-xl bg-stone-50 px-3 py-2 text-xs text-stone-600">
            {member.nutrition_summary.nutrition_goal_label
              ? `Цель: ${String(member.nutrition_summary.nutrition_goal_label)}`
              : "Профиль ещё не настроен"}
            {member.allow_admin_profile_edit
              ? " · админ может помогать с настройкой"
              : ""}
          </p>
        ) : null}
      </dl>

      <div className="mt-3 flex flex-wrap gap-2">
        {member.is_you && !member.is_virtual ? (
          <Link
            href="/profile/nutrition"
            className="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white"
          >
            Мой профиль питания
          </Link>
        ) : null}
        {isAdmin && member.can_admin_edit_nutrition && onEditNutrition ? (
          <button
            type="button"
            onClick={onEditNutrition}
            className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800"
          >
            {member.is_virtual ? "Профиль питания" : "Изменить профиль"}
          </button>
        ) : null}
        {isAdmin && member.role !== "admin" && onDelete ? (
          <button
            type="button"
            onClick={onDelete}
            className="rounded-xl px-3 py-2 text-xs font-semibold text-red-600"
          >
            Удалить
          </button>
        ) : null}
      </div>
    </article>
  );
}
