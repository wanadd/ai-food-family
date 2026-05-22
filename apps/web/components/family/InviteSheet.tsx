"use client";

import { useState } from "react";

import {
  createFamilyInviteLink,
  inviteFamilyMemberByPhone,
} from "@/lib/family/api";
import type { FamilyInvite } from "@/lib/family/invite-types";

type InviteSheetProps = {
  open: boolean;
  familyId: number;
  initData: string;
  onClose: () => void;
  onSuccess: (invite: FamilyInvite) => void;
};

type Step = "menu" | "phone";

export function InviteSheet({
  open,
  familyId,
  initData,
  onClose,
  onSuccess,
}: InviteSheetProps) {
  const [step, setStep] = useState<Step>("menu");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastInvite, setLastInvite] = useState<FamilyInvite | null>(null);

  if (!open) {
    return null;
  }

  async function handlePhoneInvite() {
    if (!phone.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const invite = await inviteFamilyMemberByPhone(
        initData,
        familyId,
        phone.trim(),
      );
      setLastInvite(invite);
      onSuccess(invite);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось пригласить");
    } finally {
      setLoading(false);
    }
  }

  async function handleLinkInvite() {
    setLoading(true);
    setError(null);
    try {
      const invite = await createFamilyInviteLink(initData, familyId);
      setLastInvite(invite);
      onSuccess(invite);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось создать ссылку",
      );
    } finally {
      setLoading(false);
    }
  }

  function shareInvite(invite: FamilyInvite) {
    window.open(invite.share_url, "_blank", "noopener,noreferrer");
  }

  const showShare =
    lastInvite && (lastInvite.is_link_invite || !lastInvite.invitee_notified);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4">
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-t-[24px] bg-white p-6 shadow-xl"
        role="dialog"
        aria-labelledby="invite-title"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="invite-title" className="text-lg font-bold text-stone-900">
            Пригласить в семью
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-sm font-semibold text-stone-500"
          >
            Закрыть
          </button>
        </div>

        {error ? (
          <p className="mb-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        {step === "menu" ? (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setStep("phone")}
              disabled={loading}
              className="w-full rounded-2xl border border-stone-200 px-4 py-4 text-left text-sm font-semibold text-stone-900 hover:border-emerald-300 disabled:opacity-50"
            >
              Ввести номер телефона
            </button>
            <button
              type="button"
              onClick={handleLinkInvite}
              disabled={loading}
              className="w-full rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-left text-sm font-semibold text-emerald-900 disabled:opacity-50"
            >
              {loading ? "Создание ссылки…" : "Отправить ссылку-приглашение"}
            </button>
          </div>
        ) : null}

        {step === "phone" ? (
          <div className="space-y-4">
            <button
              type="button"
              onClick={() => setStep("menu")}
              className="text-sm font-semibold text-emerald-700"
            >
              ← Назад
            </button>
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+79001234567"
              className="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
            />
            <button
              type="button"
              onClick={handlePhoneInvite}
              disabled={loading || !phone.trim()}
              className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {loading ? "Отправка…" : "Пригласить по номеру"}
            </button>
          </div>
        ) : null}

        {showShare && lastInvite ? (
          <section className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-xs font-bold uppercase text-amber-800">
              {lastInvite.invitee_notified
                ? "Приглашение в боте"
                : "Ожидает подтверждения"}
            </p>
            <p className="mt-2 break-all text-xs text-amber-900">
              {lastInvite.deep_link}
            </p>
            <button
              type="button"
              onClick={() => shareInvite(lastInvite)}
              className="mt-3 w-full rounded-xl border border-amber-300 bg-white py-3 text-sm font-semibold text-amber-900"
            >
              Отправить приглашение в Telegram
            </button>
          </section>
        ) : null}

        {lastInvite?.invitee_notified && lastInvite.invited_phone_masked ? (
          <p className="mt-4 text-center text-sm text-emerald-700">
            Приглашение отправлено в бот ({lastInvite.invited_phone_masked}).
            Ожидаем ответ.
          </p>
        ) : null}
      </div>
    </div>
  );
}
