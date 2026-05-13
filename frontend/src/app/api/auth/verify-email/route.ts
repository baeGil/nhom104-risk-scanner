import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

export async function POST(req: NextRequest) {
  try {
    const { token } = await req.json();

    if (!token) {
      return NextResponse.json(
        { error: "Token không hợp lệ" },
        { status: 400 }
      );
    }

    // Find valid token
    const { data: tokens } = await getSupabase()
      .from("email_verification_tokens")
      .select("*")
      .eq("token", token)
      .gt("expires", new Date().toISOString())
      .limit(1);

    if (!tokens || tokens.length === 0) {
      return NextResponse.json(
        { error: "Link xác thực đã hết hạn hoặc không hợp lệ" },
        { status: 400 }
      );
    }

    const verificationToken = tokens[0];

    // Get user info
    const { data: users } = await getSupabase()
      .from("users")
      .select("id, email, name, email_verified")
      .eq("id", verificationToken.user_id)
      .limit(1);

    if (!users || users.length === 0) {
      return NextResponse.json(
        { error: "Không tìm thấy tài khoản" },
        { status: 404 }
      );
    }

    const user = users[0];

    // Mark email as verified
    await getSupabase()
      .from("users")
      .update({ email_verified: new Date().toISOString() })
      .eq("id", user.id);

    // Delete used token
    await getSupabase()
      .from("email_verification_tokens")
      .delete()
      .eq("id", verificationToken.id);

    // Invalidate OTPs
    await getSupabase()
      .from("email_otp_codes")
      .update({ is_used: true })
      .eq("user_id", user.id);

    // Delete ALL other verification tokens for this user
    await getSupabase()
      .from("email_verification_tokens")
      .delete()
      .eq("user_id", user.id)
      .neq("id", verificationToken.id);

    return NextResponse.json(
      { success: true, email: user.email },
      { status: 200 }
    );
  } catch (err) {
    console.error("Email verification error:", err);
    return NextResponse.json(
      { error: "Lỗi server" },
      { status: 500 }
    );
  }
}
