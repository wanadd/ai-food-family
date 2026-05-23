"use client";

import { useEffect, useRef, useState } from "react";

import { useTelegram } from "@/components/TelegramProvider";
import { askNutritionist } from "@/lib/nutritionist/api";
import {
  appendChatMessage,
  loadChatMessages,
  type ChatMessage,
} from "@/lib/nutritionist/chat-storage";
import { buildFallbackReply } from "@/lib/nutritionist/chat-fallback";
import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { AppMode } from "@/lib/app-mode/types";
import type { MenuVariant } from "@/lib/menu/types";

type NutritionistChatProps = {
  mode: AppMode;
  profile: NutritionProfileData | null;
  menu: MenuVariant | null;
  initialPrompt?: string | null;
  onInitialPromptConsumed?: () => void;
};

export function NutritionistChat({
  mode,
  profile,
  menu,
  initialPrompt,
  onInitialPromptConsumed,
}: NutritionistChatProps) {
  const { initData } = useTelegram();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(loadChatMessages());
  }, []);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (!initialPrompt) return;
    void sendMessage(initialPrompt);
    onInitialPromptConsumed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialPrompt]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;

    setSending(true);
    setInput("");
    const withUser = appendChatMessage(messages, "user", trimmed);
    setMessages(withUser);

    let answer: string;
    if (initData) {
      try {
        const res = await askNutritionist(initData, mode, trimmed);
        answer = res.answer;
      } catch {
        answer = buildFallbackReply(trimmed, profile, menu);
      }
    } else {
      answer = buildFallbackReply(trimmed, profile, menu);
    }

    setMessages((prev) => appendChatMessage(prev, "assistant", answer));
    setSending(false);
  }

  return (
    <section
      id="nutritionist-chat"
      className="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm"
    >
      <h2 className="text-sm font-bold text-stone-900">Спросить нутрициолога</h2>

      <div
        ref={listRef}
        className="mt-3 max-h-52 space-y-2 overflow-y-auto rounded-xl bg-stone-50 p-3"
      >
        {messages.length === 0 ? (
          <p className="text-sm text-stone-500">
            Задайте вопрос о питании — ПланАм ответит с учётом вашей цели.
          </p>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`rounded-xl px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "ml-6 bg-emerald-600 text-white"
                  : "mr-4 bg-white text-stone-800 shadow-sm"
              }`}
            >
              {msg.text}
            </div>
          ))
        )}
      </div>

      <form
        className="mt-3 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void sendMessage(input);
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ваш вопрос…"
          disabled={sending}
          className="min-h-[44px] flex-1 rounded-xl border border-stone-200 px-3 text-sm text-stone-900 outline-none focus:border-emerald-500"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="min-h-[44px] shrink-0 rounded-xl bg-emerald-600 px-4 text-sm font-semibold text-white disabled:opacity-50"
        >
          {sending ? "…" : "→"}
        </button>
      </form>
    </section>
  );
}
