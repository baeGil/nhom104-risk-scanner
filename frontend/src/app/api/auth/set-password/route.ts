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
    const { userId, password } = await req.json();

    if (!userId || !password) {
      return NextResponse.json(
        { error: "Thiếu thông tin" },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: "Mật khẩu phải có ít nhất 8 ký tự" },
        { status: 400 }
      );
    }

    // Find user
    const { data: users } = await getSupabase()
      .from("users")
      .select("id, email, password_hash, linked_providers")
      .eq("id", userId)
      .limit(1);

    if (!users || users.length === 0) {
      return NextResponse.json(
        { error: "Không tìm thấy tài khoản" },
        { status: 404 }
      );
    }

    const user = users[0];

    // Check if user has OAuth provider
    const providers: string[] = user.linked_providers || [];
    const hasOAuth = providers.includes("google") || providers.includes("github");

    if (!hasOAuth && user.password_hash) {
      return NextResponse.json(
        { error: "Tài khoản này đã có mật khẩu" },
        { status: 400 }
      );
    }

    // Set password
    const password_hash = await hash(password, 12);

    // Add credentials to linked_providers if not already there
    if (!providers.includes("credentials")) {
      providers.push("credentials");
    }

    await getSupabase()
      .from("users")
      .update({ password_hash, linked_providers: providers })
      .eq("id", userId);

    return NextResponse.json(
      { success: true, message: "Đã đặt mật khẩu thành công" },
      { status: 200 }
    );
  } catch (err) {
    console.error("Set password error:", err);
    return NextResponse.json(
      { error: "Lỗi server" },
      { status: 500 }
    );
  }
}
