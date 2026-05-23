"use client";

import { useEffect, useId, useRef, useState } from "react";

import type { SelectOption } from "@/lib/family/virtual-member-options";

type MultiSelectFieldProps = {
  label: string;
  options: SelectOption[];
  value: string[];
  customValues: string[];
  onChange: (value: string[], customValues: string[]) => void;
  exclusiveNone?: string;
  customPlaceholder?: string;
  hint?: string;
};

function labelFor(
  options: SelectOption[],
  customValues: string[],
  value: string,
): string {
  const preset = options.find((o) => o.value === value);
  if (preset) return preset.label;
  return customValues.includes(value) ? value : value;
}

export function MultiSelectField({
  label,
  options,
  value,
  customValues,
  onChange,
  exclusiveNone = "none",
  customPlaceholder = "Добавить своё значение",
  hint,
}: MultiSelectFieldProps) {
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [customDraft, setCustomDraft] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const selectedLabels = value.map((v) =>
    labelFor(options, customValues, v),
  );
  const showOther = value.includes("other");

  function toggle(optionValue: string) {
    if (optionValue === exclusiveNone) {
      onChange([exclusiveNone], []);
      return;
    }
    let next = value.filter((v) => v !== exclusiveNone);
    if (next.includes(optionValue)) {
      next = next.filter((v) => v !== optionValue);
    } else {
      next = [...next, optionValue];
    }
    onChange(next, customValues);
  }

  function removeChip(chipValue: string) {
    if (options.some((o) => o.value === chipValue)) {
      onChange(
        value.filter((v) => v !== chipValue),
        customValues,
      );
      return;
    }
    onChange(
      value.filter((v) => v !== chipValue),
      customValues.filter((c) => c !== chipValue),
    );
  }

  function addCustom() {
    const trimmed = customDraft.trim();
    if (!trimmed) return;
    const nextCustom = customValues.includes(trimmed)
      ? customValues
      : [...customValues, trimmed];
    const nextValue = value.includes(trimmed)
      ? value.filter((v) => v !== exclusiveNone)
      : [...value.filter((v) => v !== exclusiveNone), trimmed];
    onChange(nextValue, nextCustom);
    setCustomDraft("");
  }

  return (
    <div ref={rootRef} className="relative">
      <span className="mb-1.5 block text-sm font-medium text-stone-700">
        {label}
      </span>
      {hint ? <p className="mb-2 text-xs text-stone-500">{hint}</p> : null}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={listId}
        className="flex w-full items-center justify-between rounded-xl border border-stone-200 bg-white px-4 py-3 text-left text-sm text-stone-700"
      >
        <span className="truncate">
          {selectedLabels.length
            ? `Выбрано: ${selectedLabels.length}`
            : "Выберите из списка"}
        </span>
        <span className="ml-2 text-stone-400" aria-hidden>
          {open ? "▲" : "▼"}
        </span>
      </button>

      {value.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {value.map((chip) => (
            <span
              key={chip}
              className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-900 ring-1 ring-emerald-100"
            >
              {labelFor(options, customValues, chip)}
              <button
                type="button"
                onClick={() => removeChip(chip)}
                className="rounded-full px-1 text-emerald-700 hover:bg-emerald-100"
                aria-label={`Убрать ${labelFor(options, customValues, chip)}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      ) : null}

      {open ? (
        <ul
          id={listId}
          className="absolute z-20 mt-1 max-h-52 w-full overflow-y-auto rounded-xl border border-stone-200 bg-white py-1 shadow-lg"
        >
          {options.map((opt) => {
            const checked = value.includes(opt.value);
            return (
              <li key={opt.value}>
                <button
                  type="button"
                  onClick={() => toggle(opt.value)}
                  className={`flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm ${
                    checked
                      ? "bg-emerald-50 font-medium text-emerald-900"
                      : "text-stone-700 hover:bg-stone-50"
                  }`}
                >
                  <span
                    className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                      checked
                        ? "border-emerald-600 bg-emerald-600 text-white"
                        : "border-stone-300"
                    }`}
                    aria-hidden
                  >
                    {checked ? "✓" : ""}
                  </span>
                  {opt.label}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}

      {showOther ? (
        <div className="mt-2 flex gap-2">
          <input
            value={customDraft}
            onChange={(e) => setCustomDraft(e.target.value)}
            placeholder={customPlaceholder}
            className="min-w-0 flex-1 rounded-xl border border-stone-200 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addCustom();
              }
            }}
          />
          <button
            type="button"
            onClick={addCustom}
            className="shrink-0 rounded-xl bg-stone-100 px-3 py-2 text-sm font-semibold text-stone-800"
          >
            +
          </button>
        </div>
      ) : null}
    </div>
  );
}
