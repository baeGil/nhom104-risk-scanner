import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { validateOtpForUser } from "@/lib/otp";
import { signIn } from "@/auth";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

function getClientIp(req: NextRequest): string {
  return req.headers.get("x-forwarded-for")?.split(",")[0] || "127.0.0.1";
}

export async function POST(req: NextRequest) {
  try {
    const { code, email } = await req.json();

    if (!code || !email) {
      return NextResponse.json(
        { error: "Thiếu mã hoặc email" },
        { status: 400 }
      );
    }

    if (!/^\d{6}$/.test(code)) {
      return NextResponse.json(
        { error: "Mã phải là 6 chữ số" },
        { status: 400 }
      );
    }

    // Find user by email
    const { data: users } = await getSupabase()
      .from("users")
      .select("id, email_verified")
      .eq("email", email)
      .limit(1);

    if (!users || users.length === 0) {
      return NextResponse.json(
        { error: "Không tìm thấy tài khoản" },
        { status: 404 }
      );
    }

    const user = users[0];

    if (user.email_verified) {
      return NextResponse.json(
        { error: "Email đã được xác thực" },
        { status: 400 }
      );
    }

    // Validate OTP
    const ip = getClientIp(req);
    const userAgent = req.headers.get("user-agent") || "";

    const result = await validateOtpForUser(user.id, code, ip, userAgent);

    if (!result.success) {
      const status = result.lockUntil ? 429 : 401;
      return NextResponse.json(
        { error: result.error, lockUntil: result.lockUntil?.toISOString() },
        { status }
      );
    }

    // Mark email as verified
    await getSupabase()
      .from("users")
      .update({ email_verified: new Date().toISOString() })
      .eq("id", user.id);

    // Auto-login using Auth.js signIn
    const signInResult = await signIn("credentials", {
      email,
      password: "__otp_verified__",
      redirect: false,
    });

    if (signInResult?.error) {
      console.error("Auto-login failed:", signInResult.error);
      return NextResponse.json(
        { error: "Đăng ký thành công. Vui lòng đăng nhập." },
        { status: 200 }
      );
    }

    return NextResponse.json(
      { success: true, redirect: "/dashboard" },
      { status: 200 }
    );
  } catch (err) {
    console.error("OTP verification error:", err);
    return NextResponse.json(
      { error: "Lỗi server" },
      { status: 500 }
    );
  }
}
