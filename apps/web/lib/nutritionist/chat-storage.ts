const STORAGE_KEY = "planam_nutritionist_chat";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  createdAt: string;
};

export function loadChatMessages(): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as ChatMessage[];
  } catch {
    return [];
  }
}

export function saveChatMessages(messages: ChatMessage[]): void {
  if (typeof window === "undefined") return;
  const trimmed = messages.slice(-40);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
}

export function appendChatMessage(
  messages: ChatMessage[],
  role: ChatMessage["role"],
  text: string,
): ChatMessage[] {
  const next: ChatMessage = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    text,
    createdAt: new Date().toISOString(),
  };
  const updated = [...messages, next];
  saveChatMessages(updated);
  return updated;
}
