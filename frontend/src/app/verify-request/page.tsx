"use client";

import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyButton } from "@/components/ui/wobbly-button";
import Link from "next/link";
import { ArrowLeft, Mail } from "lucide-react";

export default function VerifyRequestPage() {
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
          Chúng tôi đã gửi link xác thực đến email của bạn.
          Vui lòng kiểm tra hộp thư (và mục spam) và nhấn vào link để xác thực.
        </p>
        <Link href="/login">
          <WobblyButton className="w-full">Quay lại đăng nhập</WobblyButton>
        </Link>
      </WobblyCard>
    </div>
  );
}
