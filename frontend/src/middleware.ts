/* ────────────────────────────────────────────────
   Middleware - Protect dashboard routes
   ──────────────────────────────────────────────── */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if user has a valid session cookie
  const sessionCookie = request.cookies.get("session")?.value;

  // Protect dashboard routes
  if (pathname.startsWith("/dashboard")) {
    if (!sessionCookie) {
      // Redirect to login if no session
      const loginUrl = new URL("/login", request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
