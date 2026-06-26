"use client";

type TelegramRequiredScreenProps = {
  message: string;
};

export function TelegramRequiredScreen({ message }: TelegramRequiredScreenProps) {
  const blocked = message.includes("ограничен");
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center px-6 text-center">
      <p className="text-4xl" aria-hidden>
        {blocked ? "🔒" : "📱"}
      </p>
      <h1 className="mt-4 text-lg font-bold text-stone-900">
        {blocked ? "Доступ ограничен" : "Нужен Telegram"}
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-stone-600">{message}</p>
    </div>
  );
}
