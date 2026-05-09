"use client";

import { useState } from "react";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyInput } from "@/components/ui/wobbly-input";
import { WobblyCard } from "@/components/ui/wobbly-card";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!name) newErrors.name = "Vui lòng nhập tên";
    if (!email) newErrors.email = "Vui lòng nhập email";
    if (!password) newErrors.password = "Vui lòng nhập mật khẩu";
    if (password !== confirmPassword) newErrors.confirmPassword = "Mật khẩu không khớp";
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
      <WobblyCard decoration="tack" className="w-full max-w-md">
        <h1 className="font-heading text-3xl text-fg text-center mb-2">Đăng ký</h1>
        <p className="font-body text-fg/60 text-center mb-8">Tạo tài khoản mới</p>
        <form onSubmit={handleSubmit} className="space-y-5">
          <WobblyInput
            label="Tên"
            type="text"
            placeholder="Nguyễn Văn A"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={errors.name}
          />
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
          <WobblyInput
            label="Xác nhận mật khẩu"
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
          />
          <WobblyButton type="submit" className="w-full">
            Đăng ký
          </WobblyButton>
        </form>
        <p className="font-body text-center mt-6 text-fg/60">
          Đã có tài khoản?{" "}
          <Link href="/login" className="text-secondary hover:underline">
            Đăng nhập
          </Link>
        </p>
      </WobblyCard>
    </div>
  );
}
