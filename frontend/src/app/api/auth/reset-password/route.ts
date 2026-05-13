import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import crypto from "crypto";
import { Resend } from "resend";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

function getResend() {
  return new Resend(process.env.AUTH_RESEND_KEY);
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(req: NextRequest) {
  try {
    const { email } = await req.json();

    if (!email) {
      return NextResponse.json(
        { error: "Email là bắt buộc" },
        { status: 400 }
      );
    }

    if (!EMAIL_REGEX.test(email)) {
      return NextResponse.json(
        { error: "Email không hợp lệ" },
        { status: 400 }
      );
    }

    const { data: users } = await getSupabase()
      .from("users")
      .select("id, email, password_hash, linked_providers")
      .eq("email", email)
      .limit(1);

    if (!users || users.length === 0) {
      return NextResponse.json({ success: true, notFound: true });
    }

    const user = users[0];
    const isFirstPassword = !user.password_hash;
    const token = crypto.randomBytes(32).toString("hex");
    const expires = new Date(Date.now() + 60 * 60 * 1000);

    await getSupabase().from("password_reset_tokens").insert({
      user_id: user.id,
      token,
      expires,
    });

    const resetUrl = `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/reset-password?token=${token}`;

    const subject = isFirstPassword
      ? "Đặt mật khẩu - PhápLý"
      : "Đặt lại mật khẩu - PhápLý";

    const emailResult = await getResend().emails.send({
      from: process.env.AUTH_FROM_EMAIL || "onboarding@resend.dev",
      to: email,
      subject,
      html: `
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
          <h2>${isFirstPassword ? "Đặt mật khẩu" : "Đặt lại mật khẩu"}</h2>
          <p>${isFirstPassword
            ? "Tài khoản của bạn chưa có mật khẩu. Nhấn vào link bên dưới để đặt mật khẩu:"
            : "Nhấn vào link bên dưới để đặt lại mật khẩu:"}</p>
          <a href="${resetUrl}" style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">
            ${isFirstPassword ? "Đặt mật khẩu" : "Đặt lại mật khẩu"}
          </a>
          <p>Link hết hạn sau 1 giờ.</p>
        </div>
      `,
    });

    if (emailResult.error) {
      console.error("Resend error:", emailResult.error);
      return NextResponse.json(
        { error: "Không thể gửi email" },
        { status: 500 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Password reset error:", err);
    return NextResponse.json({ error: "Lỗi server" }, { status: 500 });
  }
}
