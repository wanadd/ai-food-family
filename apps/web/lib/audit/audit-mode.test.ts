import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  auditInitDataForPersona,
  auditPersonaSkipsOnboarding,
  buildAuditHeaders,
  buildProtectedRequestHeaders,
  getAuditHeaders,
  getStoredAuditPersona,
  isAuditInitData,
  isAuditModeEnabled,
  personaFromAuditInitData,
  storeAuditPersona,
  syncAuditPersonaFromUrl,
} from "./audit-mode";

describe("audit-mode", () => {
  const env = { ...process.env };

  beforeEach(() => {
    vi.stubGlobal("localStorage", {
      store: {} as Record<string, string>,
      getItem(key: string) {
        return this.store[key] ?? null;
      },
      setItem(key: string, value: string) {
        this.store[key] = value;
      },
      removeItem(key: string) {
        delete this.store[key];
      },
    });
    vi.stubGlobal("window", {
      localStorage: (localStorage as unknown as Storage),
      location: { search: "" },
    });
  });

  afterEach(() => {
    process.env = { ...env };
    vi.unstubAllGlobals();
  });

  it("audit mode off when public flag missing", () => {
    process.env.NODE_ENV = "development";
    delete process.env.NEXT_PUBLIC_PLANAM_AUDIT_MODE;
    expect(isAuditModeEnabled()).toBe(false);
  });

  it("audit mode off in production even with flag", () => {
    process.env.NODE_ENV = "production";
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_MODE = "true";
    expect(isAuditModeEnabled()).toBe(false);
  });

  it("audit mode on in development with flag", () => {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_MODE = "true";
    expect(isAuditModeEnabled()).toBe(true);
  });

  it("auditPersona from URL stored", () => {
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_MODE = "true";
    window.location.search = "?auditPersona=audit_family_admin";
    const persona = syncAuditPersonaFromUrl();
    expect(persona).toBe("audit_family_admin");
    expect(getStoredAuditPersona()).toBe("audit_family_admin");
  });

  it("init data encodes persona", () => {
    const init = auditInitDataForPersona("audit_personal_day5");
    expect(isAuditInitData(init)).toBe(true);
    expect(personaFromAuditInitData(init)).toBe("audit_personal_day5");
  });

  it("API headers added only with persona", () => {
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_SECRET = "local-secret";
    const headers = buildAuditHeaders("audit_athlete");
    expect(headers["X-Planam-Audit-Persona"]).toBe("audit_athlete");
    expect(headers["X-Planam-Audit-Secret"]).toBe("local-secret");
  });

  it("non-new personas skip onboarding", () => {
    expect(auditPersonaSkipsOnboarding("audit_new_user")).toBe(false);
    expect(auditPersonaSkipsOnboarding("audit_personal_day5")).toBe(true);
  });

  it("storeAuditPersona persists", () => {
    storeAuditPersona("audit_pair");
    expect(getStoredAuditPersona()).toBe("audit_pair");
  });

  it("getAuditHeaders uses stored persona in audit mode", () => {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_MODE = "true";
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_SECRET = "local-secret";
    storeAuditPersona("audit_personal_day5");
    const headers = getAuditHeaders();
    expect(headers["X-Planam-Audit-Persona"]).toBe("audit_personal_day5");
    expect(headers["X-Planam-Audit-Secret"]).toBe("local-secret");
  });

  it("buildProtectedRequestHeaders adds audit init data and secret", () => {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_MODE = "true";
    process.env.NEXT_PUBLIC_PLANAM_AUDIT_SECRET = "local-secret";
    storeAuditPersona("audit_personal_day5");
    const headers = buildProtectedRequestHeaders("", "personal");
    expect(headers["X-Telegram-Init-Data"]).toBe(
      auditInitDataForPersona("audit_personal_day5"),
    );
    expect(headers["X-Planam-Audit-Secret"]).toBe("local-secret");
    expect(headers["X-App-Mode"]).toBe("personal");
  });
});
