"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type BottomBackButtonProps = {
  className?: string;
};

export function BottomBackButton({ className = "" }: BottomBackButtonProps) {
  const router = useRouter();
  const [label, setLabel] = useState("На главную");

  useEffect(() => {
    setLabel(window.history.length > 1 ? "Назад" : "На главную");
  }, []);

  function handleClick() {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
      return;
    }
    router.push("/");
  }

  return (
    <div className={`mx-auto w-full max-w-lg px-5 ${className}`}>
      <button
        type="button"
        onClick={handleClick}
        className="w-full rounded-2xl border border-stone-200 bg-white py-3.5 text-sm font-semibold text-stone-700 shadow-sm transition active:scale-[0.99]"
      >
        {label}
      </button>
    </div>
  );
}
