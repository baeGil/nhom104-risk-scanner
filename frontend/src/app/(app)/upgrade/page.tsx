"use client";

import { motion } from "framer-motion";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyBadge } from "@/components/ui/wobbly-badge";

const tiers = [
  {
    name: "Miễn phí",
    price: "0đ",
    period: "/tháng",
    features: ["5 hợp đồng/tháng", "10 câu hỏi/ngày", "Trích dẫn cơ bản"],
    cta: "Bắt đầu",
    highlighted: false,
  },
  {
    name: "Chuyên nghiệp",
    price: "299K",
    period: "/tháng",
    features: ["Không giới hạn hợp đồng", "Không giới hạn câu hỏi", "Trích dẫn đã xác minh", "Ưu tiên xử lý", "Hỗ trợ email"],
    cta: "Dùng thử",
    highlighted: true,
  },
  {
    name: "Doanh nghiệp",
    price: "Liên hệ",
    period: "",
    features: ["Tất cả tính năng Pro", "API access", "Custom integration", "SLA cam kết", "Hỗ trợ 24/7"],
    cta: "Liên hệ",
    highlighted: false,
  },
];

export default function UpgradePage() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="font-heading text-4xl text-fg mb-2">Nâng cấp</h1>
        <p className="font-body text-xl text-fg/60">Chọn gói phù hợp với nhu cầu của bạn</p>
      </div>

      <div className="grid md:grid-cols-3 gap-8 items-start">
        {tiers.map((tier) => (
          <motion.div
            key={tier.name}
            className={tier.highlighted ? "md:scale-105" : ""}
            whileHover={{ rotate: tier.highlighted ? 0 : 1 }}
          >
            <WobblyCard
              variant={tier.highlighted ? "postit" : "default"}
              decoration={tier.highlighted ? "tape" : "none"}
              className="text-center"
            >
              {tier.highlighted && (
                <WobblyBadge variant="accent" className="mb-4">
                  Phổ biến
                </WobblyBadge>
              )}
              <h3 className="font-heading text-2xl text-fg mb-2">{tier.name}</h3>
              <div className="mb-6">
                <span className="font-heading text-4xl text-fg">{tier.price}</span>
                <span className="font-body text-fg/60">{tier.period}</span>
              </div>
              <ul className="space-y-3 mb-6 text-left">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-fg/80">
                    <span className="text-secondary">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>
              <WobblyButton
                variant={tier.highlighted ? "primary" : "secondary"}
                className="w-full"
              >
                {tier.cta}
              </WobblyButton>
            </WobblyCard>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
