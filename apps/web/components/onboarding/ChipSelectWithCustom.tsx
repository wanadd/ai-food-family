"use client";

import { useState } from "react";

import type { SelectOption } from "@/lib/onboarding/options";

import { ChipSelect } from "./ChipSelect";

type ChipSelectWithCustomProps = {
  options: SelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  exclusiveNone?: string;
  customPlaceholder?: string;
};

function labelForValue(options: SelectOption[], value: string): string {
  const found = options.find((o) => o.value === value);
  return found?.label ?? value;
}

export function ChipSelectWithCustom({
  options,
  value,
  onChange,
  exclusiveNone,
  customPlaceholder = "Своё — введите и нажмите «Добавить»",
}: ChipSelectWithCustomProps) {
  const [customText, setCustomText] = useState("");
  const presetValues = new Set(options.map((o) => o.value));
  const customTags = value.filter((v) => !presetValues.has(v));

  function addCustom() {
    const tag = customText.trim();
    if (!tag) return;
    const key = tag.toLowerCase().replace(/\s+/g, "_");
    const next = exclusiveNone
      ? value.filter((v) => v !== exclusiveNone)
      : [...value];
    if (!next.includes(key)) {
      onChange([...next, key]);
    }
    setCustomText("");
  }

  function removeCustom(tag: string) {
    onChange(value.filter((v) => v !== tag));
  }

  return (
    <div className="space-y-3">
      <ChipSelect
        options={options}
        value={value}
        onChange={onChange}
        exclusiveNone={exclusiveNone}
      />

      <div className="flex gap-2">
        <input
          type="text"
          value={customText}
          onChange={(e) => setCustomText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addCustom();
            }
          }}
          placeholder={customPlaceholder}
          className="min-w-0 flex-1 rounded-xl border border-stone-200 px-3 py-2.5 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
        />
        <button
          type="button"
          onClick={addCustom}
          disabled={!customText.trim()}
          className="shrink-0 rounded-xl border border-stone-200 px-3 py-2.5 text-sm font-semibold text-stone-700 disabled:opacity-40"
        >
          Добавить
        </button>
      </div>

      {customTags.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {customTags.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => removeCustom(tag)}
              className="rounded-full border border-emerald-600 bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-900"
            >
              {labelForValue(options, tag)} ×
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
