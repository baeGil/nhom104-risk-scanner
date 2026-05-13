import { NextRequest, NextResponse } from "next/server";
import { hash } from "bcryptjs";
import { createClient } from "@supabase/supabase-js";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

export async function POST(req: NextRequest) {
  try {
    const { token, password } = await req.json();

    if (!token || !password) {
      return NextResponse.json(
        { error: "Token và mật khẩu là bắt buộc" },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: "Mật khẩu phải có ít nhất 8 ký tự" },
        { status: 400 }
      );
    }

    const { data: resetTokens } = await getSupabase()
      .from("password_reset_tokens")
      .select("*")
      .eq("token", token)
      .gt("expires", new Date().toISOString())
      .limit(1);

    if (!resetTokens || resetTokens.length === 0) {
      return NextResponse.json(
        { error: "Link đặt lại mật khẩu đã hết hạn hoặc không hợp lệ" },
        { status: 400 }
      );
    }

    const resetToken = resetTokens[0];
    const password_hash = await hash(password, 12);

    await getSupabase()
      .from("users")
      .update({ password_hash })
      .eq("id", resetToken.user_id);

    await getSupabase()
      .from("password_reset_tokens")
      .delete()
      .eq("id", resetToken.id);

    await getSupabase()
      .from("sessions")
      .delete()
      .eq("user_id", resetToken.user_id);

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Password reset confirm error:", err);
    return NextResponse.json(
      { error: "Lỗi server" },
      { status: 500 }
    );
  }
}
