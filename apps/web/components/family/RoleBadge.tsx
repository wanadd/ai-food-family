import { roleLabel } from "@/lib/family/labels";
import type { FamilyRole } from "@/lib/family/types";

const ROLE_STYLES: Record<FamilyRole, string> = {
  admin: "bg-sage-50 text-sage-700",
  adult: "bg-olive/20 text-graphite-700",
  child: "bg-warm/10 text-graphite-700",
};

export function RoleBadge({ role }: { role: FamilyRole }) {
  return (
    <span
      className={`rounded-pill px-2.5 py-0.5 text-xs font-semibold ${ROLE_STYLES[role]}`}
    >
      {roleLabel(role)}
    </span>
  );
}
