import { auth } from "@/auth";
import { NextRequest, NextResponse } from "next/server";

const protectedRoutes = ["/dashboard", "/contract-review", "/legal-qa", "/settings", "/upgrade"];
const authRoutes = ["/login", "/register"];

export async function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Skip proxy for static assets and API routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api/auth") ||
    pathname === "/favicon.ico" ||
    pathname.startsWith("/public/")
  ) {
    return NextResponse.next();
  }

  // Only check auth for protected routes or auth routes
  const isProtected = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
  const isAuthRoute = authRoutes.includes(pathname);

  if (!isProtected && !isAuthRoute) {
    return NextResponse.next();
  }

  const session = await auth();

  if (isProtected && !session) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthRoute && session) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api/auth|public).*)",
  ],
};
