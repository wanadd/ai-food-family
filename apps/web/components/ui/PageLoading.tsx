type PageLoadingProps = {
  message: string;
};

export function PageLoading({ message }: PageLoadingProps) {
  return (
    <div
      className="flex min-h-[50vh] flex-col items-center justify-center px-5 py-20"
      aria-busy="true"
      aria-live="polite"
    >
      <div
        className="h-8 w-8 animate-spin rounded-full border-2 border-stone-200 border-t-emerald-600"
        aria-hidden
      />
      <p className="mt-4 text-center text-sm font-medium text-stone-600">
        {message}
      </p>
    </div>
  );
}
