"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useLogoutConfirm } from "@/lib/logout-context";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyInput } from "@/components/ui/wobbly-input";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyBadge } from "@/components/ui/wobbly-badge";
import { User, Key, Bell, Copy, Plus, LogOut, Shield } from "lucide-react";
import { getLimits, isPremium, isAdmin } from "@/lib/role-checks";

export default function SettingsPage() {
  const { user } = useAuth();
  const { showLogoutConfirm } = useLogoutConfirm();
  const [name, setName] = useState(user.name || "");
  const [apiKey, setApiKey] = useState("sk-phaply-••••••••••••••••••••");
  const [notifications, setNotifications] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  const role = (user as any).role || "free";
  const limits = getLimits(role);

  const handleCopyKey = () => {
    navigator.clipboard.writeText("sk-phaply-xxx");
  };

  const handleGenerateKey = () => {
    setApiKey("sk-phaply-" + Math.random().toString(36).substring(2, 15));
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    setSaveMessage("");
    const res = await fetch("/api/auth/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    setSaving(false);
    if (res.ok) {
      setSaveMessage("Đã lưu thay đổi");
    } else {
      const data = await res.json();
      setSaveMessage(data.error || "Có lỗi xảy ra");
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="font-heading text-4xl text-fg">Cài đặt</h1>

      {/* Profile */}
      <WobblyCard decoration="tack">
        <div className="flex items-center gap-3 mb-6">
          {user.image ? (
            <img src={user.image} alt={user.name || ""} className="w-12 h-12 rounded-full" />
          ) : (
            <div className="w-12 h-12 bg-fg text-white rounded-full flex items-center justify-center" style={{ borderRadius: "45% 55% 50% 50% / 55% 45% 55% 45%" }}>
              <User className="w-6 h-6" />
            </div>
          )}
          <div>
            <h2 className="font-heading text-2xl text-fg">Hồ sơ</h2>
            <p className="font-body text-sm text-fg/60">{user.email}</p>
          </div>
          <div className="ml-auto">
            <WobblyBadge variant={isAdmin(role) ? "accent" : isPremium(role) ? "default" : "secondary"}>
              {role === "free" ? "Miễn phí" : role === "premium" ? "Chuyên nghiệp" : "Admin"}
            </WobblyBadge>
          </div>
        </div>
        <div className="space-y-4">
          <WobblyInput label="Tên" value={name} onChange={(e) => setName(e.target.value)} />
          <WobblyButton onClick={handleSaveProfile} disabled={saving}>
            {saving ? "Đang lưu..." : "Lưu thay đổi"}
          </WobblyButton>
          {saveMessage && (
            <p className="font-body text-sm text-green-600">{saveMessage}</p>
          )}
        </div>
      </WobblyCard>

      {/* Usage */}
      <WobblyCard decoration="tape">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="w-6 h-6 text-secondary" strokeWidth={2.5} />
          <h2 className="font-heading text-2xl text-fg">Sử dụng</h2>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-muted rounded-lg">
            <p className="font-body text-sm text-fg/60">Hợp đồng/tháng</p>
            <p className="font-heading text-xl text-fg">
              {limits.contractsPerMonth === Infinity ? "Không giới hạn" : `0/${limits.contractsPerMonth}`}
            </p>
          </div>
          <div className="p-4 bg-muted rounded-lg">
            <p className="font-body text-sm text-fg/60">Câu hỏi/ngày</p>
            <p className="font-heading text-xl text-fg">
              {limits.qaPerDay === Infinity ? "Không giới hạn" : `0/${limits.qaPerDay}`}
            </p>
          </div>
        </div>
      </WobblyCard>

      {/* API Keys */}
      <WobblyCard decoration="tape">
        <div className="flex items-center gap-3 mb-6">
          <Key className="w-6 h-6 text-secondary" strokeWidth={2.5} />
          <h2 className="font-heading text-2xl text-fg">API Key</h2>
        </div>
        <div className="flex items-center gap-3 mb-4">
          <code className="flex-1 font-body text-lg bg-muted px-4 py-3" style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}>
            {apiKey}
          </code>
          <WobblyButton variant="secondary" size="sm" onClick={handleCopyKey}>
            <Copy className="w-4 h-4" />
          </WobblyButton>
        </div>
        <WobblyButton variant="secondary" onClick={handleGenerateKey}>
          <Plus className="w-4 h-4 mr-2" />
          Tạo key mới
        </WobblyButton>
      </WobblyCard>

      {/* Preferences */}
      <WobblyCard>
        <div className="flex items-center gap-3 mb-6">
          <Bell className="w-6 h-6 text-accent" strokeWidth={2.5} />
          <h2 className="font-heading text-2xl text-fg">Tùy chọn</h2>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-body text-lg text-fg">Thông báo email</span>
            <button
              className={`w-14 h-8 border-2 border-fg transition-colors ${
                notifications ? "bg-secondary" : "bg-muted"
              }`}
              style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
              onClick={() => setNotifications(!notifications)}
            >
              <div
                className={`w-6 h-6 bg-white border border-fg transition-transform ${
                  notifications ? "translate-x-7" : "translate-x-0.5"
                }`}
                style={{ borderRadius: "50%" }}
              />
            </button>
          </div>
        </div>
      </WobblyCard>

      {/* Logout */}
      <WobblyCard>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LogOut className="w-6 h-6 text-red-500" strokeWidth={2.5} />
            <h2 className="font-heading text-2xl text-fg">Đăng xuất</h2>
          </div>
          <WobblyButton variant="secondary" onClick={showLogoutConfirm}>
            Đăng xuất
          </WobblyButton>
        </div>
      </WobblyCard>
    </div>
  );
}
