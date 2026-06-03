import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { resolveMigrationTarget } from "@/lib/navigation/route-migration-2026";

const UI_2026_ENABLED = process.env.NEXT_PUBLIC_PLANAM_UI_2026 === "true";
const REDIRECTS_ENABLED =
  process.env.NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS === "true";

export function middleware(request: NextRequest) {
  if (!UI_2026_ENABLED || !REDIRECTS_ENABLED) {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  if (pathname.startsWith("/admin") || pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  const target = resolveMigrationTarget(pathname);
  if (target && target !== pathname) {
    const url = request.nextUrl.clone();
    url.pathname = target;
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/menu/:path*",
    "/shopping/:path*",
    "/pantry/:path*",
    "/health/:path*",
    "/nutritionist/:path*",
    "/progress",
    "/profile",
    "/settings/:path*",
    "/recipes/:path*",
  ],
};
