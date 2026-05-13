import { NextRequest, NextResponse } from "next/server";
import { signOut } from "@/auth";

export async function POST(req: NextRequest) {
  const callbackUrl = req.nextUrl.searchParams.get("callbackUrl") || "/";

  await signOut({ redirect: false });

  const response = NextResponse.redirect(new URL(callbackUrl, req.nextUrl.origin));

  // Double-clear all possible cookie names
  const cookieNames = [
    "authjs.session-token",
    "__Secure-authjs.session-token",
    "__Host-authjs.session-token",
    "authjs.csrf-token",
    "__Host-authjs.csrf-token",
    "authjs.callback-url",
    "next-auth.session-token",
    "__Secure-next-auth.session-token",
  ];

  cookieNames.forEach((name) => {
    response.cookies.set(name, "", {
      maxAge: 0,
      path: "/",
      httpOnly: true,
      secure: name.startsWith("__"),
      sameSite: "lax",
    });
  });

  return response;
}
