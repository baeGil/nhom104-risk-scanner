import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { jwtVerify } from "jose";
import { SignJWT } from "jose";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

async function verifyTempToken(token: string): Promise<{ userId: string } | null> {
  try {
    const secret = new TextEncoder().encode(
      process.env.AUTH_SECRET || "default-secret-change-in-production"
    );

    const { payload } = await jwtVerify(token, secret, {
      algorithms: ["HS256"],
    });

    if (payload.type !== "auto-login" || !payload.userId) {
      return null;
    }

    return { userId: payload.userId as string };
  } catch {
    return null;
  }
}

async function createSessionToken(userId: string, email: string, name: string, role: string): Promise<string> {
  const secret = new TextEncoder().encode(
    process.env.AUTH_SECRET || "default-secret-change-in-production"
  );

  return new SignJWT({
    id: userId,
    email,
    name,
    role,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(userId)
    .setIssuedAt()
    .setExpirationTime("15m") // 15 minutes (matches session maxAge)
    .sign(secret);
}

export async function POST(req: NextRequest) {
  try {
    const { tempToken } = await req.json();

    if (!tempToken) {
      return NextResponse.json(
        { error: "Thiếu token" },
        { status: 400 }
      );
    }

    // Verify temp token
    const result = await verifyTempToken(tempToken);
    if (!result) {
      return NextResponse.json(
        { error: "Token không hợp lệ hoặc đã hết hạn" },
        { status: 400 }
      );
    }

    // Get user info
    const { data: users } = await getSupabase()
      .from("users")
      .select("id, email, name, email_verified")
      .eq("id", result.userId)
      .limit(1);

    if (!users || users.length === 0) {
      return NextResponse.json(
        { error: "Không tìm thấy tài khoản" },
        { status: 404 }
      );
    }

    const user = users[0];

    // Get role
    const { data: roleData } = await getSupabase()
      .from("user_roles")
      .select("role")
      .eq("user_id", user.id)
      .single();

    const role = roleData?.role || "free";

    // Create session token
    const sessionToken = await createSessionToken(user.id, user.email, user.name, role);

    // Build response with redirect and session cookie
    const response = NextResponse.json(
      { success: true, redirect: "/dashboard" },
      { status: 200 }
    );

    // Set Auth.js session cookie
    response.cookies.set("authjs.session-token", sessionToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 15 * 60, // 15 minutes
    });

    return response;
  } catch (err) {
    console.error("Auto-login error:", err);
    return NextResponse.json(
      { error: "Lỗi server" },
      { status: 500 }
    );
  }
}
