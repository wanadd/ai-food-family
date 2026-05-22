import { apiUrl } from "@/lib/api";

import type { FamilyInvite } from "./invite-types";
import type { Family, FamilyMember, MemberDraft } from "./types";

async function familyFetch<T>(
  path: string,
  initData: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
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
    headers: { "X-Telegram-Init-Data": initData },
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
): Promise<Family> {
  return familyFetch<Family>("/families", initData, {
    method: "POST",
    body: JSON.stringify({ name }),
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
