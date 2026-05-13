"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyCard } from "@/components/ui/wobbly-card";
import Link from "next/link";
import { ArrowLeft, Loader2, CheckCircle, Eye, EyeOff } from "lucide-react";

function PasswordInput({
  label,
  value,
  onChange,
  error,
  placeholder = "••••••••",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
  placeholder?: string;
}) {
  const [show, setShow] = useState(false);

  return (
    <div className="space-y-2">
      <label className="font-body text-sm text-fg/70">{label}</label>
      <div className="relative">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full border-2 bg-white p-3 pr-12 font-body text-lg focus:outline-none transition-colors ${
            error ? "border-red-400" : "border-fg focus:border-secondary"
          }`}
          style={{ borderRadius: "120px 8px 90px 8px / 8px 90px 8px 120px" }}
        />
        <button
          type="button"
          onClick={() => setShow(!show)}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-fg/50 hover:text-fg transition-colors"
        >
          {show ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
        </button>
      </div>
      {error && <p className="font-body text-sm text-red-500">{error}</p>}
    </div>
  );
}

function ResetPasswordContent() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const t = searchParams.get("token");
    if (t) setToken(t);
  }, [searchParams]);

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Về trang chủ
        </Link>
        <WobblyCard decoration="tape" className="w-full max-w-md text-center">
          <h1 className="font-heading text-3xl text-fg mb-2">Link không hợp lệ</h1>
          <p className="font-body text-fg/60 mb-6">
            Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.
          </p>
          <Link href="/forgot-password">
            <WobblyButton className="w-full">Yêu cầu link mới</WobblyButton>
          </Link>
        </WobblyCard>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <WobblyCard decoration="tape" className="w-full max-w-md text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="font-heading text-3xl text-fg mb-2">Đặt lại thành công</h1>
          <p className="font-body text-fg/60 mb-6">
            Mật khẩu của bạn đã được cập nhật. Vui lòng đăng nhập lại.
          </p>
          <Link href="/login">
            <WobblyButton className="w-full">Đăng nhập</WobblyButton>
          </Link>
        </WobblyCard>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!password) newErrors.password = "Vui lòng nhập mật khẩu";
    if (password.length < 8) newErrors.password = "Mật khẩu phải có ít nhất 8 ký tự";
    if (password !== confirmPassword) newErrors.confirmPassword = "Mật khẩu không khớp";
    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      setLoading(true);
      const res = await fetch("/api/auth/reset-password/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });

      setLoading(false);

      if (res.ok) {
        setSuccess(true);
      } else {
        const data = await res.json();
        setErrors({ form: data.error || "Có lỗi xảy ra" });
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Về trang chủ
      </Link>
      <WobblyCard decoration="tape" className="w-full max-w-md">
        <h1 className="font-heading text-3xl text-fg text-center mb-2">Đặt lại mật khẩu</h1>
        <p className="font-body text-fg/60 text-center mb-8">Nhập mật khẩu mới</p>

        {errors.form && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm font-body">
            {errors.form}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <PasswordInput
            label="Mật khẩu mới"
            value={password}
            onChange={setPassword}
            error={errors.password}
          />
          <PasswordInput
            label="Xác nhận mật khẩu"
            value={confirmPassword}
            onChange={setConfirmPassword}
            error={errors.confirmPassword}
          />
          <WobblyButton type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Đặt lại mật khẩu"}
          </WobblyButton>
        </form>
      </WobblyCard>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
