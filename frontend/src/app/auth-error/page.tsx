"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyButton } from "@/components/ui/wobbly-button";
import Link from "next/link";
import { ArrowLeft, AlertCircle } from "lucide-react";

const errorMessages: Record<string, string> = {
  Configuration: "Cấu hình xác thực có lỗi. Vui lòng liên hệ quản trị viên.",
  AccessDenied: "Bạn không có quyền truy cập.",
  Verification: "Link xác thực đã hết hạn hoặc không hợp lệ.",
  OAuthSignin: "Lỗi khi bắt đầu đăng nhập OAuth.",
  OAuthCallback: "Lỗi khi xử lý callback OAuth.",
  OAuthCreateAccount: "Không thể tạo tài khoản từ OAuth.",
  EmailCreateAccount: "Không thể tạo tài khoản từ email.",
  Callback: "Lỗi khi xử lý callback.",
  OAuthAccountNotLinked: "Email này đã được sử dụng với provider khác.",
  Default: "Đã xảy ra lỗi trong quá trình xác thực.",
};

function AuthErrorContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error") || "Default";
  const message = errorMessages[error] || errorMessages.Default;

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <Link href="/" className="absolute top-6 left-6 flex items-center gap-2 font-body text-lg text-fg hover:text-secondary transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Về trang chủ
      </Link>
      <WobblyCard decoration="tape" className="w-full max-w-md text-center">
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h1 className="font-heading text-3xl text-fg mb-2">Lỗi xác thực</h1>
        <p className="font-body text-fg/60 mb-6">{message}</p>
        <Link href="/login">
          <WobblyButton className="w-full">Quay lại đăng nhập</WobblyButton>
        </Link>
      </WobblyCard>
    </div>
  );
}

export default function AuthErrorPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AuthErrorContent />
    </Suspense>
  );
}
