import { HealthStatus } from "@/components/HealthStatus";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <section className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-600">
          Telegram Mini App
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">
          AI Food Family
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-600">
          Monorepo готов: Next.js + Tailwind на фронте, FastAPI на бэке,
          PostgreSQL и Redis в Docker Compose.
        </p>

        <div className="mt-6 space-y-3 border-t border-slate-200 pt-6">
          <div>
            <span className="text-sm text-slate-500">Backend API</span>
            <code className="mt-1 block break-all text-sm text-slate-800">
              {apiUrl}
            </code>
          </div>
          <HealthStatus apiUrl={apiUrl} />
        </div>
      </section>
    </main>
  );
}
