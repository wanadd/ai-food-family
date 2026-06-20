"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { useTelegram } from "@/components/TelegramProvider";
import { AddPersonSheet } from "@/components/family/AddPersonSheet";
import { InviteSheet } from "@/components/family/InviteSheet";
import { MemberCard } from "@/components/family/MemberCard";
import { FamilyManageSheet } from "@/components/family/FamilyManageSheet";
import { VirtualMemberNutritionForm } from "@/components/family/VirtualMemberNutritionForm";
import { ScreenLayout } from "@/components/layout/ScreenLayout";
import { usePlanam2026Embedded } from "@/lib/planam/embedded-2026";
import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";
import { StickyBottomBar } from "@/components/layout/StickyBottomBar";
import { useToast } from "@/components/ui/ToastProvider";
import {
  addVirtualFamilyMember,
  createFamily,
  fetchMyFamily,
  removeFamilyMember,
  updateMemberNutrition,
} from "@/lib/family/api";
import type { FamilyInvite } from "@/lib/family/invite-types";
import {
  EMPTY_VIRTUAL_DRAFT,
  EMPTY_VIRTUAL_NUTRITION,
  type Family,
  type FamilyMember,
  type VirtualMemberDraft,
  type VirtualNutrition,
} from "@/lib/family/types";
import { sanitizeFamilyName, sanitizeUserFacingLabel } from "@/lib/display/sanitize-label";

function memberCountLabel(count: number): string {
  const n = Math.abs(count);
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return `${n} участник`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `${n} участника`;
  }
  return `${n} участников`;
}

function draftFromMember(member: FamilyMember): VirtualMemberDraft {
  const raw = member.virtual_nutrition;
  const nutrition: VirtualNutrition = raw
    ? {
        ...EMPTY_VIRTUAL_NUTRITION,
        ...raw,
        custom_allergies: raw.custom_allergies ?? [],
        custom_restrictions: raw.custom_restrictions ?? [],
      }
    : { ...EMPTY_VIRTUAL_NUTRITION };

  return {
    display_name: sanitizeUserFacingLabel(member.display_name, "Участник"),
    virtual_kind: member.virtual_kind ?? "child",
    role: member.role === "child" ? "child" : "adult",
    nutrition,
  };
}

function isDraftValid(
  draft: VirtualMemberDraft,
  linkedAccount: boolean,
): boolean {
  const n = draft.nutrition;
  const goalOk =
    n.nutrition_goal &&
    (n.nutrition_goal !== "other" || (n.custom_nutrition_goal || "").trim());
  const isChild = draft.virtual_kind === "child" || draft.role === "child";
  const consentOk = linkedAccount
    ? true
    : isChild
      ? Boolean(draft.guardian_consent)
      : Boolean(draft.data_consent);

  return Boolean(
    (linkedAccount || draft.display_name.trim()) &&
      goalOk &&
      n.age_months != null &&
      consentOk,
  );
}

type FamilyLayoutProps = {
  title: string;
  subtitle?: string;
  back?: { label: string; href?: string; onClick?: () => void };
  footer?: ReactNode;
  children: ReactNode;
};

