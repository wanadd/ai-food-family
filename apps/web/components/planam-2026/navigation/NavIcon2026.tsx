import type { Nav2026IconId } from "@/lib/navigation/nav-config-2026";
import { cn } from "@/lib/planam/cn";

type NavIcon2026Props = {
  id: Nav2026IconId;
  className?: string;
};

/** Inline SVG icons — id задаётся только из nav-config-2026. */
export function NavIcon2026({ id, className }: NavIcon2026Props) {
  const base = cn("size-5 shrink-0", className);

  switch (id) {
    case "plan":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <rect x="4" y="5" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="1.75" />
          <path d="M8 3v4M16 3v4M4 10h16" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
          <path d="M9 14h2M13 14h2M9 17h2" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
        </svg>
      );
    case "home":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M4 10.5L12 4l8 6.5V20a1 1 0 01-1 1h-5v-6H10v6H5a1 1 0 01-1-1v-9.5z"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "wellness":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.75" />
          <path
            d="M12 8v4l2.5 1.5"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "events":
    case "calendar-star":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <rect x="4" y="5" width="16" height="15" rx="2" stroke="currentColor" strokeWidth="1.75" />
          <path d="M8 3v4M16 3v4M4 10h16" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
          <path
            d="M12 13l1.2 2.4 2.6.4-1.9 1.8.5 2.6L12 18.8l-2.4 1.4.5-2.6-1.9-1.8 2.6-.4L12 13z"
            fill="currentColor"
            stroke="none"
          />
        </svg>
      );
    case "account":
    case "profile":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.75" />
          <path
            d="M5 20c0-3.3 3.1-5.5 7-5.5s7 2.2 7 5.5"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      );
    case "shopping":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M6 6h15l-1.5 9H8L6 6zM9 20a1 1 0 100-2 1 1 0 000 2zm8 0a1 1 0 100-2 1 1 0 000 2z"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "pantry":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <rect
            x="5"
            y="7"
            width="14"
            height="13"
            rx="2"
            stroke="currentColor"
            strokeWidth="1.75"
          />
          <path d="M9 7V5h6v2" stroke="currentColor" strokeWidth="1.75" />
        </svg>
      );
    case "recipes":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M4 10h16M6 10V8a2 2 0 012-2h8a2 2 0 012 2v2M7 10v8a1 1 0 001 1h8a1 1 0 001-1v-8"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
          <path d="M9 14h6" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
        </svg>
      );
    case "today":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.75" />
          <path d="M12 8v4l3 2" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
        </svg>
      );
    case "family":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="16" cy="10" r="2" stroke="currentColor" strokeWidth="1.5" />
          <path
            d="M3 19c0-2.5 2.7-4 6-4M14 19c0-2 1.8-3.5 5-3.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      );
    case "subscription":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M6 9l6-4 6 4v8l-6 4-6-4V9z"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "notifications":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M12 4a4 4 0 014 4v3l2 3H6l2-3V8a4 4 0 014-4z"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
          <path d="M10 18a2 2 0 004 0" stroke="currentColor" strokeWidth="1.75" />
        </svg>
      );
    case "settings":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.75" />
          <path
            d="M12 4v2M12 18v2M4 12h2M18 12h2M6.3 6.3l1.4 1.4M16.3 16.3l1.4 1.4M6.3 17.7l1.4-1.4M16.3 7.7l1.4-1.4"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      );
    case "theme":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.75" />
          <path
            d="M12 2v2M12 20v2M2 12h2M20 12h2"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      );
    case "legal":
      return (
        <svg className={base} viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M8 4h8v16H8zM10 8h4M10 12h4M10 16h3"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
        </svg>
      );
    default:
      return (
        <span className={cn("inline-block size-5 rounded-full bg-sage-200", className)} aria-hidden />
      );
  }
}
