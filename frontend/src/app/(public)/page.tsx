"use client";

import { useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyBadge } from "@/components/ui/wobbly-badge";
import { AnimatedCounter } from "@/components/ui/animated-counter";
import { SquiggleSVG } from "@/components/decorative/squiggle-svg";
import { ArrowSVG } from "@/components/decorative/arrow-svg";
import { FileText, MessageSquare } from "lucide-react";

function FadeInSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

const features = [
  {
    icon: FileText,
    title: "Rà soát hợp đồng",
    description: "Tải lên hợp đồng PDF/DOCX, AI tự động phân tích điều khoản, phát hiện rủi ro và đối chiếu với pháp luật hiện hành.",
    bullets: ["Parse PDF/DOCX tự động", "Trích xuất điều khoản", "Phân tích tuân thủ", "Xác minh trích dẫn"],
  },
  {
    icon: MessageSquare,
    title: "Hỏi đáp pháp lý",
    description: "Đặt câu hỏi bằng tiếng Việt, AI phân tích intent, truy xuất văn bản pháp lý và trả lời kèm trích dẫn chính xác.",
    bullets: ["Hỏi bằng tiếng Việt", "Phân tích intent tự động", "Truy xuất văn bản", "Trả lời có trích dẫn"],
  },
];

const steps = [
  { num: 1, title: "Tải lên", desc: "Kéo thả hợp đồng PDF hoặc DOCX" },
  { num: 2, title: "AI phân tích", desc: "Trích xuất điều khoản, đối chiếu pháp luật" },
  { num: 3, title: "Báo cáo", desc: "Xem kết quả với trích dẫn đã xác minh" },
];

