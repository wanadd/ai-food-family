import {
  AUDIT_PERSONA_STORAGE_KEY,
  DEFAULT_AUDIT_PERSONA,
  isAuditPersona,
  type AuditPersona,
} from "@/lib/audit/personas";

const AUDIT_INIT_PREFIX = "planam-audit-v1:";

/** True only in non-production builds with explicit public flag. */
export function isAuditModeEnabled(): boolean {
  if (typeof process !== "undefined" && process.env.NODE_ENV === "production") {
    return false;
  }
  return process.env.NEXT_PUBLIC_PLANAM_AUDIT_MODE === "true";
}

export function getAuditSecret(): string {
  return process.env.NEXT_PUBLIC_PLANAM_AUDIT_SECRET ?? "";
}

export function auditInitDataForPersona(persona: AuditPersona): string {
  return `${AUDIT_INIT_PREFIX}${persona}`;
}

export function isAuditInitData(initData: string): boolean {
  return initData.startsWith(AUDIT_INIT_PREFIX);
}

export function personaFromAuditInitData(initData: string): AuditPersona | null {
  if (!isAuditInitData(initData)) return null;
  const slug = initData.slice(AUDIT_INIT_PREFIX.length);
  return isAuditPersona(slug) ? slug : null;
}

export function getStoredAuditPersona(): AuditPersona {
  if (typeof window === "undefined") {
    return DEFAULT_AUDIT_PERSONA;
  }
  const stored = window.localStorage.getItem(AUDIT_PERSONA_STORAGE_KEY);
  if (stored && isAuditPersona(stored)) {
    return stored;
  }
  return DEFAULT_AUDIT_PERSONA;
}

export function storeAuditPersona(persona: AuditPersona): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUDIT_PERSONA_STORAGE_KEY, persona);
}

export function clearAuditPersona(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUDIT_PERSONA_STORAGE_KEY);
}

/** Read `?auditPersona=` from URL and persist when audit mode is on. */
export function syncAuditPersonaFromUrl(): AuditPersona | null {
  if (typeof window === "undefined" || !isAuditModeEnabled()) {
    return null;
  }
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("auditPersona");
  if (raw && isAuditPersona(raw)) {
    storeAuditPersona(raw);
    return raw;
  }
  return null;
}

export function buildAuditHeaders(persona: AuditPersona): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Planam-Audit-Persona": persona,
    "X-Planam-Audit-User": persona,
  };
  const secret = getAuditSecret();
  if (secret) {
    headers["X-Planam-Audit-Secret"] = secret;
  }
  return headers;
}

/** Audit personas that should skip onboarding redirect (pre-seeded / returning). */
export function auditPersonaSkipsOnboarding(persona: AuditPersona): boolean {
  return persona !== "audit_new_user";
}
