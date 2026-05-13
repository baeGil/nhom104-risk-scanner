import { NextRequest, NextResponse } from "next/server";
import { hash } from "bcryptjs";
import { createClient } from "@supabase/supabase-js";
import { Resend } from "resend";
import crypto from "crypto";
import { rateLimitService } from "@/lib/rate-limit";
import { createOtpForUser, invalidateUserOtps } from "@/lib/otp";
import { generateVerificationEmail } from "@/lib/email-templates/verification";

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
    const ip = getClientIp(req);
    const { email, password, name } = await req.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email và mật khẩu là bắt buộc" },
        { status: 400 }
      );
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json(
        { error: "Email không hợp lệ" },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: "Mật khẩu phải có ít nhất 8 ký tự" },
        { status: 400 }
      );
    }

    // Check IP rate limit for registration (3/hour)
    const regLimit = await rateLimitService.check(ip, "registration", 3);
    if (!regLimit.allowed) {
      return NextResponse.json(
        { error: "Quá nhiều tài khoản tạo từ IP này. Vui lòng thử lại sau" },
        { status: 429 }
      );
    }

    // Check if user already exists
    const { data: existing } = await getSupabase()
      .from("users")
      .select("id, email_verified, name, password_hash, linked_providers")
      .eq("email", email)
      .limit(1);

    if (existing && existing.length > 0) {
      const user = existing[0];
      const providers: string[] = user.linked_providers || [];
      const hasOAuth = providers.includes("google") || providers.includes("github");

      // User exists with OAuth provider
      if (hasOAuth) {
        return NextResponse.json(
          {
            error: "Email này đã được dùng để đăng nhập bằng " +
              (providers.includes("google") ? "Google" : "GitHub") +
              ". Bạn có muốn đặt mật khẩu cho tài khoản này không?",
            existingAccount: true,
            providers,
            userId: user.id,
          },
          { status: 409 }
        );
      }

      // User exists with credentials
      if (user.password_hash) {
        return NextResponse.json(
          { error: "Email đã được sử dụng" },
          { status: 409 }
        );
      }

      // User exists but not verified - invalidate old OTPs and create new ones
      const userId = existing[0].id;
      const userName = existing[0].name || email.split("@")[0];

      await invalidateUserOtps(userId);

      // Check OTP rate limit (10/hour)
      const otpLimit = await rateLimitService.check(ip, "otp_request", 10);
      if (!otpLimit.allowed) {
        return NextResponse.json(
          { error: "Quá nhiều yêu cầu. Vui lòng thử lại sau" },
          { status: 429 }
        );
      }

      const { code, expires } = await createOtpForUser(userId);

      // Invalidate old verification tokens
      await getSupabase()
        .from("email_verification_tokens")
        .delete()
        .eq("user_id", userId);

      const verifyToken = crypto.randomUUID();
      const verifyExpires = new Date(Date.now() + 24 * 60 * 60 * 1000);

      await getSupabase()
        .from("email_verification_tokens")
        .insert({
          user_id: userId,
          token: verifyToken,
          expires: verifyExpires.toISOString(),
        });

      const verifyUrl = `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/verify-email?token=${verifyToken}`;

      const { subject, html } = generateVerificationEmail({
        otpCode: code,
        userName,
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
        { success: true, email },
        { status: 200 }
      );
    }

    // Record registration in rate limit
    await rateLimitService.record(ip, "registration");

    const password_hash = await hash(password, 12);
    const id = crypto.randomUUID();
    const userName = name || email.split("@")[0];

    // Create user (not verified yet)
    const { data: user, error } = await getSupabase()
      .from("users")
      .insert({
        id,
        email,
        name: userName,
        password_hash,
        email_verified: null,
        linked_providers: ["credentials"],
      })
      .select()
      .single();

    if (error) {
      console.error("User creation error:", error);
      return NextResponse.json(
        { error: "Không thể tạo tài khoản" },
        { status: 500 }
      );
    }

    // Create role
    await getSupabase()
      .from("user_roles")
      .insert({ user_id: id, role: "free" });

    // Check OTP rate limit
    const otpLimit = await rateLimitService.check(ip, "otp_request", 10);
    if (!otpLimit.allowed) {
      return NextResponse.json(
        { error: "Quá nhiều yêu cầu. Vui lòng thử lại sau" },
        { status: 429 }
      );
    }

    // Create OTP and send email
    const { code, expires } = await createOtpForUser(id);

    // Create verification token (invalidate any existing ones first)
    await getSupabase()
      .from("email_verification_tokens")
      .delete()
      .eq("user_id", id);

    const verifyToken = crypto.randomUUID();
    const verifyExpires = new Date(Date.now() + 24 * 60 * 60 * 1000);

    await getSupabase()
      .from("email_verification_tokens")
      .insert({
        user_id: id,
        token: verifyToken,
        expires: verifyExpires.toISOString(),
      });

    const verifyUrl = `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/verify-email?token=${verifyToken}`;

    const { subject, html } = generateVerificationEmail({
      otpCode: code,
      userName,
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
      { success: true, email },
      { status: 201 }
    );
  } catch (err) {
    console.error("Registration error:", err);
    return NextResponse.json(
      { error: "Lỗi server" },
      { status: 500 }
    );
  }
}
