import { createClient } from "@supabase/supabase-js";
import crypto from "crypto";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

function getSalt(): string {
  return process.env.AUTH_SECRET || "default-salt-change-in-production";
}

export function generateOtp(): string {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

export function hashOtp(code: string): string {
  return crypto.createHash("sha256").update(code + getSalt()).digest("hex");
}

export function verifyOtp(input: string, storedHash: string): boolean {
  return hashOtp(input) === storedHash;
}

export async function createOtpForUser(userId: string): Promise<{ code: string; expires: Date }> {
  // Invalidate ALL existing OTPs for this user first
  await getSupabase()
    .from("email_otp_codes")
    .update({ is_used: true })
    .eq("user_id", userId)
    .eq("is_used", false);

  const code = generateOtp();
  const codeHash = hashOtp(code);
  const expires = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes

  const { data, error } = await getSupabase()
    .from("email_otp_codes")
    .insert({
      user_id: userId,
      code_hash: codeHash,
      expires: expires.toISOString(),
    })
    .select()
    .single();

  if (error) {
    console.error("Create OTP error:", error);
    throw error;
  }

  return { code, expires };
}

export async function validateOtpForUser(
  userId: string,
  code: string,
  ip?: string,
  userAgent?: string
): Promise<
  | { success: true; userId: string }
  | { success: false; error: string; lockUntil?: Date; failedCount?: number }
> {
  const now = new Date();

  // Get the MOST RECENT OTP for user (regardless of is_used)
  const { data: otps } = await getSupabase()
    .from("email_otp_codes")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1);

  if (!otps || otps.length === 0) {
    return { success: false, error: "Không tìm thấy mã xác thực" };
  }

  const otp = otps[0];

  // If the most recent OTP is already used, reject
  if (otp.is_used) {
    return { success: false, error: "Mã đã được sử dụng" };
  }

  // Check if locked
  if (otp.locked_until && new Date(otp.locked_until) > now) {
    return {
      success: false,
      error: "Đã khóa 15 phút",
      lockUntil: new Date(otp.locked_until),
    };
  }

  // Check if expired
  if (new Date(otp.expires) < now) {
    return { success: false, error: "Mã đã hết hạn" };
  }

  // Verify code
  const isValid = verifyOtp(code, otp.code_hash);

  // Update attempt metadata
  const updateData: Record<string, unknown> = {
    last_attempt_at: now.toISOString(),
    last_ip: ip || null,
    last_user_agent: userAgent || null,
  };

  if (!isValid) {
    const newFailedCount = otp.failed_count + 1;
    updateData.failed_count = newFailedCount;

    if (newFailedCount >= 5) {
      updateData.locked_until = new Date(now.getTime() + 15 * 60 * 1000).toISOString();
    }

    await getSupabase()
      .from("email_otp_codes")
      .update(updateData)
      .eq("id", otp.id);

    return {
      success: false,
      error: newFailedCount >= 5 ? "Đã khóa 15 phút" : "Mã không đúng",
      lockUntil: newFailedCount >= 5 ? new Date(now.getTime() + 15 * 60 * 1000) : undefined,
      failedCount: newFailedCount,
    };
  }

  // Invalidate ALL other OTPs for this user
  await getSupabase()
    .from("email_otp_codes")
    .update({ is_used: true })
    .eq("user_id", userId)
    .neq("id", otp.id);

  // Mark current OTP as used
  await getSupabase()
    .from("email_otp_codes")
    .update({ is_used: true, ...updateData })
    .eq("id", otp.id);

  return { success: true, userId: otp.user_id };
}

export async function invalidateUserOtps(userId: string): Promise<void> {
  await getSupabase()
    .from("email_otp_codes")
    .update({ is_used: true })
    .eq("user_id", userId)
    .eq("is_used", false);
}

export async function cleanupExpiredOtps(): Promise<void> {
  const twentyFourHoursAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

  await getSupabase()
    .from("email_otp_codes")
    .delete()
    .or(`is_used.eq.true,expires.lt.${twentyFourHoursAgo.toISOString()}`);
}
