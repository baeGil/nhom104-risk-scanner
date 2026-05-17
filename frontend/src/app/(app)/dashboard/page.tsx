"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyBadge } from "@/components/ui/wobbly-badge";
import { contractApi, qaApi } from "@/lib/api";
import { FileText, MessageSquare, Activity, Database } from "lucide-react";

const mockStats = [
  { label: "Hợp đồng đã rà soát", value: "12", icon: FileText, color: "text-secondary" },
  { label: "Câu hỏi đã hỏi", value: "47", icon: MessageSquare, color: "text-accent" },
  { label: "Trạng thái hệ thống", value: "Hoạt động", icon: Activity, color: "text-green-600" },
  { label: "Văn bản trong KG", value: "12,921", icon: Database, color: "text-fg" },
];

const quickActions = [
  { href: "/contract-review", label: "Rà soát hợp đồng", icon: FileText, desc: "Tải lên và phân tích hợp đồng" },
  { href: "/legal-qa", label: "Hỏi đáp pháp lý", icon: MessageSquare, desc: "Đặt câu hỏi về pháp luật" },
  { href: "/settings", label: "Cài đặt", icon: Activity, desc: "Quản lý tài khoản" },
  { href: "/upgrade", label: "Nâng cấp", icon: Database, desc: "Xem các gói dịch vụ" },
];

type RecentQuestion = {
  id: string;
  title: string;
  lastMessage?: string;
  createdAt: string;
  lastMessageAt?: string | null;
};

type RecentContract = {
  id: string;
  filename: string;
  status: string;
  createdAt: string;
};

export default function DashboardPage() {
  const [recentQuestions, setRecentQuestions] = useState<RecentQuestion[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [recentContracts, setRecentContracts] = useState<RecentContract[]>([]);
  const [isLoadingContracts, setIsLoadingContracts] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const loadRecentQuestions = async () => {
      try {
        const conversations = await qaApi.getConversations();
        if (!isMounted) return;
        setRecentQuestions(
          conversations.slice(0, 5).map((conversation) => ({
            id: conversation.id,
            title: conversation.title,
            lastMessage: conversation.lastMessage,
            createdAt: conversation.createdAt,
            lastMessageAt: conversation.lastMessageAt,
          }))
        );
      } catch (error) {
        console.error("Could not load recent QA conversations:", error);
        if (!isMounted) return;
        setRecentQuestions([]);
      } finally {
        if (isMounted) setIsLoadingQuestions(false);
      }
    };

    loadRecentQuestions();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadRecentContracts = async () => {
      try {
        const history = await contractApi.getJobHistory();
        if (!isMounted) return;
        setRecentContracts(
          history.slice(0, 5).map((job) => ({
            id: job.id,
            filename: job.filename,
            status: job.status,
            createdAt: job.createdAt,
          }))
        );
      } catch (error) {
        console.error("Could not load recent contract reviews:", error);
        if (!isMounted) return;
        setRecentContracts([]);
      } finally {
        if (isMounted) setIsLoadingContracts(false);
      }
    };

    loadRecentContracts();

    return () => {
      isMounted = false;
    };
  }, []);

  const formatDate = (value?: string | null) => {
    if (!value) return "";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    return date.toLocaleDateString("sv-SE");
  };

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
            {isLoadingContracts ? (
              <div className="py-2 font-body text-fg/60">Đang tải lịch sử rà soát...</div>
            ) : recentContracts.length === 0 ? (
              <div className="py-2 font-body text-fg/60">Chưa có lần rà soát hợp đồng nào.</div>
            ) : (
              recentContracts.map((contract) => (
                <Link
                  key={contract.id}
                  href={`/contract-review?jobId=${contract.id}`}
                  className="flex items-center justify-between gap-3 py-2 border-b border-fg/10 last:border-0 hover:bg-secondary/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-fg/40" />
                    <span className="font-body text-fg">{contract.filename}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <WobblyBadge
                      variant={contract.status === "completed" ? "secondary" : contract.status === "failed" ? "accent" : "postit"}
                    >
                      {contract.status === "completed" ? "Hoàn thành" : contract.status === "failed" ? "Thất bại" : "Đang xử lý"}
                    </WobblyBadge>
                    <span className="font-body text-sm text-fg/40">{formatDate(contract.createdAt)}</span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </WobblyCard>
      </div>

      {/* Recent Questions */}
      <div>
        <h2 className="font-heading text-2xl text-fg mb-4">Câu hỏi gần đây</h2>
        <WobblyCard>
          <div className="space-y-3">
            {isLoadingQuestions ? (
              <div className="py-2 font-body text-fg/60">Đang tải cuộc trò chuyện...</div>
            ) : recentQuestions.length === 0 ? (
              <div className="py-2 font-body text-fg/60">
                Chưa có cuộc trò chuyện nào. Vào mục Hỏi đáp pháp lý để bắt đầu.
              </div>
            ) : (
              recentQuestions.map((conversation) => (
                <Link
                  key={conversation.id}
                  href={`/legal-qa?conversationId=${conversation.id}`}
                  className="flex items-center justify-between gap-3 py-2 border-b border-fg/10 last:border-0 hover:bg-secondary/5 transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <MessageSquare className="w-5 h-5 text-fg/40 flex-shrink-0" />
                    <span className="font-body text-fg truncate">
                      {conversation.title || conversation.lastMessage || "Cuộc trò chuyện chưa có tiêu đề"}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <WobblyBadge variant="default">QA</WobblyBadge>
                    <span className="font-body text-sm text-fg/40">
                      {formatDate(conversation.lastMessageAt || conversation.createdAt)}
                    </span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </WobblyCard>
      </div>
    </div>
  );
}
