"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyButton } from "@/components/ui/wobbly-button";
import Link from "next/link";
import { ArrowLeft, Loader2, CheckCircle, Mail } from "lucide-react";
import { signIn } from "next-auth/react";
import { broadcastLogin } from "@/lib/auth-sync";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) return;

    const verify = async () => {
      const res = await fetch("/api/auth/verify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });

      const data = await res.json();

      if (res.ok) {
        // Auto-login using credentials
        const result = await signIn("credentials", {
          email: data.email,
          password: "__otp_verified__",
          redirect: false,
        });

        if (result?.error) {
          setStatus("success");
        } else {
          broadcastLogin();
          router.push("/dashboard");
        }
      } else {
        setStatus("error");
        setMessage(data.error || "Có lỗi xảy ra");
      }
    };

    verify();
  }, [token, router]);

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Về trang chủ
        </Link>
        <WobblyCard decoration="tape" className="w-full max-w-md text-center">
          <Mail className="w-16 h-16 text-secondary mx-auto mb-4" />
          <h1 className="font-heading text-3xl text-fg mb-2">Xác thực email</h1>
          <p className="font-body text-fg/60 mb-6">
            Vui lòng kiểm tra email và nhấn vào link xác thực chúng tôi đã gửi.
          </p>
          <WobblyButton className="w-full" onClick={() => router.back()}>Quay lại</WobblyButton>
        </WobblyCard>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <WobblyCard decoration="tape" className="w-full max-w-md text-center">
          <Loader2 className="w-16 h-16 text-secondary mx-auto mb-4 animate-spin" />
          <h1 className="font-heading text-3xl text-fg mb-2">Đang xác thực...</h1>
          <p className="font-body text-fg/60">Vui lòng đợi trong giây lát.</p>
        </WobblyCard>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <WobblyCard decoration="tape" className="w-full max-w-md text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="font-heading text-3xl text-fg mb-2">Xác thực thành công</h1>
          <p className="font-body text-fg/60 mb-6">
            Email của bạn đã được xác thực. Bạn có thể đăng nhập ngay.
          </p>
          <Link href="/login">
            <WobblyButton className="w-full">Đăng nhập</WobblyButton>
          </Link>
        </WobblyCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <WobblyCard decoration="tape" className="w-full max-w-md text-center">
        <h1 className="font-heading text-3xl text-fg mb-2">Xác thực thất bại</h1>
        <p className="font-body text-fg/60 mb-6">{message}</p>
        <WobblyButton className="w-full" onClick={() => router.back()}>Quay lại</WobblyButton>
      </WobblyCard>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