export function FamilyDashboard() {
  const embedded = usePlanam2026Embedded("/account/family");
  const profileBack = embedded ? "/account" : "/profile";
  const generateHref = isPlanamUi2026Enabled()
    ? PLAN_PATHS.generate
    : "/menu/generate";

  function FamilyLayout({
    title,
    subtitle,
    back,
    footer,
    children,
  }: FamilyLayoutProps) {
    if (embedded) {
      return (
        <>
          <div className="mx-auto max-w-lg px-4 pb-6 pt-[max(0.75rem,env(safe-area-inset-top))]">
            <header className="mb-3">
              <h1 className="pa26-page-title">Семья</h1>
              {subtitle ? (
                <p className="pa26-micro mt-0.5 text-pa-muted">{subtitle}</p>
              ) : null}
            </header>
            {children}
          </div>
          {footer}
        </>
      );
    }

    return (
      <ScreenLayout title={title} subtitle={subtitle} back={back} footer={footer}>
        {children}
      </ScreenLayout>
    );
  }

  const { refreshContext } = useAppMode();
  const { initData } = useTelegram();
  const { showToast } = useToast();
  const [family, setFamily] = useState<Family | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [familyName, setFamilyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [adminConsent, setAdminConsent] = useState(false);
  const [showAddPerson, setShowAddPerson] = useState(false);
  const [showInviteSheet, setShowInviteSheet] = useState(false);
  const [virtualDraft, setVirtualDraft] = useState<VirtualMemberDraft>(
    EMPTY_VIRTUAL_DRAFT,
  );
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);
  const [showNutritionForm, setShowNutritionForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastInvite, setLastInvite] = useState<FamilyInvite | null>(null);
  const [showManage, setShowManage] = useState(false);

  const loadFamily = useCallback(async (telegramInitData: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyFamily(telegramInitData);
      setFamily(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить семью");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!initData) {
      setLoading(false);
      return;
    }
    void loadFamily(initData);
  }, [initData, loadFamily]);

  const isAdmin = family?.your_role === "admin";
  const linkedAccount = Boolean(editingMember && !editingMember.is_virtual);

  function closeMemberForm() {
    setShowNutritionForm(false);
    setEditingMember(null);
    setVirtualDraft(EMPTY_VIRTUAL_DRAFT);
    setError(null);
  }

  async function handleCreateFamily() {
    if (!initData || !familyName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createFamily(initData, sanitizeFamilyName(familyName), adminConsent);
      setFamily(created);
      setFamilyName("");
      await refreshContext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось создать семью");
    } finally {
      setCreating(false);
    }
  }

  function openNewVirtual() {
    setEditingMember(null);
    setVirtualDraft(EMPTY_VIRTUAL_DRAFT);
    setShowNutritionForm(true);
  }

  async function openEditNutrition(member: FamilyMember) {
    if (initData) {
      const data = await fetchMyFamily(initData);
      const fresh = data?.members.find((m) => m.id === member.id) ?? member;
      setEditingMember(fresh);
      setVirtualDraft(draftFromMember(fresh));
    } else {
      setEditingMember(member);
      setVirtualDraft(draftFromMember(member));
    }
    setShowNutritionForm(true);
  }

  async function handleSaveNutrition() {
    if (!initData || !family) return;
    setSaving(true);
    setError(null);
    try {
      if (editingMember) {
        await updateMemberNutrition(
          initData,
          family.id,
          editingMember.id,
          virtualDraft.nutrition,
        );
      } else {
        await addVirtualFamilyMember(initData, family.id, {
          ...virtualDraft,
          display_name: virtualDraft.display_name.trim(),
        });
      }
      await loadFamily(initData);
      await refreshContext();
      closeMemberForm();
      await showToast("✓ Сохранено");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteMember(member: FamilyMember) {
    if (!initData || !family) return;
    if (!window.confirm(`Убрать ${sanitizeUserFacingLabel(member.display_name, "участника")} из семьи?`)) return;
    setError(null);
    try {
      await removeFamilyMember(initData, family.id, member.id);
      await loadFamily(initData);
      await refreshContext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить");
    }
  }

  if (loading) {
    return (
      <p className="py-20 text-center text-sm text-graphite-500">Загрузка…</p>
    );
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-5">
        <p className="text-sm text-graphite-600">
          Семья доступна в Telegram Mini App.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-sage-700"
        >
          На главную
        </Link>
      </div>
    );
  }

  if (showNutritionForm) {
    const formTitle = linkedAccount
      ? sanitizeUserFacingLabel(editingMember?.display_name, "Участник")
      : editingMember
        ? sanitizeUserFacingLabel(editingMember.display_name, "Участник")
        : "Новый участник";

    return (
      <>
        <FamilyLayout
          title={formTitle}
          subtitle="Профиль учтётся в семейном меню"
          back={{ label: "Семья", onClick: closeMemberForm }}
          footer={
            <StickyBottomBar>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={closeMemberForm}
                  className="pa-btn-ghost flex-1"
                >
                  Отмена
                </button>
                <button
                  type="button"
                  disabled={
                    saving || !isDraftValid(virtualDraft, linkedAccount)
                  }
                  onClick={() => void handleSaveNutrition()}
                  className="pa-btn-primary flex-1 disabled:opacity-50"
                >
                  {saving
                    ? "Сохранение…"
                    : editingMember
                      ? "Сохранить"
                      : "Добавить в семью"}
                </button>
              </div>
            </StickyBottomBar>
          }
        >
          {error ? (
            <p className="mb-3 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          ) : null}
          <VirtualMemberNutritionForm
            draft={virtualDraft}
            onChange={setVirtualDraft}
            submitLabel={
              editingMember ? "Сохранить профиль" : "Добавить в семью"
            }
            linkedAccount={linkedAccount}
            linkedName={sanitizeUserFacingLabel(editingMember?.display_name, "")}
            onSubmit={() => void handleSaveNutrition()}
            onCancel={closeMemberForm}
            loading={saving}
            hideFooter
          />
        </FamilyLayout>

        <AddPersonSheet
          open={showAddPerson}
          onClose={() => setShowAddPerson(false)}
          onInviteTelegram={() => setShowInviteSheet(true)}
          onAddVirtual={openNewVirtual}
        />
      </>
    );
  }

  return (
    <>
      <FamilyLayout
        title="Семья и участники"
        subtitle="Общее меню, покупки и профили участников"
        back={{ label: "Профиль", href: profileBack }}
      >
        {error ? (
          <p className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        ) : null}

        {!family ? (
          <section className="pa-card p-5">
            <h2 className="text-lg font-bold text-graphite-900">Создать семью</h2>
            <p className="mt-2 text-sm leading-relaxed text-graphite-500">
              Общее меню и покупки для близких. Личный режим останется доступен.
            </p>
            <input
              value={familyName}
              onChange={(e) => setFamilyName(e.target.value)}
              placeholder="Например: Семья Ивановых"
              className="mt-4 w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-base text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200"
            />
            <label className="mt-4 flex items-start gap-3 text-sm text-graphite-700">
              <input
                type="checkbox"
                checked={adminConsent}
                onChange={(e) => setAdminConsent(e.target.checked)}
                className="mt-1 rounded border-cream-border text-sage-500"
              />
              <span>Я подтверждаю право управлять семейным аккаунтом</span>
            </label>
            <button
              type="button"
              onClick={() => void handleCreateFamily()}
              disabled={creating || !familyName.trim() || !adminConsent}
              className="pa-btn-primary mt-4 w-full disabled:opacity-50"
            >
              {creating ? "Создание…" : "Создать семью"}
            </button>
          </section>
        ) : (
          <>
            <section className="pa-card border-sage-200 bg-sage-50/40 p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
                Ваша семья
              </p>
              <h2 className="mt-1 text-xl font-bold text-graphite-900">
                {sanitizeFamilyName(family.name)}
              </h2>
              <div className="mt-3 flex flex-wrap gap-2 text-sm">
                <span className="pa-chip">
                  {memberCountLabel(family.members_count)}
                </span>
                <span className="pa-chip">
                  Тариф: {family.plan_label}
                </span>
                <span className="pa-chip">
                  {isAdmin ? "Админ" : "Взрослый участник"}
                </span>
              </div>
              <p className="mt-3 text-sm text-graphite-700">
                Семейное меню и общий список покупок будут учитывать участников и их профили.
              </p>
              <button
                type="button"
                onClick={() => setShowManage(true)}
                className="pa-btn-ghost mt-4 w-full"
              >
                Управление семьёй
              </button>
            </section>

            {isAdmin ? (
              <button
                type="button"
                onClick={() => setShowAddPerson(true)}
                data-testid="family-add-member"
                className="pa-btn-primary w-full active:scale-[0.99]"
              >
                + Добавить человека
              </button>
            ) : null}

            {lastInvite ? (
              <p className="rounded-control border border-warm/30 bg-warm/10 px-4 py-3 text-sm text-graphite-900 dark:border-sage-700/40 dark:bg-sage-900/20 dark:text-pa-foreground">
                {lastInvite.invitee_notified
                  ? "Приглашение отправлено — ожидаем ответ в Telegram"
                  : "Ссылка отправлена — ожидаем, когда человек примет приглашение"}
              </p>
            ) : null}

            <section className="space-y-3">
              <h3 className="px-1 text-xs font-semibold uppercase tracking-wide text-graphite-400">
                Участники
              </h3>
              {family.members.map((member) => (
                <MemberCard
                  key={member.id}
                  member={member}
                  isAdmin={Boolean(isAdmin)}
                  onEditNutrition={
                    member.can_admin_edit_nutrition
                      ? () => void openEditNutrition(member)
                      : undefined
                  }
                  onDelete={() => void handleDeleteMember(member)}
                />
              ))}
            </section>

            <section className="pa-card border-sage-200 bg-sage-50/50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">
                Следующий шаг
              </p>
              <p className="mt-1 text-sm text-graphite-700">
                {family.members_count <= 1
                  ? "Добавьте ещё участника или соберите семейное меню — оба шага не обязательны."
                  : "Соберите меню для семьи — ПланАм учтёт всех участников и их ограничения."}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link
                  href={generateHref}
                  className="pa-btn-primary inline-flex min-h-[40px] items-center px-4 active:scale-[0.99]"
                >
                  Составить семейное меню
                </Link>
                {isAdmin ? (
                  <button
                    type="button"
                    onClick={() => setShowAddPerson(true)}
                    data-testid="family-add-member-secondary"
                    className="pa-btn-ghost inline-flex min-h-[40px] items-center px-4"
                  >
                    + Добавить участника
                  </button>
                ) : null}
              </div>
            </section>
          </>
        )}
      </FamilyLayout>

      <AddPersonSheet
        open={showAddPerson}
        onClose={() => setShowAddPerson(false)}
        onInviteTelegram={() => setShowInviteSheet(true)}
        onAddVirtual={openNewVirtual}
      />

      {family && isAdmin ? (
        <InviteSheet
          open={showInviteSheet}
          familyId={family.id}
          initData={initData}
          onClose={() => setShowInviteSheet(false)}
          onSuccess={(invite) => {
            setLastInvite(invite);
          }}
        />
      ) : null}

      {family ? (
        <FamilyManageSheet
          open={showManage}
          onClose={() => setShowManage(false)}
          family={family}
          initData={initData}
          onUpdated={async (updated) => {
            setFamily(updated);
            setShowManage(false);
            await refreshContext();
          }}
        />
      ) : null}
    </>
  );
}
