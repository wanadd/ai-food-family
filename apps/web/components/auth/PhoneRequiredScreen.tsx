"use client";

export function PhoneRequiredScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#fafaf9] p-6">
      <section className="w-full max-w-md rounded-[24px] border border-emerald-100 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-semibold text-emerald-700">ПланАм</p>
        <h1 className="mt-3 text-2xl font-bold text-stone-900">
          Нужен номер телефона
        </h1>
        <p className="mt-4 text-sm leading-relaxed text-stone-600">
          Mini App и команды бота доступны только после подтверждения номера.
        </p>
        <ol className="mt-6 space-y-3 text-left text-sm text-stone-700">
          <li>1. Откройте чат с ботом ПланАм</li>
          <li>2. Отправьте команду /start</li>
          <li>3. Нажмите «Поделиться номером»</li>
          <li>4. Вернитесь сюда и обновите приложение</li>
        </ol>
        <p className="mt-6 text-xs text-stone-400">
          После этого можно приглашать в семью по номеру и пользоваться меню.
        </p>
      </section>
    </div>
  );
}
