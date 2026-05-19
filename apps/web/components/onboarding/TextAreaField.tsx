type TextAreaFieldProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
};

export function TextAreaField({ value, onChange, placeholder }: TextAreaFieldProps) {
  return (
    <textarea
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      rows={5}
      className="w-full resize-none rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-800 outline-none ring-emerald-500 transition placeholder:text-stone-400 focus:border-emerald-500 focus:ring-2"
    />
  );
}
