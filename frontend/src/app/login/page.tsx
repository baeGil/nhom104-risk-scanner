"use client";

import { useState } from "react";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyInput } from "@/components/ui/wobbly-input";
import { WobblyCard } from "@/components/ui/wobbly-card";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: typeof errors = {};
    if (!email) newErrors.email = "Vui lòng nhập email";
    if (!password) newErrors.password = "Vui lòng nhập mật khẩu";
    setErrors(newErrors);
    if (Object.keys(newErrors).length === 0) {
      router.push("/dashboard");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Về trang chủ
      </Link>
      <WobblyCard decoration="tape" className="w-full max-w-md">
        <h1 className="font-heading text-3xl text-fg text-center mb-2">Đăng nhập</h1>
        <p className="font-body text-fg/60 text-center mb-8">Chào mừng trở lại!</p>
        <form onSubmit={handleSubmit} className="space-y-6">
          <WobblyInput
            label="Email"
            type="email"
            placeholder="email@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
          />
          <WobblyInput
            label="Mật khẩu"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
          />
          <WobblyButton type="submit" className="w-full">
            Đăng nhập
          </WobblyButton>
        </form>
        <p className="font-body text-center mt-6 text-fg/60">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="text-secondary hover:underline">
            Đăng ký
          </Link>
        </p>
      </WobblyCard>
    </div>
  );
}
