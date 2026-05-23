"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { AddPersonSheet } from "@/components/family/AddPersonSheet";
import { InviteSheet } from "@/components/family/InviteSheet";
import { MemberCard } from "@/components/family/MemberCard";
import { VirtualMemberNutritionForm } from "@/components/family/VirtualMemberNutritionForm";
import { BottomBackButton } from "@/components/layout/BottomBackButton";
import { useTelegram } from "@/components/TelegramProvider";
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
import { getTelegramInitData } from "@/lib/telegram-webapp";

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
  const nutrition: VirtualNutrition = member.virtual_nutrition
    ? { ...member.virtual_nutrition }
    : { ...EMPTY_VIRTUAL_NUTRITION };

  return {
    display_name: member.display_name,
    virtual_kind: member.virtual_kind ?? "child",
    role: member.role === "child" ? "child" : "adult",
    nutrition,
  };
}

export function FamilyDashboard() {
  const { refreshContext } = useAppMode();
  const [initData, setInitData] = useState("");
  const [family, setFamily] = useState<Family | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [familyName, setFamilyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [showAddPerson, setShowAddPerson] = useState(false);
  const [showInviteSheet, setShowInviteSheet] = useState(false);
  const [virtualDraft, setVirtualDraft] = useState<VirtualMemberDraft>(
    EMPTY_VIRTUAL_DRAFT,
  );
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);
  const [showNutritionForm, setShowNutritionForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastInvite, setLastInvite] = useState<FamilyInvite | null>(null);

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
    const data = getTelegramInitData();
    setInitData(data);
    if (!data) {
      setLoading(false);
      return;
    }
    void loadFamily(data);
  }, [loadFamily]);

  const isAdmin = family?.your_role === "admin";

  async function handleCreateFamily() {
    if (!initData || !familyName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createFamily(initData, familyName.trim());
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
      setShowNutritionForm(false);
      setEditingMember(null);
      setVirtualDraft(EMPTY_VIRTUAL_DRAFT);
      await loadFamily(initData);
      await refreshContext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteMember(member: FamilyMember) {
    if (!initData || !family) return;
    if (!window.confirm(`Убрать ${member.display_name} из семьи?`)) return;
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
      <p className="py-20 text-center text-sm text-stone-500">Загрузка…</p>
    );
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-5">
        <p className="text-sm text-stone-600">
          Семья доступна в Telegram Mini App.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-semibold text-emerald-700"
        >
          На главную
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-100 bg-white px-4 pb-3 pt-7 sm:px-5">
        <div className="mx-auto max-w-lg">
          <h1 className="text-2xl font-bold text-stone-900">Семья и участники</h1>
          <p className="mt-1 text-sm text-stone-500">
            Необязательно — можно пользоваться ПланАм одному
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-lg space-y-4 px-4 py-4 pb-24 sm:px-5">
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        ) : null}

        {!family ? (
          <section className="rounded-3xl border border-stone-100 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-bold text-stone-900">Создать семью</h2>
            <p className="mt-2 text-sm leading-relaxed text-stone-600">
              Общее меню и покупки для близких. Личный режим останется доступен.
            </p>
            <input
              value={familyName}
              onChange={(e) => setFamilyName(e.target.value)}
              placeholder="Например: Семья Ивановых"
              className="mt-4 w-full rounded-xl border border-stone-200 px-4 py-3 text-base outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500"
            />
            <button
              type="button"
              onClick={() => void handleCreateFamily()}
              disabled={creating || !familyName.trim()}
              className="mt-4 w-full rounded-2xl bg-emerald-600 py-3.5 text-sm font-semibold text-white disabled:opacity-50"
            >
              {creating ? "Создание…" : "Создать семью"}
            </button>
          </section>
        ) : (
          <>
            <section className="rounded-3xl border border-violet-100 bg-gradient-to-br from-violet-50/90 to-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">
                Ваша семья
              </p>
              <h2 className="mt-1 text-xl font-bold text-stone-900">{family.name}</h2>
              <div className="mt-3 flex flex-wrap gap-2 text-sm">
                <span className="rounded-full bg-white/80 px-3 py-1 font-medium text-stone-700 ring-1 ring-stone-100">
                  {memberCountLabel(family.members_count)}
                </span>
                <span className="rounded-full bg-white/80 px-3 py-1 font-medium text-stone-700 ring-1 ring-stone-100">
                  Тариф: {family.plan_label}
                </span>
              </div>
            </section>

            {isAdmin ? (
              <button
                type="button"
                onClick={() => setShowAddPerson(true)}
                className="w-full rounded-2xl bg-emerald-600 py-3.5 text-base font-semibold text-white shadow-md shadow-emerald-200/40 active:scale-[0.99]"
              >
                + Добавить человека
              </button>
            ) : null}

            {lastInvite ? (
              <p className="rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-950">
                Приглашение отправлено — ожидаем ответ в Telegram
              </p>
            ) : null}

            {showNutritionForm ? (
              <VirtualMemberNutritionForm
                draft={virtualDraft}
                onChange={setVirtualDraft}
                submitLabel={
                  editingMember
                    ? "Сохранить профиль"
                    : "Добавить в семью"
                }
                linkedAccount={Boolean(
                  editingMember && !editingMember.is_virtual,
                )}
                linkedName={editingMember?.display_name}
                onSubmit={() => void handleSaveNutrition()}
                onCancel={() => {
                  setShowNutritionForm(false);
                  setEditingMember(null);
                  setVirtualDraft(EMPTY_VIRTUAL_DRAFT);
                }}
                loading={saving}
              />
            ) : null}

            <section className="space-y-3">
              <h3 className="px-1 text-xs font-semibold uppercase tracking-wide text-stone-400">
                Участники
              </h3>
              {family.members.map((member) => (
                <MemberCard
                  key={member.id}
                  member={member}
                  isAdmin={Boolean(isAdmin)}
                  onEditNutrition={
                    member.can_admin_edit_nutrition
                      ? () => openEditNutrition(member)
                      : undefined
                  }
                  onDelete={() => void handleDeleteMember(member)}
                />
              ))}
            </section>
          </>
        )}
      </main>

      <BottomBackButton className="pb-2 pt-2" />

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
            setShowInviteSheet(false);
          }}
        />
      ) : null}
    </div>
  );
}
