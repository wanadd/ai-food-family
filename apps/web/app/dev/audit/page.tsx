"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { useTelegram } from "@/components/TelegramProvider";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { clearAll as clearSessionCache } from "@/lib/cache/session-cache";
import {
  AUDIT_PERSONAS,
  AUDIT_PERSONA_LABELS,
  type AuditPersona,
} from "@/lib/audit/personas";
import {
  clearAuditPersona,
  getStoredAuditPersona,
  isAuditModeEnabled,
  storeAuditPersona,
} from "@/lib/audit/audit-mode";
import { PLANAM_ROUTES } from "@/lib/planam/routes";
import { notFound } from "next/navigation";

const QUICK_ROUTES: { href: string; label: string }[] = [
  { href: "/", label: "Главная" },
  { href: PLANAM_ROUTES.planToday, label: "Меню сегодня" },
  { href: PLANAM_ROUTES.shopping, label: "Покупки" },
  { href: PLANAM_ROUTES.pantry, label: "Запасы" },
  { href: PLANAM_ROUTES.wellness, label: "Здоровье" },
  { href: "/plan/recipes", label: "Рецепты" },
  { href: "/account", label: "Профиль" },
  { href: "/account/subscription", label: "Тарифы" },
  { href: "/account/family", label: "Семья" },
];

export default function AuditDevPanelPage() {
  const router = useRouter();
  const { user, auditPersona, isAuditMode, retryAuth } = useTelegram();

  if (!isAuditModeEnabled()) {
    notFound();
  }

  const currentPersona = (auditPersona ?? getStoredAuditPersona()) as AuditPersona;

  const switchPersona = useCallback(
    (persona: AuditPersona) => {
      storeAuditPersona(persona);
      clearSessionCache();
      router.push(`/?auditPersona=${persona}`);
      retryAuth();
    },
    [router, retryAuth],
  );

  const resetLocal = useCallback(() => {
    clearAuditPersona();
    clearSessionCache();
    if (typeof window !== "undefined") {
      window.sessionStorage.clear();
    }
    router.refresh();
    retryAuth();
  }, [router, retryAuth]);

  return (
    <main className="mx-auto max-w-lg px-4 pb-12 pt-6">
      <p className="pa26-micro mb-1 text-warm">Local only · Audit harness</p>
      <h1 className="pa26-hero">PLANAM Audit Panel</h1>
      <p className="pa26-body mt-2 text-pa-muted">
        Переключение persona для UX-аудита без Telegram. Не доступно в production.
      </p>

      <section className="mt-6 rounded-2xl border border-pa-border bg-pa-surface p-4">
        <h2 className="pa26-section-title">Текущая сессия</h2>
        <dl className="mt-3 space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-pa-muted">Audit mode</dt>
            <dd>{isAuditMode ? "on" : "off"}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-pa-muted">Persona</dt>
            <dd className="font-mono text-xs">{currentPersona}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-pa-muted">User id</dt>
            <dd>{user?.id ?? "—"}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-pa-muted">Имя</dt>
            <dd>{user?.first_name ?? "—"}</dd>
          </div>
        </dl>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Personas</h2>
        <div className="flex flex-col gap-2">
          {AUDIT_PERSONAS.map((persona) => (
            <Button2026
              key={persona}
              variant={persona === currentPersona ? "primary" : "secondary"}
              onClick={() => switchPersona(persona)}
            >
              {AUDIT_PERSONA_LABELS[persona]}
            </Button2026>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="pa26-section-title mb-3">Маршруты</h2>
        <div className="flex flex-col gap-2">
          {QUICK_ROUTES.map((route) => (
            <Link
              key={route.href}
              href={`${route.href}?auditPersona=${currentPersona}`}
              className="rounded-xl border border-pa-border px-4 py-3 text-sm hover:bg-pa-surface"
            >
              {route.label}
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <Button2026 variant="danger" onClick={resetLocal}>
          Сбросить persona + session cache
        </Button2026>
      </section>
    </main>
  );
}
