"use client";

import { useState, useRef, useEffect, Suspense, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyButton } from "@/components/ui/wobbly-button";
import Link from "next/link";
import { ArrowLeft, Loader2, CheckCircle, Mail } from "lucide-react";
import { broadcastLogin } from "@/lib/auth-sync";

function VerifyOtpContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const email = searchParams.get("email") || "";
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resendLoading, setResendLoading] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setTimeout(() => setResendCooldown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [resendCooldown]);

  const verifyOtp = useCallback(async (otpCode: string) => {
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: otpCode, email }),
      });

      const data = await res.json();

      if (!res.ok || data.error) {
        setError(data.error || "Mã không đúng");
        setLoading(false);
        return;
      }

      broadcastLogin();
      setSuccess(true);
      setTimeout(() => {
        router.push(data.redirect || "/dashboard");
      }, 1500);
    } catch {
      setError("Có lỗi xảy ra");
      setLoading(false);
    }
  }, [router]);

  // Auto-submit when all 6 digits are filled
  useEffect(() => {
    const otpCode = code.join("");
    if (otpCode.length === 6 && !loading && !error) {
      const timer = setTimeout(() => {
        verifyOtp(otpCode);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [code, loading, error, email, router, verifyOtp]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value.slice(-1);
    setCode(newCode);
    setError("");

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted) {
      const newCode = [...code];
      for (let i = 0; i < pasted.length; i++) {
        newCode[i] = pasted[i];
      }
      setCode(newCode);
      inputRefs.current[Math.min(pasted.length, 5)]?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const otpCode = code.join("");

    if (otpCode.length !== 6) {
      setError("Vui lòng nhập đủ 6 chữ số");
      return;
    }

    verifyOtp(otpCode);
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;

    setResendLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/resend-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Không thể gửi lại mã");
        setResendLoading(false);
        return;
      }

      setResendCooldown(60);
      setResendLoading(false);
    } catch {
      setError("Có lỗi xảy ra");
      setResendLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <WobblyCard decoration="tape" className="w-full max-w-md text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="font-heading text-3xl text-fg mb-2">Xác thực thành công</h1>
          <p className="font-body text-fg/60 mb-6">
            Đang chuyển đến dashboard...
          </p>
          <Loader2 className="w-6 h-6 text-secondary mx-auto animate-spin" />
        </WobblyCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Về trang chủ
      </Link>
      <WobblyCard decoration="tape" className="w-full max-w-md">
        <Mail className="w-12 h-12 text-secondary mx-auto mb-4" />
        <h1 className="font-heading text-3xl text-fg text-center mb-2">Xác thực email</h1>
        <p className="font-body text-fg/60 text-center mb-6">
          Chúng tôi đã gửi mã 6 số tới <strong>{email}</strong>
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm font-body text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex justify-center gap-2" onPaste={handlePaste}>
            {code.map((digit, index) => (
              <input
                key={index}
                ref={(el) => {
                  inputRefs.current[index] = el;
                }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                className="w-12 h-14 text-center text-2xl font-bold border-2 border-fg focus:border-secondary focus:outline-none bg-white"
                style={{ borderRadius: "12px 4px 10px 4px / 4px 10px 4px 12px" }}
              />
            ))}
          </div>

          <WobblyButton type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác thực"}
          </WobblyButton>
        </form>

        <div className="mt-6 text-center">
          <p className="font-body text-sm text-fg/60 mb-2">
            Chưa nhận được mã?
          </p>
          <button
            type="button"
            onClick={handleResend}
            disabled={resendCooldown > 0 || resendLoading}
            className="font-body text-sm text-secondary hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {resendLoading ? (
              <Loader2 className="w-4 h-4 animate-spin inline" />
            ) : resendCooldown > 0 ? (
              `Gửi lại mã (${resendCooldown}s)`
            ) : (
              "Gửi lại mã"
            )}
          </button>
        </div>

        <div className="mt-6 pt-4 border-t border-fg/10 text-center">
          <p className="font-body text-xs text-fg/40">
            Hoặc{" "}
            <Link href="/verify-email" className="text-secondary hover:underline">
              xác thực bằng link trong email
            </Link>
          </p>
        </div>
      </WobblyCard>
    </div>
  );
}

export default function VerifyOtpPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VerifyOtpContent />
    </Suspense>
  );
}
