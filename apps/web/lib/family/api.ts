import { apiUrl } from "@/lib/api";
import { buildProtectedRequestHeaders } from "@/lib/audit/audit-mode";
import type {
  Family,
  FamilyMember,
  MemberDraft,
  VirtualMemberDraft,
  VirtualNutrition,
} from "./types";

async function familyFetch<T>(
  path: string,
  initData: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...buildProtectedRequestHeaders(initData),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function fetchMyFamily(initData: string): Promise<Family | null> {
  const response = await fetch(`${apiUrl}/families/me`, {
    headers: buildProtectedRequestHeaders(initData),
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    return null;
  }

  const text = await response.text();
  if (!text) {
    return null;
  }

  return JSON.parse(text) as Family;
}

export async function createFamily(
  initData: string,
  name: string,
  adminManageConsent: boolean,
): Promise<Family> {
  return familyFetch<Family>("/families", initData, {
    method: "POST",
    body: JSON.stringify({ name, admin_manage_consent: adminManageConsent }),
  });
}

export async function addFamilyMember(
  initData: string,
  familyId: number,
  draft: MemberDraft,
): Promise<FamilyMember> {
  return familyFetch<FamilyMember>(`/families/${familyId}/members`, initData, {
    method: "POST",
    body: JSON.stringify(draft),
  });
}

export async function updateFamilyMember(
  initData: string,
  familyId: number,
  memberId: number,
  draft: Partial<MemberDraft>,
): Promise<FamilyMember> {
  return familyFetch<FamilyMember>(
    `/families/${familyId}/members/${memberId}`,
    initData,
    {
      method: "PATCH",
      body: JSON.stringify(draft),
    },
  );
}

export async function inviteFamilyMemberByPhone(
  initData: string,
  familyId: number,
  phoneNumber: string,
): Promise<FamilyInvite> {
  return familyFetch<FamilyInvite>(
    `/families/${familyId}/invite-by-phone`,
    initData,
    {
      method: "POST",
      body: JSON.stringify({ phone_number: phoneNumber }),
    },
  );
}

export async function fetchFamilyInvites(
  initData: string,
  familyId: number,
): Promise<FamilyInvite[]> {
  return familyFetch<FamilyInvite[]>(
    `/families/${familyId}/invites`,
    initData,
  );
}

export async function createFamilyInviteLink(
  initData: string,
  familyId: number,
): Promise<FamilyInvite> {
  return familyFetch<FamilyInvite>(
    `/families/${familyId}/invites/link`,
    initData,
    { method: "POST", body: "{}" },
  );
}

export async function removeFamilyMember(
  initData: string,
  familyId: number,
  memberId: number,
): Promise<void> {
  await familyFetch<void>(`/families/${familyId}/members/${memberId}`, initData, {
    method: "DELETE",
  });
}

export async function addVirtualFamilyMember(
  initData: string,
  familyId: number,
  draft: VirtualMemberDraft,
): Promise<FamilyMember> {
  return familyFetch<FamilyMember>(
    `/families/${familyId}/members/virtual`,
    initData,
    {
      method: "POST",
      body: JSON.stringify(draft),
    },
  );
}

export async function updateMemberNutrition(
  initData: string,
  familyId: number,
  memberId: number,
  nutrition: VirtualNutrition,
): Promise<FamilyMember> {
  return familyFetch<FamilyMember>(
    `/families/${familyId}/members/${memberId}/nutrition`,
    initData,
    {
      method: "PUT",
      body: JSON.stringify({ nutrition }),
    },
  );
}

export async function setAllowAdminProfileEdit(
  initData: string,
  allow: boolean,
): Promise<FamilyMember> {
  return familyFetch<FamilyMember>("/families/me/allow-admin-edit", initData, {
    method: "PATCH",
    body: JSON.stringify({ allow_admin_profile_edit: allow }),
  });
}

export async function renameFamily(
  initData: string,
  name: string,
): Promise<Family> {
  return familyFetch<Family>("/families/me", initData, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export async function deleteFamily(initData: string): Promise<void> {
  await familyFetch<void>("/families/me", initData, { method: "DELETE" });
}

export async function leaveFamily(initData: string): Promise<void> {
  await familyFetch<void>("/families/me/leave", initData, { method: "POST" });
}

export async function transferFamilyAdmin(
  initData: string,
  memberId: number,
): Promise<Family> {
  return familyFetch<Family>("/families/me/transfer-admin", initData, {
    method: "POST",
    body: JSON.stringify({ member_id: memberId }),
  });
}
