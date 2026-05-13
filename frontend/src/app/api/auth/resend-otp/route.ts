import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { createOtpForUser } from "@/lib/otp";
import { rateLimitService } from "@/lib/rate-limit";
import { generateVerificationEmail } from "@/lib/email-templates/verification";
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

function getClientIp(req: NextRequest): string {
  return req.headers.get("x-forwarded-for")?.split(",")[0] || "127.0.0.1";
}

export async function POST(req: NextRequest) {
  try {
    const { email } = await req.json();

    if (!email) {
      return NextResponse.json(
        { error: "Thiếu email" },
        { status: 400 }
      );
    }

    const ip = getClientIp(req);

    // Check OTP rate limit
    const otpLimit = await rateLimitService.check(ip, "otp_request", 10);
    if (!otpLimit.allowed) {
      return NextResponse.json(
        { error: "Quá nhiều yêu cầu. Vui lòng thử lại sau" },
        { status: 429 }
      );
    }

    // Find user
    const { data: users } = await getSupabase()
      .from("users")
      .select("id, name, email_verified")
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

    // Check cooldown (60 seconds) — skip for first resend
    const { data: recentOtps } = await getSupabase()
      .from("email_otp_codes")
      .select("created_at, resend_count")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(1);

    if (recentOtps && recentOtps.length > 0) {
      // First resend: no cooldown
      if (recentOtps[0].resend_count > 0) {
        const lastSent = new Date(recentOtps[0].created_at);
        const cooldownEnd = new Date(lastSent.getTime() + 60 * 1000);

        if (new Date() < cooldownEnd) {
          const remainingSeconds = Math.ceil((cooldownEnd.getTime() - Date.now()) / 1000);
          return NextResponse.json(
            { error: `Vui lòng đợi ${remainingSeconds} giây trước khi gửi lại` },
            { status: 429 }
          );
        }
      }
    }

    // Create new OTP (automatically invalidates old ones)
    const { code, expires } = await createOtpForUser(user.id);

    // Invalidate old verification tokens and create new one
    await getSupabase()
      .from("email_verification_tokens")
      .delete()
      .eq("user_id", user.id);

    const verifyToken = crypto.randomUUID();
    const verifyExpires = new Date(Date.now() + 24 * 60 * 60 * 1000);

    await getSupabase()
      .from("email_verification_tokens")
      .insert({
        user_id: user.id,
        token: verifyToken,
        expires: verifyExpires.toISOString(),
      });

    const verifyUrl = `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/verify-email?token=${verifyToken}`;

    const { subject, html } = generateVerificationEmail({
      otpCode: code,
      userName: user.name || email.split("@")[0],
      verifyUrl,
      expiryMinutes: 10,
    });

    const emailResult = await getResend().emails.send({
      from: process.env.AUTH_FROM_EMAIL || "onboarding@resend.dev",
      to: email,
      subject,
      html,
    });

    if (emailResult.error) {
      console.error("Resend error:", emailResult.error);
      return NextResponse.json(
        { error: "Không thể gửi email xác thực" },
        { status: 500 }
      );
    }

    console.log("Email sent successfully:", emailResult.data?.id);

    await rateLimitService.record(ip, "otp_request");

    return NextResponse.json(
      { success: true, message: "Đã gửi mã mới" },
      { status: 200 }
    );
  } catch (err) {
    console.error("Resend OTP error:", err);
    return NextResponse.json(
      { error: "Lỗi server" },
      { status: 500 }
    );
  }
}
