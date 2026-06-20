import { apiUrl } from "@/lib/api";
import { buildProtectedRequestHeaders } from "@/lib/audit/audit-mode";

export type LegalDocument = {
  id: string;
  title: string;
  url: string;
  stub_text: string;
  version: string;
};

export type LegalStatus = {
  version: string;
  accepted_terms: boolean;
  accepted_privacy: boolean;
  accepted_personal_data: boolean;
  legal_accepted_at: string | null;
  documents_up_to_date: boolean;
  can_use_app: boolean;
  phone_number: string | null;
  phone_skipped: boolean;
};

export async function fetchLegalDocuments(): Promise<{
  version: string;
  documents: LegalDocument[];
}> {
  const res = await fetch(`${apiUrl}/legal/documents`);
  if (!res.ok) throw new Error("Не удалось загрузить документы");
  return res.json();
}

export async function fetchLegalStatus(initData: string): Promise<LegalStatus> {
  const res = await fetch(`${apiUrl}/legal/status`, {
    headers: buildProtectedRequestHeaders(initData),
  });
  if (!res.ok) throw new Error("Не удалось проверить согласия");
  return res.json();
}

export async function acceptLegal(
  initData: string,
  payload: {
    accepted_terms: boolean;
    accepted_privacy: boolean;
    accepted_personal_data: boolean;
  },
): Promise<LegalStatus> {
  const res = await fetch(`${apiUrl}/legal/accept`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...buildProtectedRequestHeaders(initData),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(data?.detail ?? "Не удалось сохранить согласия");
  }
  return res.json();
}

export async function skipPhone(initData: string): Promise<LegalStatus> {
  const res = await fetch(`${apiUrl}/legal/skip-phone`, {
    method: "POST",
    headers: buildProtectedRequestHeaders(initData),
  });
  if (!res.ok) throw new Error("Не удалось пропустить телефон");
  return res.json();
}

export async function requestDataDeletion(initData: string): Promise<{
  status: string;
  message: string;
  request_id: string | null;
}> {
  const res = await fetch(`${apiUrl}/legal/delete-data-request`, {
    method: "POST",
    headers: buildProtectedRequestHeaders(initData),
  });
  if (!res.ok) throw new Error("Не удалось отправить запрос");
  return res.json();
}
