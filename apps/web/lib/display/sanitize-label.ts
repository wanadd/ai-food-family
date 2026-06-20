import {
  isAuditPersona,
  type AuditPersona,
} from "@/lib/audit/personas";

const AUDIT_SUFFIX = /\s*\(audit\)\s*$/i;
const AUDIT_PREFIX_IN_NAME = /^Audit\s+/i;

/** Human-readable names for audit harness personas on user-facing screens. */
export const AUDIT_ACCOUNT_DISPLAY_NAMES: Record<AuditPersona, string> = {
  audit_new_user: "Иван",
  audit_personal_day5: "Иван",
  audit_family_admin: "Иван",
  audit_family_adult: "Анна",
  audit_family_child: "Ребёнок",
  audit_athlete: "Иван",
  audit_strict_diet: "Иван",
  audit_healthy_eating: "Иван",
  audit_start_trial: "Иван",
  audit_personal_plus: "Иван",
  audit_pair: "Иван",
  audit_family: "Иван",
  audit_family_pro: "Иван",
};

/** Remove test harness suffix from user-visible labels. */
export function stripAuditSuffix(text: string | null | undefined): string {
  return (text ?? "").replace(AUDIT_SUFFIX, "").trim();
}

export function formatUserDisplayName(
  first?: string | null,
  last?: string | null,
): string {
  const parts = [first, last]
    .map((p) => stripAuditSuffix(p))
    .filter(Boolean);
  return parts.join(" ").trim();
}

function resolveAuditPersonaKey(
  username?: string | null,
  first?: string | null,
): AuditPersona | null {
  if (username && isAuditPersona(username)) {
    return username;
  }
  const slug = stripAuditSuffix(first ?? "")
    .toLowerCase()
    .replace(/\s+/g, "_");
  if (slug.startsWith("audit_") && isAuditPersona(slug)) {
    return slug;
  }
  return null;
}

/** Display name for profile/account — never shows "(audit)" or raw audit slugs. */
export function formatAccountDisplayName(
  first?: string | null,
  last?: string | null,
  username?: string | null,
): string {
  const persona = resolveAuditPersonaKey(username, first);
  if (persona) {
    return AUDIT_ACCOUNT_DISPLAY_NAMES[persona];
  }

  const cleaned = formatUserDisplayName(first, last);
  if (cleaned && !AUDIT_PREFIX_IN_NAME.test(cleaned)) {
    return cleaned;
  }

  return "Пользователь";
}

/** Username line on account — hides @audit_* slugs. */
export function formatAccountUsernameLabel(
  username?: string | null,
): string {
  if (!username || isAuditPersona(username)) {
    return "Ваш аккаунт";
  }
  return `@${username}`;
}

/** Short name for mobile greeting — avoids mid-word truncation. */
export function formatGreetingName(
  displayName: string | null | undefined,
  maxLen = 20,
): string {
  const clean = stripAuditSuffix(displayName?.trim() ?? "");
  if (!clean || AUDIT_PREFIX_IN_NAME.test(clean)) return "";
  if (clean.length <= maxLen) return clean;
  const firstWord = clean.split(/\s+/)[0];
  if (firstWord && firstWord.length <= maxLen) return firstWord;
  return `${clean.slice(0, maxLen - 1)}…`;
}