const pricingTiers = [
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

export default function LandingPage() {
  const [demoText, setDemoText] = useState("");
  const [demoResult, setDemoResult] = useState(false);

  const handleDemo = () => {
    if (demoText.trim()) {
      setDemoResult(true);
    }
  };

  return (
    <div className="font-body">
      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 py-20 md:py-32">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <motion.h1
              className="font-heading text-5xl md:text-6xl text-fg leading-tight mb-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              Rà soát hợp đồng
              <br />
              <span className="text-accent">trong 30 giây</span>
              <motion.span
                className="inline-block text-accent ml-2"
                animate={{ rotate: [0, 10, -5, 0] }}
                transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              >
                !
              </motion.span>
            </motion.h1>
            <motion.p
              className="text-xl text-fg/70 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              AI phân tích rủi ro hợp đồng và hỏi đáp pháp lý tiếng Việt.
              Đối chiếu tự động với 12,921 văn bản pháp luật hiện hành.
            </motion.p>
            <motion.div
              className="flex gap-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <WobblyButton size="lg" onClick={() => window.location.href = "/contract-review"}>
                Thử ngay →
              </WobblyButton>
              <WobblyButton variant="secondary" size="lg" onClick={() => window.location.href = "/legal-qa"}>
                Hỏi đáp
              </WobblyButton>
            </motion.div>
          </div>

          {/* Interactive Demo */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <WobblyCard decoration="tape" className="bg-white">
              <h3 className="font-heading text-2xl text-fg mb-4">Thử phân tích nhanh</h3>
              <textarea
                className="w-full border-2 border-fg bg-white p-4 font-body text-lg resize-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 focus:outline-none"
                style={{ borderRadius: "120px 8px 90px 8px / 8px 90px 8px 120px" }}
                rows={4}
                placeholder="Dán đoạn hợp đồng cần phân tích..."
                value={demoText}
                onChange={(e) => setDemoText(e.target.value)}
              />
              <div className="mt-4">
                <WobblyButton onClick={handleDemo} disabled={!demoText.trim()}>
                  Phân tích
                </WobblyButton>
              </div>
              {demoResult && (
                <motion.div
                  className="mt-4 p-4 bg-postit border-2 border-fg"
                  style={{ borderRadius: "120px 8px 90px 8px / 8px 90px 8px 120px" }}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <h4 className="font-heading text-lg text-fg mb-2">Kết quả mô phỏng:</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-green-600">✓</span>
                      <span className="text-fg">Điều khoản thanh toán — Ổn</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-accent">⚠</span>
                      <span className="text-fg">Phạt vi phạm — Có thể quá cao</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-fg/40">?</span>
                      <span className="text-fg/60">Bảo hành — Cần xem thêm</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </WobblyCard>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <FadeInSection>
        <section className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="font-heading text-4xl md:text-5xl text-fg text-center mb-16">
            Cách hoạt động
          </h2>
          <div className="grid md:grid-cols-3 gap-8 items-start">
            {steps.map((step, i) => (
              <FadeInSection key={step.num} delay={i * 0.2}>
                <div className="flex flex-col items-center text-center">
                  <div
                    className="w-20 h-20 bg-fg text-white rounded-full flex items-center justify-center font-heading text-3xl mb-4"
                    style={{ borderRadius: "45% 55% 50% 50% / 55% 45% 55% 45%" }}
                  >
                    {step.num}
                  </div>
                  <h3 className="font-heading text-2xl text-fg mb-2">{step.title}</h3>
                  <p className="text-fg/70">{step.desc}</p>
                </div>
              </FadeInSection>
            ))}
          </div>
          <div className="flex justify-center mt-4">
            <SquiggleSVG className="w-64" />
          </div>
        </section>
      </FadeInSection>

      {/* Features */}
      <FadeInSection>
        <section className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="font-heading text-4xl md:text-5xl text-fg text-center mb-16">
            Tính năng chính
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <FadeInSection key={feature.title} delay={i * 0.15}>
                  <WobblyCard decoration="tack">
                    <div className="flex items-start gap-4 mb-4">
                      <div className="w-12 h-12 border-2 border-fg flex items-center justify-center" style={{ borderRadius: "45% 55% 50% 50% / 55% 45% 55% 45%" }}>
                        <Icon className="w-6 h-6" strokeWidth={2.5} />
                      </div>
                      <div>
                        <h3 className="font-heading text-2xl text-fg">{feature.title}</h3>
                        <p className="text-fg/70 mt-1">{feature.description}</p>
                      </div>
                    </div>
                    <ul className="space-y-2 mt-4">
                      {feature.bullets.map((bullet) => (
                        <li key={bullet} className="flex items-center gap-2 text-fg/80">
                          <span className="text-secondary">✦</span>
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  </WobblyCard>
                </FadeInSection>
              );
            })}
          </div>
        </section>
      </FadeInSection>

      {/* Stats */}
      <FadeInSection>
        <section className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="font-heading text-4xl md:text-5xl text-fg text-center mb-16">
            Cơ sở tri thức
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: 12921, label: "Văn bản", suffix: "" },
              { value: 900, label: "Nodes", suffix: "K+" },
              { value: 659, label: "Quan hệ", suffix: "K+" },
              { value: 35, label: "VB hợp nhất", suffix: "" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div
                  className="inline-flex items-center justify-center w-24 h-24 md:w-32 md:h-32 bg-white border-2 border-fg shadow-hard mb-4"
                  style={{ borderRadius: "45% 55% 50% 50% / 55% 45% 55% 45%" }}
                >
                  <AnimatedCounter
                    target={stat.value}
                    suffix={stat.suffix}
                    className="font-heading text-2xl md:text-4xl text-fg"
                  />
                </div>
                <p className="font-body text-lg text-fg/70">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>
      </FadeInSection>

      {/* Pricing */}
      <FadeInSection>
        <section className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="font-heading text-4xl md:text-5xl text-fg text-center mb-16">
            Bảng giá
          </h2>
          <div className="grid md:grid-cols-3 gap-8 items-start">
            {pricingTiers.map((tier, i) => (
              <FadeInSection key={tier.name} delay={i * 0.15}>
                <div className={tier.highlighted ? "md:scale-105" : ""}>
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
                </div>
              </FadeInSection>
            ))}
          </div>
        </section>
      </FadeInSection>
    </div>
  );
}
