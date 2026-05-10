"use client";

import { useState } from "react";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyInput } from "@/components/ui/wobbly-input";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyDivider } from "@/components/ui/wobbly-divider";
import { User, Key, Bell, Copy, Plus } from "lucide-react";

export default function SettingsPage() {
  const [name, setName] = useState("Nguyễn Văn A");
  const [email, setEmail] = useState("vana@example.com");
  const [apiKey, setApiKey] = useState("sk-phaply-••••••••••••••••••••");
  const [notifications, setNotifications] = useState(true);

  const handleCopyKey = () => {
    navigator.clipboard.writeText("sk-phaply-xxx");
  };

  const handleGenerateKey = () => {
    setApiKey("sk-phaply-" + Math.random().toString(36).substring(2, 15));
  };

  return (
    <div className="space-y-8">
      <h1 className="font-heading text-4xl text-fg">Cài đặt</h1>

      {/* Profile */}
      <WobblyCard decoration="tack">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-fg text-white rounded-full flex items-center justify-center" style={{ borderRadius: "45% 55% 50% 50% / 55% 45% 55% 45%" }}>
            <User className="w-6 h-6" />
          </div>
          <h2 className="font-heading text-2xl text-fg">Hồ sơ</h2>
        </div>
        <div className="space-y-4">
          <WobblyInput label="Tên" value={name} onChange={(e) => setName(e.target.value)} />
          <WobblyInput label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <WobblyButton>Lưu thay đổi</WobblyButton>
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
    </div>
  );
}
