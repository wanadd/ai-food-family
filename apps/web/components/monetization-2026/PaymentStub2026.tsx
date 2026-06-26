"use client";

import { useRouter } from "next/navigation";

import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import { MONETIZATION_PATHS } from "@/lib/monetization/paths";

export function PaymentStub2026() {
  const router = useRouter();

  return (
    <div className="space-y-4 px-4 py-6">
      <Card2026>
        <p className="pa26-micro text-pa-muted">Тариф</p>
        <h1 className="pa26-page-title mt-1">Смена тарифа недоступна</h1>
        <p className="pa26-body mt-3 text-pa-muted">
          Тариф и доступ управляются администратором. Для изменения обратитесь в
          поддержку.
        </p>
      </Card2026>

      <Button2026
        size="wide"
        onClick={() => router.push(MONETIZATION_PATHS.subscription)}
      >
        Ваш тариф
      </Button2026>
    </div>
  );
}
