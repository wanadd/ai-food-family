"use client";

import { useEffect, useState } from "react";

import {
  createFamilyInviteLink,
  inviteFamilyMemberByPhone,
} from "@/lib/family/api";
import type { FamilyInvite } from "@/lib/family/invite-types";

const INPUT_CLS =
  "w-full rounded-control border border-cream-border bg-cream-surface px-4 py-3 text-sm text-graphite-900 outline-none focus:border-sage-400 focus:ring-2 focus:ring-sage-200 dark:border-pa-border dark:bg-pa-surface dark:text-pa-foreground dark:focus:border-sage-500 dark:focus:ring-sage-700/40";

type InviteSheetProps = {
  open: boolean;
  familyId: number;
  initData: string;
  onClose: () => void;
  /** Вызывается только после завершения flow: бот уведомил или пользователь отправил share. */
  onSuccess: (invite: FamilyInvite) => void;
};

type Step = "menu" | "phone" | "loading" | "share" | "sent";

function needsTelegramShare(invite: FamilyInvite): boolean {
  return invite.is_link_invite || !invite.invitee_notified;
}

export function InviteSheet({
  open,
  familyId,
  initData,
  onClose,
  onSuccess,
}: InviteSheetProps) {
  const [step, setStep] = useState<Step>("menu");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [lastInvite, setLastInvite] = useState<FamilyInvite | null>(null);

  useEffect(() => {
    if (open) {
      setStep("menu");
      setPhone("");
      setError(null);
      setLastInvite(null);
    }
  }, [open]);

  if (!open) {
    return null;
  }

  async function handlePhoneInvite() {
    if (!phone.trim()) {
      return;
    }
    setStep("loading");
    setError(null);
    try {
      const invite = await inviteFamilyMemberByPhone(
        initData,
        familyId,
        phone.trim(),
      );
      setLastInvite(invite);
      if (needsTelegramShare(invite)) {
        setStep("share");
      } else {
        setStep("sent");
        onSuccess(invite);
      }
    } catch (err) {
      setStep("phone");
      setError(err instanceof Error ? err.message : "Не удалось пригласить");
    }
  }

  async function handleLinkInvite() {
    setStep("loading");
    setError(null);
    try {
      const invite = await createFamilyInviteLink(initData, familyId);
      setLastInvite(invite);
      setStep("share");
    } catch (err) {
      setStep("menu");
      setError(
        err instanceof Error ? err.message : "Не удалось создать ссылку",
      );
    }
  }

  function handleShare() {
    if (!lastInvite) {
      return;
    }
    window.open(lastInvite.share_url, "_blank", "noopener,noreferrer");
    onSuccess(lastInvite);
    setStep("sent");
  }

  function handleClose() {
    if (step === "loading") {
      return;
    }
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-graphite-900/40 p-4 dark:bg-black/50">
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-t-card bg-cream-surface p-6 shadow-lift dark:border dark:border-pa-border dark:bg-pa-surface"
        role="dialog"
        aria-labelledby="invite-title"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2
            id="invite-title"
            className="text-lg font-bold text-graphite-900 dark:text-pa-foreground"
          >
            Пригласить в семью
          </h2>
          <button
            type="button"
            onClick={handleClose}
            disabled={step === "loading"}
            className="text-sm font-semibold text-graphite-500 disabled:opacity-40 dark:text-pa-muted"
          >
            Закрыть
          </button>
        </div>

        {error ? (
          <p className="mb-4 rounded-control border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-pa-error/30 dark:bg-pa-error/10 dark:text-pa-error">
            {error}
          </p>
        ) : null}

        {step === "loading" ? (
          <div className="py-8 text-center">
            <p className="text-sm font-semibold text-graphite-900 dark:text-pa-foreground">
              Готовим приглашение…
            </p>
            <p className="mt-1 text-sm text-graphite-500 dark:text-pa-muted">
              Создаём ссылку для Telegram
            </p>
          </div>
        ) : null}

        {step === "menu" ? (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setStep("phone")}
              className="pa-card w-full px-4 py-4 text-left text-sm font-semibold text-graphite-900 hover:border-sage-200 dark:text-pa-foreground dark:hover:border-sage-700/50"
            >
              Ввести номер телефона
            </button>
            <button
              type="button"
              onClick={() => void handleLinkInvite()}
              className="w-full rounded-card border border-sage-200 bg-sage-50 px-4 py-4 text-left text-sm font-semibold text-sage-700 hover:bg-sage-100 dark:border-sage-700/50 dark:bg-sage-900/30 dark:text-sage-300 dark:hover:bg-sage-800/40"
            >
              Отправить ссылку-приглашение
            </button>
          </div>
        ) : null}

        {step === "phone" ? (
          <div className="space-y-4">
            <button
              type="button"
              onClick={() => setStep("menu")}
              className="text-sm font-semibold text-sage-700 dark:text-sage-300"
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
              onClick={() => void handlePhoneInvite()}
              disabled={!phone.trim()}
              className="pa-btn-primary w-full disabled:opacity-50"
            >
              Пригласить по номеру
            </button>
          </div>
        ) : null}

        {step === "share" && lastInvite ? (
          <section className="space-y-4">
            <p className="text-sm text-graphite-700 dark:text-pa-muted">
              Ссылка готова. Отправьте её человеку в Telegram — он сможет
              принять приглашение в боте.
            </p>
            <div className="rounded-card border border-warm/30 bg-warm/10 p-4 dark:border-food/30 dark:bg-food-soft/40">
              <p className="text-xs font-bold uppercase text-graphite-700 dark:text-pa-muted">
                Ссылка-приглашение
              </p>
              <p className="mt-2 break-all text-xs text-graphite-700 dark:text-pa-foreground">
                {lastInvite.deep_link}
              </p>
            </div>
            <button
              type="button"
              onClick={handleShare}
              className="pa-btn-primary w-full"
            >
              Отправить приглашение в Telegram
            </button>
            <button
              type="button"
              onClick={() => setStep("menu")}
              className="pa-btn-ghost w-full"
            >
              Создать другое приглашение
            </button>
          </section>
        ) : null}

        {step === "sent" && lastInvite ? (
          <section className="space-y-4 py-2 text-center">
            {lastInvite.invitee_notified && lastInvite.invited_phone_masked ? (
              <p className="text-sm text-sage-700 dark:text-sage-300">
                Приглашение отправлено в бот ({lastInvite.invited_phone_masked}
                ). Ожидаем ответ.
              </p>
            ) : (
              <p className="text-sm text-sage-700 dark:text-sage-300">
                Ссылка отправлена — ожидаем, когда человек примет приглашение
                в Telegram.
              </p>
            )}
            <button type="button" onClick={handleClose} className="pa-btn-primary w-full">
              Готово
            </button>
          </section>
        ) : null}
      </div>
    </div>
  );
}
