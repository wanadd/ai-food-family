import { roleLabel } from "@/lib/family/labels";
import type { FamilyRole } from "@/lib/family/types";

const ROLE_STYLES: Record<FamilyRole, string> = {
  admin: "bg-violet-100 text-violet-800",
  adult: "bg-sky-100 text-sky-800",
  child: "bg-amber-100 text-amber-800",
};

export function RoleBadge({ role }: { role: FamilyRole }) {
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${ROLE_STYLES[role]}`}
    >
      {roleLabel(role)}
    </span>
  );
}
