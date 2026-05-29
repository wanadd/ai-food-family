"use client";

import { useState } from "react";

import { useToast } from "@/components/ui/ToastProvider";
import {
  deleteFamily,
  leaveFamily,
  renameFamily,
  transferFamilyAdmin,
} from "@/lib/family/api";
import type { Family, FamilyMember } from "@/lib/family/types";

const INPUT_CLS =
  "mt-1 w-full rounded-control border border-cream-border bg-cream-surface px-3 py-2.5 text-sm text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200";

type Props = {
  open: boolean;
  onClose: () => void;
  family: Family;
  initData: string;
  onUpdated: (family: Family | null) => void;
};

export function FamilyManageSheet({
  open,
  onClose,
  family,
  initData,
  onUpdated,
}: Props) {
  const { showToast } = useToast();
  const isAdmin = family.your_role === "admin";
  const [name, setName] = useState(family.name);
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [transferId, setTransferId] = useState<number | null>(null);

  const telegramMembers = family.members.filter(
    (m) => !m.is_virtual && m.user_id && !m.is_you,
  );

  if (!open) return null;

  async function handleRename() {
    const trimmed = name.trim();
    if (!trimmed) return;
    setBusy(true);
    try {
      const updated = await renameFamily(initData, trimmed);
      showToast("Название семьи обновлено");
      onUpdated(updated);
      onClose();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    try {
      await deleteFamily(initData);
      showToast("Семья удалена");
      onUpdated(null);
      onClose();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Не удалось удалить");
    } finally {
      setBusy(false);
      setConfirmDelete(false);
    }
  }

  async function handleLeave() {
    setBusy(true);
    try {
      await leaveFamily(initData);
      showToast("Вы покинули семью");
      onUpdated(null);
      onClose();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Не удалось выйти");
    } finally {
      setBusy(false);
    }
  }

  async function handleTransfer(member: FamilyMember) {
    setBusy(true);
    try {
      const updated = await transferFamilyAdmin(initData, member.id);
      showToast(`Права переданы: ${member.display_name}`);
      onUpdated(updated);
      onClose();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Не удалось передать права");
    } finally {
      setBusy(false);
      setTransferId(null);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-graphite-900/40 p-0">
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-t-card bg-cream-surface p-4 pb-8 shadow-lift">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-graphite-900">Управление семьёй</h2>
          <button type="button" onClick={onClose} className="text-graphite-500">
            Закрыть
          </button>
        </div>

        {isAdmin ? (
          <>
            <label className="block text-sm font-medium text-graphite-700">
              Название семьи
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={INPUT_CLS}
            />
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleRename()}
              className="pa-btn-primary mt-3 w-full disabled:opacity-50"
            >
              Сохранить
            </button>

            {telegramMembers.length > 0 ? (
              <div className="mt-6">
                <p className="text-sm font-semibold text-graphite-900">
                  Передать права администратора
                </p>
                <ul className="mt-2 space-y-2">
                  {telegramMembers.map((m) => (
                    <li key={m.id}>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => {
                          setTransferId(m.id);
                          void handleTransfer(m);
                        }}
                        className="pa-card w-full px-3 py-2.5 text-left text-sm disabled:opacity-50"
                      >
                        {m.display_name}
                        {transferId === m.id ? " …" : ""}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {!confirmDelete ? (
              <button
                type="button"
                onClick={() => setConfirmDelete(true)}
                className="mt-6 w-full rounded-control border border-red-200 py-3 text-sm font-semibold text-red-700"
              >
                Удалить семью
              </button>
            ) : (
              <div className="mt-6 rounded-card border border-red-100 bg-red-50 p-4">
                <p className="font-semibold text-graphite-900">
                  Удалить семью «{family.name}»?
                </p>
                <p className="mt-2 text-xs text-graphite-500">
                  Будут удалены семейные меню, общие покупки, общие запасы и
                  участники без аккаунта. Telegram-пользователи не удаляются.
                </p>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void handleDelete()}
                    className="flex-1 rounded-control bg-red-600 py-2.5 text-sm font-semibold text-white"
                  >
                    Удалить
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(false)}
                    className="pa-btn-ghost flex-1 py-2.5"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <button
            type="button"
            disabled={busy}
            onClick={() => void handleLeave()}
            className="pa-btn-ghost w-full"
          >
            Покинуть семью
          </button>
        )}
      </div>
    </div>
  );
}
