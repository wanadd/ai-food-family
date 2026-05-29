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
    ? "bg-sage-50 text-sage-700"
    : "bg-warm/10 text-graphite-700";

  return (
    <article className="pa-card p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-bold text-graphite-900">
            {member.display_name}
            {member.is_you ? (
              <span className="ml-1.5 text-sm font-medium text-graphite-400">
                (вы)
              </span>
            ) : null}
          </h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="pa-chip">{typeLabel}</span>
            <span className="rounded-pill bg-olive/20 px-2.5 py-0.5 text-xs font-medium text-graphite-700">
              {member.role_label}
            </span>
            <span
              className={`rounded-pill px-2.5 py-0.5 text-xs font-medium ${statusColor}`}
            >
              Профиль: {profileStatus}
            </span>
          </div>
        </div>
      </div>

      <dl className="mt-3 space-y-1.5 text-sm">
        <div className="flex justify-between gap-2">
          <dt className="text-graphite-500">Цель питания</dt>
          <dd className="text-right font-medium text-graphite-900">
            {member.nutrition_goal_label ?? "—"}
          </dd>
        </div>
        {member.is_virtual && member.virtual_kind ? (
          <div className="flex justify-between gap-2">
            <dt className="text-graphite-500">Кто</dt>
            <dd className="text-right text-graphite-900">
              {member.virtual_kind === "child"
                ? "Ребёнок"
                : member.virtual_kind === "elder"
                  ? "Пожилой родственник"
                  : "Другой"}
            </dd>
          </div>
        ) : null}
        {member.is_virtual && member.age_label ? (
          <div className="flex justify-between gap-2">
            <dt className="text-graphite-500">Возраст</dt>
            <dd className="text-right font-medium text-graphite-900">
              {member.age_label}
            </dd>
          </div>
        ) : null}
        {!member.is_virtual &&
        member.nutrition_summary &&
        !member.is_you ? (
          <p className="rounded-control bg-cream-deep px-3 py-2 text-xs text-graphite-500">
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
            className="pa-btn-primary px-3 py-2 text-xs"
          >
            Мой профиль питания
          </Link>
        ) : null}
        {isAdmin && member.can_admin_edit_nutrition && onEditNutrition ? (
          <button
            type="button"
            onClick={onEditNutrition}
            className="pa-btn-ghost px-3 py-2 text-xs"
          >
            {member.is_virtual ? "Профиль питания" : "Изменить профиль"}
          </button>
        ) : null}
        {isAdmin && member.role !== "admin" && onDelete ? (
          <button
            type="button"
            onClick={onDelete}
            className="rounded-control px-3 py-2 text-xs font-semibold text-red-600"
          >
            Удалить
          </button>
        ) : null}
      </div>
    </article>
  );
}
