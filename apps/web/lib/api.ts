const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type AuthUser = {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  language_code: string | null;
  phone_number: string | null;
  photo_url: string | null;
  accepted_terms?: boolean;
  accepted_privacy?: boolean;
  accepted_personal_data?: boolean;
  legal_accepted_at?: string | null;
  legal_documents_version?: string | null;
  phone_skipped?: boolean;
  created_at: string;
  updated_at: string;
};

export type TelegramAuthResponse = {
  user: AuthUser;
  is_new: boolean;
  phone_verified: boolean;
  legal_accepted?: boolean;
  can_use_app?: boolean;
};

export type DevLoginResponse = TelegramAuthResponse & {
  dev_init_data: string;
};

export async function authenticateDevLogin(): Promise<DevLoginResponse> {
  const response = await fetch(`${apiUrl}/auth/dev-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }

  return response.json() as Promise<DevLoginResponse>;
}

export async function authenticateWithTelegram(
  initData: string,
): Promise<TelegramAuthResponse> {
  const response = await fetch(`${apiUrl}/auth/telegram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData }),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }

  return response.json() as Promise<TelegramAuthResponse>;
}

export { apiUrl };
