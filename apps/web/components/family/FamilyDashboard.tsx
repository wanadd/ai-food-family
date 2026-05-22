"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getTelegramInitData } from "@/lib/telegram-webapp";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import { MemberCard } from "@/components/family/MemberCard";
import { MemberForm } from "@/components/family/MemberForm";
import {
  addFamilyMember,
  createFamily,
  fetchMyFamily,
  inviteFamilyMemberByPhone,
  removeFamilyMember,
  updateFamilyMember,
} from "@/lib/family/api";
import type { Family, FamilyMember } from "@/lib/family/types";
import { EMPTY_MEMBER_DRAFT, type MemberDraft } from "@/lib/family/types";

export function FamilyDashboard() {
  const { refreshContext } = useAppMode();
  const [initData, setInitData] = useState("");
  const [family, setFamily] = useState<Family | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [familyName, setFamilyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);
  const [draft, setDraft] = useState<MemberDraft>(EMPTY_MEMBER_DRAFT);
  const [saving, setSaving] = useState(false);
  const [invitePhone, setInvitePhone] = useState("");
  const [inviting, setInviting] = useState(false);

  const loadFamily = useCallback(async (telegramInitData: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyFamily(telegramInitData);
      setFamily(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load family");
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
    loadFamily(data);
  }, [loadFamily]);

  const isAdmin = family?.your_role === "admin";

  async function handleCreateFamily() {
    if (!initData || !familyName.trim()) {
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const created = await createFamily(initData, familyName.trim());
      setFamily(created);
      setFamilyName("");
      await refreshContext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create family");
    } finally {
      setCreating(false);
    }
  }

  async function handleInviteByPhone() {
    if (!initData || !family || !invitePhone.trim()) {
      return;
    }
    setInviting(true);
    setError(null);
    try {
      await inviteFamilyMemberByPhone(
        initData,
        family.id,
        invitePhone.trim(),
      );
      setInvitePhone("");
      await loadFamily(initData);
      await refreshContext();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось пригласить",
      );
    } finally {
      setInviting(false);
    }
  }

  async function handleAddMember() {
    if (!initData || !family) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await addFamilyMember(initData, family.id, {
        ...draft,
        display_name: draft.display_name.trim(),
      });
      setDraft(EMPTY_MEMBER_DRAFT);
      setShowAddForm(false);
      await loadFamily(initData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add member");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdateMember() {
    if (!initData || !family || !editingMember) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const patch: Partial<MemberDraft> = {
        display_name: draft.display_name.trim(),
        goals: draft.goals,
        restrictions: draft.restrictions,
      };
      if (editingMember.role !== "admin") {
        patch.role = draft.role;
      }
      await updateFamilyMember(initData, family.id, editingMember.id, patch);
      setEditingMember(null);
      setDraft(EMPTY_MEMBER_DRAFT);
      await loadFamily(initData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update member");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteMember(member: FamilyMember) {
    if (!initData || !family) {
      return;
    }
    if (!window.confirm(`Удалить ${member.display_name} из семьи?`)) {
      return;
    }
    setError(null);
    try {
      await removeFamilyMember(initData, family.id, member.id);
      await loadFamily(initData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove member");
    }
  }

  function startEdit(member: FamilyMember) {
    setEditingMember(member);
    setShowAddForm(false);
    setDraft({
      display_name: member.display_name,
      role: member.role,
      goals: member.goals,
      restrictions: member.restrictions,
    });
  }

  if (loading) {
    return (
      <p className="py-20 text-center text-sm text-stone-500">Загрузка семьи…</p>
    );
  }

  if (!initData) {
    return (
      <div className="mx-auto max-w-lg px-5 py-16 text-center">
        <p className="text-sm text-stone-600">
          Управление семьёй доступно в Telegram Mini App после авторизации.
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
    <div className="min-h-screen bg-[#fafaf9]">
      <header className="border-b border-stone-200/80 px-5 py-6">
        <Link href="/" className="text-xs font-semibold text-emerald-700">
          ← Назад
        </Link>
        <h1 className="mt-3 text-2xl font-bold text-stone-900">Семейный режим</h1>
        <p className="mt-1 text-sm text-stone-500">
          Опционально: общие меню, покупки и остатки для всей семьи
        </p>
      </header>

      <main className="mx-auto max-w-lg space-y-6 px-5 py-8">
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        {!family ? (
          <section className="rounded-2xl border border-stone-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-stone-900">
              Подключить семейный режим
            </h2>
            <p className="mt-2 text-sm text-stone-500">
              После создания на главной появится переключатель «Личный / Семейный»
            </p>
            <input
              value={familyName}
              onChange={(event) => setFamilyName(event.target.value)}
              placeholder="Например: Семья Ивановых"
              className="mt-4 w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none ring-emerald-500 focus:border-emerald-500 focus:ring-2"
            />
            <button
              type="button"
              onClick={handleCreateFamily}
              disabled={creating || !familyName.trim()}
              className="mt-4 w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {creating ? "Создание…" : "Создать семью"}
            </button>
          </section>
        ) : (
          <>
            <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
              <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                Ваша семья
              </p>
              <h2 className="mt-1 text-xl font-bold text-stone-900">
                {family.name}
              </h2>
              <p className="mt-2 text-sm text-emerald-900">
                {family.members.length} участник
                {family.members.length === 1
                  ? ""
                  : family.members.length < 5
                    ? "а"
                    : "ов"}
                · ваша роль: {family.your_role}
              </p>
            </section>

            {isAdmin ? (
              <section className="rounded-2xl border border-violet-200 bg-violet-50/60 p-5">
                <h3 className="text-sm font-semibold text-violet-900">
                  Пригласить по номеру
                </h3>
                <p className="mt-1 text-xs text-violet-800">
                  Номер должен быть подтверждён в боте (/start). В боте:{" "}
                  <code className="rounded bg-white/80 px-1">/invite +7900...</code>
                </p>
                <input
                  value={invitePhone}
                  onChange={(e) => setInvitePhone(e.target.value)}
                  placeholder="+79001234567"
                  className="mt-3 w-full rounded-xl border border-violet-200 bg-white px-4 py-3 text-sm outline-none ring-violet-400 focus:border-violet-400 focus:ring-2"
                />
                <button
                  type="button"
                  onClick={handleInviteByPhone}
                  disabled={inviting || !invitePhone.trim()}
                  className="mt-3 w-full rounded-xl bg-violet-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
                >
                  {inviting ? "Приглашение…" : "Пригласить"}
                </button>
              </section>
            ) : null}

            <section className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-stone-500">
                Участники
              </h3>
              {family.members.map((member) => (
                <MemberCard
                  key={member.id}
                  member={member}
                  canManage={Boolean(isAdmin)}
                  onEdit={() => startEdit(member)}
                  onDelete={() => handleDeleteMember(member)}
                />
              ))}
            </section>

            {isAdmin && !showAddForm && !editingMember ? (
              <button
                type="button"
                onClick={() => {
                  setDraft(EMPTY_MEMBER_DRAFT);
                  setShowAddForm(true);
                }}
                className="w-full rounded-xl border border-dashed border-emerald-300 bg-white py-3 text-sm font-semibold text-emerald-700"
              >
                + Добавить члена семьи
              </button>
            ) : null}

            {isAdmin && showAddForm ? (
              <MemberForm
                draft={draft}
                onChange={setDraft}
                submitLabel="Добавить"
                onSubmit={handleAddMember}
                onCancel={() => setShowAddForm(false)}
                loading={saving}
              />
            ) : null}

            {isAdmin && editingMember ? (
              <MemberForm
                draft={draft}
                onChange={setDraft}
                allowRoleSelect={editingMember.role !== "admin"}
                submitLabel="Сохранить"
                onSubmit={handleUpdateMember}
                onCancel={() => {
                  setEditingMember(null);
                  setDraft(EMPTY_MEMBER_DRAFT);
                }}
                loading={saving}
              />
            ) : null}

            {!isAdmin ? (
              <p className="text-center text-xs text-stone-400">
                Только админ может добавлять и редактировать участников
              </p>
            ) : null}
          </>
        )}
      </main>
    </div>
  );
}
