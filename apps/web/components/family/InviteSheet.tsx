"use client";

import { useState } from "react";

import {
  createFamilyInviteLink,
  inviteFamilyMemberByPhone,
} from "@/lib/family/api";
import type { FamilyInvite } from "@/lib/family/invite-types";

const INPUT_CLS =
  "w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-sm text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200";

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
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-graphite-900/40 p-4">
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-t-card bg-cream-surface p-6 shadow-lift"
        role="dialog"
        aria-labelledby="invite-title"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="invite-title" className="text-lg font-bold text-graphite-900">
            Пригласить в семью
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-sm font-semibold text-graphite-500"
          >
            Закрыть
          </button>
        </div>

        {error ? (
          <p className="mb-4 rounded-control border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        {step === "menu" ? (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setStep("phone")}
              disabled={loading}
              className="pa-card w-full px-4 py-4 text-left text-sm font-semibold text-graphite-900 hover:border-sage-200 disabled:opacity-50"
            >
              Ввести номер телефона
            </button>
            <button
              type="button"
              onClick={handleLinkInvite}
              disabled={loading}
              className="w-full rounded-card border border-sage-200 bg-sage-50 px-4 py-4 text-left text-sm font-semibold text-sage-700 disabled:opacity-50"
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
              className="text-sm font-semibold text-sage-700"
            >
              ← Назад
            </button>
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+79001234567"
              className={INPUT_CLS}
            />
            <button
              type="button"
              onClick={handlePhoneInvite}
              disabled={loading || !phone.trim()}
              className="pa-btn-primary w-full disabled:opacity-50"
            >
              {loading ? "Отправка…" : "Пригласить по номеру"}
            </button>
          </div>
        ) : null}

        {showShare && lastInvite ? (
          <section className="mt-6 rounded-card border border-warm/30 bg-warm/10 p-4">
            <p className="text-xs font-bold uppercase text-graphite-700">
              {lastInvite.invitee_notified
                ? "Приглашение в боте"
                : "Ожидает подтверждения"}
            </p>
            <p className="mt-2 break-all text-xs text-graphite-700">
              {lastInvite.deep_link}
            </p>
            <button
              type="button"
              onClick={() => shareInvite(lastInvite)}
              className="pa-btn-ghost mt-3 w-full"
            >
              Отправить приглашение в Telegram
            </button>
          </section>
        ) : null}

        {lastInvite?.invitee_notified && lastInvite.invited_phone_masked ? (
          <p className="mt-4 text-center text-sm text-sage-700">
            Приглашение отправлено в бот ({lastInvite.invited_phone_masked}).
            Ожидаем ответ.
          </p>
        ) : null}
      </div>
    </div>
  );
}
