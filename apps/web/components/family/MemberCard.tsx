"use client";

import Link from "next/link";

import type { FamilyMember } from "@/lib/family/types";
import { sanitizeUserFacingLabel } from "@/lib/display/sanitize-label";

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
    member.member_type === "virtual" ? "Виртуальный участник" : "Аккаунт Telegram";
  const roleLabel =
    member.role === "admin"
      ? "Админ"
      : member.role === "child"
        ? "Ребёнок"
        : "Взрослый";
  const displayName = sanitizeUserFacingLabel(member.display_name, "Участник");
  const profileStatus = member.nutrition_profile_complete
    ? "Заполнен"
    : "Не заполнен";
  const statusColor = member.nutrition_profile_complete
    ? "bg-sage-50 text-sage-700 dark:bg-sage-700/30 dark:text-sage-200"
    : "bg-warm/10 text-pa-muted";

  return (
    <article className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-bold text-pa-foreground">
            {displayName || "Участник"}
            {member.is_you ? (
              <span className="ml-1.5 text-sm font-medium text-pa-muted">
                (вы)
              </span>
            ) : null}
          </h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="rounded-pill bg-cream-deep px-2.5 py-1 text-xs font-medium text-pa-muted dark:bg-pa-elevated">
              {typeLabel}
            </span>
            <span className="rounded-pill bg-olive/20 px-2.5 py-1 text-xs font-medium text-pa-foreground">
              {roleLabel}
            </span>
            <span
              className={`rounded-pill px-2.5 py-1 text-xs font-medium ${statusColor}`}
            >
              Профиль: {profileStatus}
            </span>
          </div>
        </div>
      </div>

      <dl className="mt-4 space-y-3 text-sm">
        <div className="grid gap-1 rounded-control bg-cream-deep/60 px-3 py-2 dark:bg-pa-elevated/50">
          <dt className="text-xs font-medium text-pa-muted">Цель питания</dt>
          <dd className="break-words font-semibold text-pa-foreground">
            {member.nutrition_goal_label ?? "—"}
          </dd>
        </div>
        {member.is_virtual && member.virtual_kind ? (
          <div className="flex justify-between gap-3">
            <dt className="shrink-0 text-pa-muted">Кто</dt>
            <dd className="break-words text-right text-pa-foreground">
              {member.virtual_kind === "child"
                ? "Ребёнок"
                : member.virtual_kind === "elder"
                  ? "Пожилой родственник"
                  : "Другой"}
            </dd>
          </div>
        ) : null}
        {member.is_virtual && member.age_label ? (
          <div className="flex justify-between gap-3">
            <dt className="shrink-0 text-pa-muted">Возраст</dt>
            <dd className="break-words text-right font-medium text-pa-foreground">
              {member.age_label}
            </dd>
          </div>
        ) : null}
        {!member.is_virtual &&
        member.nutrition_summary &&
        !member.is_you ? (
          <p className="rounded-control bg-cream-deep px-3 py-2 text-xs text-pa-muted dark:bg-pa-elevated">
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
            href="/account/nutrition"
            className="rounded-control bg-sage-600 px-3 py-2 text-xs font-semibold text-white"
          >
            Мой профиль питания
          </Link>
        ) : null}
        {isAdmin && member.can_admin_edit_nutrition && onEditNutrition ? (
          <button
            type="button"
            onClick={onEditNutrition}
            data-testid="family-member-edit"
            className="rounded-control border border-pa-border bg-pa-surface px-3 py-2 text-xs font-semibold text-pa-foreground"
          >
            {member.is_virtual ? "Профиль питания" : "Изменить профиль"}
          </button>
        ) : null}
        {isAdmin && member.role !== "admin" && onDelete ? (
          <button
            type="button"
            onClick={onDelete}
            data-testid="family-member-delete"
            className="rounded-control px-3 py-2 text-xs font-semibold text-red-600"
          >
            Удалить
          </button>
        ) : null}
      </div>
    </article>
  );
}
