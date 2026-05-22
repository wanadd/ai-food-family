"use client";

import { useEffect, useState } from "react";

import {
  fetchFamilyInvites,
  getBotDeepLink,
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

type Step = "menu" | "phone" | "contact";

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
  const [pendingInvites, setPendingInvites] = useState<FamilyInvite[]>([]);

  useEffect(() => {
    if (!open) {
      setStep("menu");
      setError(null);
      return;
    }
    fetchFamilyInvites(initData, familyId)
      .then(setPendingInvites)
      .catch(() => setPendingInvites([]));
  }, [open, initData, familyId]);

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

  function openBotForContact() {
    window.open(getBotDeepLink("invite"), "_blank", "noopener,noreferrer");
  }

  function shareInvite(invite: FamilyInvite) {
    window.open(invite.share_url, "_blank", "noopener,noreferrer");
  }

  async function copyInviteLink(invite: FamilyInvite) {
    try {
      await navigator.clipboard.writeText(invite.deep_link);
    } catch {
      window.prompt("Скопируйте ссылку:", invite.deep_link);
    }
  }

  const showPendingShare = lastInvite && !lastInvite.invitee_notified;
  const latestPending = pendingInvites[0] ?? null;

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
              className="w-full rounded-2xl border border-stone-200 px-4 py-4 text-left text-sm font-semibold text-stone-900 hover:border-emerald-300"
            >
              По номеру телефона
            </button>
            <button
              type="button"
              onClick={() => setStep("contact")}
              className="w-full rounded-2xl border border-violet-200 bg-violet-50/60 px-4 py-4 text-left text-sm font-semibold text-violet-900"
            >
              Через Telegram-контакт
            </button>
            {latestPending ? (
              <button
                type="button"
                onClick={() => copyInviteLink(latestPending)}
                className="w-full rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-left text-sm font-semibold text-amber-900"
              >
                Скопировать ссылку-приглашение
                <span className="mt-1 block text-xs font-normal text-amber-800">
                  {latestPending.invited_phone_masked} — ожидает подтверждения
                </span>
              </button>
            ) : null}
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

        {step === "contact" ? (
          <div className="space-y-4">
            <button
              type="button"
              onClick={() => setStep("menu")}
              className="text-sm font-semibold text-emerald-700"
            >
              ← Назад
            </button>
            <p className="text-sm leading-relaxed text-stone-600">
              Telegram не даёт Mini App прямой доступ к списку контактов.
              Выбор контакта доступен в чат-боте: «Пригласить в семью» → «Выбрать
              контакт».
            </p>
            <button
              type="button"
              onClick={openBotForContact}
              className="w-full rounded-xl bg-violet-600 py-3 text-sm font-semibold text-white"
            >
              Открыть бота для приглашения
            </button>
          </div>
        ) : null}

        {showPendingShare ? (
          <section className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-xs font-bold uppercase text-amber-800">
              Ожидает подтверждения
            </p>
            <p className="mt-2 text-sm text-amber-900">
              Человек ещё не запускал ПланАм. Отправьте ссылку в Telegram.
            </p>
            <button
              type="button"
              onClick={() => shareInvite(lastInvite)}
              className="mt-3 w-full rounded-xl border border-amber-300 bg-white py-3 text-sm font-semibold text-amber-900"
            >
              Отправить ссылку в Telegram
            </button>
          </section>
        ) : null}

        {lastInvite?.invitee_notified ? (
          <p className="mt-4 text-center text-sm text-emerald-700">
            Приглашение отправлено в бот. Ожидаем ответ.
          </p>
        ) : null}
      </div>
    </div>
  );
}
