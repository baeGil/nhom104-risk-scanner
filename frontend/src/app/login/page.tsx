"use client";

import { useState, Suspense } from "react";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyCard } from "@/components/ui/wobbly-card";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Loader2, Eye, EyeOff } from "lucide-react";
import { signIn } from "next-auth/react";

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

function LoginContent() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string; form?: string }>({});
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: typeof errors = {};
    if (!email) newErrors.email = "Vui lòng nhập email";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) newErrors.email = "Email không hợp lệ";
    if (!password) newErrors.password = "Vui lòng nhập mật khẩu";
    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      setLoading(true);
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        const checkRes = await fetch("/api/auth/check-verification", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const checkData = await checkRes.json();

        if (checkData.needsVerification) {
          setErrors({ form: "Vui lòng xác thực email trước khi đăng nhập" });
        } else {
          setErrors({ form: "Email hoặc mật khẩu không đúng" });
        }
        setLoading(false);
      } else {
        router.push(callbackUrl);
      }
    }
  };

  const handleOAuth = (provider: "google" | "github") => {
    signIn(provider, { callbackUrl });
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Về trang chủ
      </Link>
      <WobblyCard decoration="tape" className="w-full max-w-md">
        <h1 className="font-heading text-3xl text-fg text-center mb-2">Đăng nhập</h1>
        <p className="font-body text-fg/60 text-center mb-6">Chào mừng trở lại!</p>

        {errors.form && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm font-body">
            {errors.form}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="font-body text-sm text-fg/70">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@example.com"
              className={`w-full border-2 bg-white p-3 font-body text-lg focus:outline-none transition-colors ${
                errors.email ? "border-red-400" : "border-fg focus:border-secondary"
              }`}
              style={{ borderRadius: "120px 8px 90px 8px / 8px 90px 8px 120px" }}
            />
            {errors.email && <p className="font-body text-sm text-red-500">{errors.email}</p>}
          </div>

          <PasswordInput
            label="Mật khẩu"
            value={password}
            onChange={setPassword}
            error={errors.password}
          />

          <div className="flex justify-end">
            <Link href="/forgot-password" className="font-body text-sm text-secondary hover:underline">
              Quên mật khẩu?
            </Link>
          </div>
          <WobblyButton type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Đăng nhập"}
          </WobblyButton>
        </form>

        <p className="font-body text-center mt-6 text-fg/60">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="text-secondary hover:underline">
            Đăng ký
          </Link>
        </p>

        <div className="flex items-center gap-4 my-6">
          <div className="flex-1 h-px bg-fg/20" />
          <span className="font-body text-sm text-fg/40">hoặc tiếp tục với</span>
          <div className="flex-1 h-px bg-fg/20" />
        </div>

        <div className="flex justify-center gap-4">
          <button
            onClick={() => handleOAuth("google")}
            className="w-12 h-12 flex items-center justify-center border-2 border-fg/20 hover:border-fg hover:bg-muted transition-all"
            style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </button>
          <button
            onClick={() => handleOAuth("github")}
            className="w-12 h-12 flex items-center justify-center border-2 border-fg/20 hover:border-fg hover:bg-muted transition-all"
            style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 2.614-.131.759-.211 1.564-.319 2.371-.323.807.004 1.612.112 2.371.323 1.606-.191 2.605.131 2.605.131.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </button>
        </div>
      </WobblyCard>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginContent />
    </Suspense>
  );
}
