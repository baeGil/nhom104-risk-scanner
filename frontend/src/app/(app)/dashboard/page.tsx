import Link from "next/link";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyBadge } from "@/components/ui/wobbly-badge";
import { FileText, MessageSquare, Activity, Database } from "lucide-react";

const mockStats = [
  { label: "Hợp đồng đã rà soát", value: "12", icon: FileText, color: "text-secondary" },
  { label: "Câu hỏi đã hỏi", value: "47", icon: MessageSquare, color: "text-accent" },
  { label: "Trạng thái hệ thống", value: "Hoạt động", icon: Activity, color: "text-green-600" },
  { label: "Văn bản trong KG", value: "12,921", icon: Database, color: "text-fg" },
];

const mockContracts = [
  { name: "Hợp đồng thuê VP.pdf", status: "completed", date: "2026-05-08" },
  { name: "Hợp đồng lao động.docx", status: "completed", date: "2026-05-07" },
  { name: "Phụ lục hợp đồng.pdf", status: "processing", date: "2026-05-09" },
];

const mockQuestions = [
  { question: "Điều 17 Luật Doanh nghiệp quy định gì?", domain: "QA", date: "2026-05-09" },
  { question: "Luật DN 2020 còn hiệu lực không?", domain: "VALIDITY", date: "2026-05-08" },
  { question: "So sánh Luật DN 2020 và 2014", domain: "COMPARISON", date: "2026-05-07" },
];

const quickActions = [
  { href: "/contract-review", label: "Rà soát hợp đồng", icon: FileText, desc: "Tải lên và phân tích hợp đồng" },
  { href: "/legal-qa", label: "Hỏi đáp pháp lý", icon: MessageSquare, desc: "Đặt câu hỏi về pháp luật" },
  { href: "/settings", label: "Cài đặt", icon: Activity, desc: "Quản lý tài khoản" },
  { href: "/upgrade", label: "Nâng cấp", icon: Database, desc: "Xem các gói dịch vụ" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <h1 className="font-heading text-4xl text-fg">Tổng quan</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {mockStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <WobblyCard key={stat.label} className="text-center p-4">
              <Icon className={`w-8 h-8 mx-auto mb-2 ${stat.color}`} strokeWidth={2.5} />
              <div className="font-heading text-2xl text-fg">{stat.value}</div>
              <div className="font-body text-sm text-fg/60">{stat.label}</div>
            </WobblyCard>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="font-heading text-2xl text-fg mb-4">Thao tác nhanh</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.href} href={action.href}>
                <WobblyCard className="hover:-rotate-1 cursor-pointer">
                  <Icon className="w-8 h-8 text-secondary mb-3" strokeWidth={2.5} />
                  <h3 className="font-heading text-lg text-fg">{action.label}</h3>
                  <p className="font-body text-sm text-fg/60">{action.desc}</p>
                </WobblyCard>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Contracts */}
      <div>
        <h2 className="font-heading text-2xl text-fg mb-4">Hợp đồng gần đây</h2>
        <WobblyCard>
          <div className="space-y-3">
            {mockContracts.map((c) => (
              <div key={c.name} className="flex items-center justify-between py-2 border-b border-fg/10 last:border-0">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-fg/40" />
                  <span className="font-body text-fg">{c.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <WobblyBadge
                    variant={c.status === "completed" ? "secondary" : "postit"}
                  >
                    {c.status === "completed" ? "Hoàn thành" : "Đang xử lý"}
                  </WobblyBadge>
                  <span className="font-body text-sm text-fg/40">{c.date}</span>
                </div>
              </div>
            ))}
          </div>
        </WobblyCard>
      </div>

      {/* Recent Questions */}
      <div>
        <h2 className="font-heading text-2xl text-fg mb-4">Câu hỏi gần đây</h2>
        <WobblyCard>
          <div className="space-y-3">
            {mockQuestions.map((q) => (
              <div key={q.question} className="flex items-center justify-between py-2 border-b border-fg/10 last:border-0">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <MessageSquare className="w-5 h-5 text-fg/40 flex-shrink-0" />
                  <span className="font-body text-fg truncate">{q.question}</span>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <WobblyBadge variant="default">{q.domain}</WobblyBadge>
                  <span className="font-body text-sm text-fg/40">{q.date}</span>
                </div>
              </div>
            ))}
          </div>
        </WobblyCard>
      </div>
    </div>
  );
}
