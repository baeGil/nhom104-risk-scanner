"use client";

import { useState } from "react";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyCard } from "@/components/ui/wobbly-card";
import Link from "next/link";
import { ArrowLeft, Loader2, Mail } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const validateEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email) {
      setError("Vui lòng nhập email");
      return;
    }

    if (!validateEmail(email)) {
      setError("Email không hợp lệ");
      return;
    }

    setLoading(true);
    const res = await fetch("/api/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    const data = await res.json();
    setLoading(false);

    if (res.ok) {
      if (data.notFound) {
        setError("Email chưa được đăng ký tài khoản");
      } else {
        setSent(true);
      }
    } else {
      setError(data.error || "Có lỗi xảy ra. Vui lòng thử lại.");
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Về trang chủ
        </Link>
        <WobblyCard decoration="tape" className="w-full max-w-md text-center">
          <Mail className="w-16 h-16 text-secondary mx-auto mb-4" />
          <h1 className="font-heading text-3xl text-fg mb-2">Kiểm tra email</h1>
          <p className="font-body text-fg/60 mb-6">
            Chúng tôi đã gửi link đặt lại mật khẩu đến <strong>{email}</strong>.
            Vui lòng kiểm tra hộp thư (và spam).
          </p>
          <Link href="/login">
            <WobblyButton className="w-full">Quay lại đăng nhập</WobblyButton>
          </Link>
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
        <h1 className="font-heading text-3xl text-fg text-center mb-2">Quên mật khẩu</h1>
        <p className="font-body text-fg/60 text-center mb-8">Nhập email để nhận link đặt lại mật khẩu</p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm font-body">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="font-body text-sm text-fg/70">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@example.com"
              className={`w-full border-2 bg-white p-3 font-body text-lg focus:outline-none transition-colors ${
                error ? "border-red-400" : "border-fg focus:border-secondary"
              }`}
              style={{ borderRadius: "120px 8px 90px 8px / 8px 90px 8px 120px" }}
            />
          </div>
          <WobblyButton type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Gửi link đặt lại"}
          </WobblyButton>
        </form>
        <p className="font-body text-center mt-6 text-fg/60">
          Nhớ mật khẩu?{" "}
          <Link href="/login" className="text-secondary hover:underline">
            Đăng nhập
          </Link>
        </p>
      </WobblyCard>
    </div>
  );
}
