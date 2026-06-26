"use client";

import { useMemo, useState } from "react";

import { useAppMode } from "@/components/app-mode/AppModeProvider";
import {
  V2BottomSheet,
  V2Button,
  V2Chip,
} from "@/components/planam-v2/ui/V2Primitives";
import { useTelegram } from "@/components/TelegramProvider";
import { getStoredAuditPersona, isAuditModeEnabled } from "@/lib/audit/audit-mode";
import { askNutritionist } from "@/lib/nutritionist/api";

const PROMPTS = [
  "Что съесть вечером?",
  "Как добрать белок?",
  "Я ел вне дома",
  "Я пропустил обед",
  "Можно заменить ужин?",
];

const AI_UNAVAILABLE_FALLBACK =
  "AI-нутрициолог временно недоступен. Данные дня сохранены, рекомендации PLANAM остаются на экране.";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
  fromFallback?: boolean;
};

function personaHint(): string {
  if (!isAuditModeEnabled()) return "";
  const persona = getStoredAuditPersona();
  if (persona === "audit_athlete") return "sport";
  if (persona === "audit_strict_diet") return "restriction";
  if (persona === "audit_family_pro") return "pro";
  if (persona === "audit_new_user") return "new";
  return "";
}

function safeLocalAnswer(question: string): string {
  const lower = question.toLowerCase();
  const persona = personaHint();

  if (persona === "new") {
    return "Сначала настройте питание: цель, ограничения и обычный режим дня. После этого я смогу подсказать точнее. Сегодня начните с простого приёма пищи с белком и овощами.";
  }
  if (lower.includes("аллер") || lower.includes("огранич") || persona === "restriction") {
    return "Если есть аллергия или медицинское ограничение, не рискуйте: выберите блюдо без спорного ингредиента и проверьте состав. Для диагноза и лечения лучше опираться на врача.";
  }
  if (lower.includes("пропуст") || lower.includes("обед")) {
    return "Не нужно догонять всё сразу. Сделайте следующий приём пищи обычным: белок, овощи и сложные углеводы. В «Здоровье» отметьте пропуск, чтобы баланс дня был честным.";
  }
  if (
    lower.includes("другое") ||
    lower.includes("вне") ||
    lower.includes("шаурм")
  ) {
    return "Отметьте «ел другое» и запишите, что именно съели. Дальше держите ужин легче: белок и овощи, без попытки наказать себя голодом.";
  }
  if (
    lower.includes("белок") ||
    lower.includes("трен") ||
    persona === "sport"
  ) {
    return "После тренировки удобнее добрать белок простым блюдом: творог, яйца, рыба, курица или бобовые. Ориентируйтесь на вашу дневную цель, а не на один идеальный приём.";
  }
  if (lower.includes("вечер") || lower.includes("ужин") || lower.includes("замен")) {
    return "Посмотрите ужин в меню на сегодня или выберите лёгкий вариант с белком и овощами. Если съели другое — отметьте это в приёме пищи.";
  }
  if (lower.includes("похуд")) {
    return "Для похудения важен умеренный дефицит и регулярность. Смотрите на калории за день, не пропускайте белок и добавьте овощи к следующему приёму пищи.";
  }
  if (persona === "pro") {
    return "PRO-разбор: начните с отметок по сегодняшним приёмам пищи, затем сравните план и факт по калориям и белку. Практический шаг — закрыть самый большой недобор без перегруза ужина.";
  }
  return "Отметьте факт питания в «Здоровье», посмотрите баланс дня и выберите следующий небольшой шаг: белок, овощи или вода. Советы не заменяют медицинскую консультацию.";
}

export function AiNutritionChatSheet({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { initData } = useTelegram();
  const { mode } = useAppMode();
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [aiUnavailable, setAiUnavailable] = useState(false);

  const suggested = useMemo(() => PROMPTS, []);

  async function send(text: string) {
    const question = text.trim();
    if (!question || sending) return;
    setSending(true);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);

    let answer = safeLocalAnswer(question);
    let fromFallback = !initData;

    if (initData) {
      try {
        const result = await askNutritionist(initData, mode, question);
        if (result.answer?.trim()) {
          answer = result.answer.trim();
          fromFallback = false;
          setAiUnavailable(false);
        } else {
          fromFallback = true;
          setAiUnavailable(true);
          answer = `${AI_UNAVAILABLE_FALLBACK}\n\n${safeLocalAnswer(question)}`;
        }
      } catch {
        fromFallback = true;
        setAiUnavailable(true);
        answer = `${AI_UNAVAILABLE_FALLBACK}\n\n${safeLocalAnswer(question)}`;
      }
    }

    setMessages((prev) => [
      ...prev,
      { role: "assistant", text: answer, fromFallback },
    ]);
    setSending(false);
  }

  return (
    <V2BottomSheet open={open} title="AI-нутрициолог" onClose={onClose}>
      <div className="space-y-3 pb-2">
        {aiUnavailable ? (
          <p
            className="rounded-control border border-ai/30 bg-ai-soft/50 px-3 py-2 pa26-micro text-pa-foreground"
            data-testid="wellness-ai-unavailable"
          >
            {AI_UNAVAILABLE_FALLBACK}
          </p>
        ) : (
          <p className="pa26-caption text-pa-muted">
            Короткий ответ с практическим следующим шагом.
          </p>
        )}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {suggested.map((prompt) => (
            <V2Chip
              key={prompt}
              label={prompt}
              onClick={() => {
                setInput(prompt);
                void send(prompt);
              }}
            />
          ))}
        </div>
        <div className="max-h-60 space-y-2 overflow-y-auto rounded-card border border-pa-border bg-pa-canvas p-2">
          {messages.length === 0 ? (
            <p className="pa26-caption text-pa-muted">
              Задайте вопрос — ответ будет коротким и с практическим следующим шагом.
            </p>
          ) : (
            messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                data-testid={
                  message.role === "assistant" ? "wellness-ai-answer" : undefined
                }
                className={
                  message.role === "user"
                    ? "ml-8 rounded-card bg-sage-500 px-3 py-2 pa26-caption text-white"
                    : "mr-4 rounded-card bg-pa-surface px-3 py-2 pa26-caption text-pa-foreground"
                }
              >
                {message.text}
              </div>
            ))
          )}
        </div>
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            void send(input);
          }}
        >
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Напишите, что вы съели или что хотите узнать"
            data-testid="wellness-ai-input"
            rows={2}
            className="min-w-0 flex-1 resize-none rounded-control border border-pa-border bg-pa-surface px-3 py-2.5 pa26-body outline-none focus:border-sage-400"
          />
          <V2Button
            variant="primary"
            disabled={!input.trim() || sending}
            loading={sending}
            data-testid="wellness-ai-send"
            onClick={() => void send(input)}
          >
            Отправить
          </V2Button>
        </form>
      </div>
    </V2BottomSheet>
  );
}
