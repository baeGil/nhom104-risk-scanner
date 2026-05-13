"use client";

import { motion, AnimatePresence } from "framer-motion";
import { WobblyCard } from "./wobbly-card";
import { WobblyButton } from "./wobbly-button";
import { WobblyBadge } from "./wobbly-badge";
import { X, Zap, Check } from "lucide-react";
import Link from "next/link";

interface UpgradePromptProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message?: string;
}

const premiumFeatures = [
  "Không giới hạn hợp đồng",
  "Không giới hạn câu hỏi",
  "Trích dẫn đã xác minh",
  "Ưu tiên xử lý",
  "Hỗ trợ email",
];

export function UpgradePrompt({
  isOpen,
  onClose,
  title = "Nâng cấp để mở khóa",
  message = "Tính năng này chỉ dành cho tài khoản Chuyên nghiệp.",
}: UpgradePromptProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", duration: 0.5 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md"
          >
            <WobblyCard decoration="tape" className="relative">
              <button
                onClick={onClose}
                className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center border-2 border-fg/20 hover:border-fg transition-colors"
                style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
              >
                <X className="w-4 h-4 text-fg" />
              </button>

              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-secondary/10 rounded-full mb-4">
                  <Zap className="w-6 h-6 text-secondary" />
                </div>
                <h2 className="font-heading text-2xl text-fg mb-1">{title}</h2>
                <p className="font-body text-fg/60">{message}</p>
              </div>

              <div className="mb-6">
                <WobblyBadge variant="accent" className="mb-3">
                  Chuyên nghiệp — 299K/tháng
                </WobblyBadge>
                <ul className="space-y-2">
                  {premiumFeatures.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 font-body text-fg/80">
                      <Check className="w-4 h-4 text-secondary flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex gap-3">
                <WobblyButton variant="secondary" className="flex-1" onClick={onClose}>
                  Để sau
                </WobblyButton>
                <Link href="/upgrade" className="flex-1">
                  <WobblyButton className="w-full">Nâng cấp ngay</WobblyButton>
                </Link>
              </div>
            </WobblyCard>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
