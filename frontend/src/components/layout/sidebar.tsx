"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  FileText,
  MessageSquare,
  LayoutDashboard,
  Settings,
  Zap,
  LogOut,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { href: "/contract-review", label: "Rà soát hợp đồng", icon: FileText },
  { href: "/legal-qa", label: "Hỏi đáp pháp lý", icon: MessageSquare },
  { href: "/settings", label: "Cài đặt", icon: Settings },
  { href: "/upgrade", label: "Nâng cấp", icon: Zap },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  return (
    <aside
      className={cn(
        "h-screen border-r-2 border-fg bg-white/90 backdrop-blur-sm flex flex-col relative overflow-hidden transition-[width] duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo / Toggle */}
      <div
        className={cn(
          "flex items-center border-b-2 border-fg/20 h-16 transition-all duration-300",
          collapsed ? "justify-center px-2" : "justify-between px-4"
        )}
      >
        <div
          className={cn(
            "overflow-hidden transition-all duration-300 ease-in-out whitespace-nowrap",
            collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
          )}
        >
          <Link href="/" className="font-heading text-2xl text-fg hover:text-accent transition-colors">
            PhápLý
          </Link>
        </div>
        <button
          onClick={onToggle}
          className={cn(
            "flex items-center justify-center w-8 h-8 border-2 border-fg/30 hover:border-fg hover:bg-muted transition-all duration-200 flex-shrink-0",
            !collapsed && "ml-auto"
          )}
          style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
        >
          <svg
            className={cn("w-4 h-4 text-fg transition-transform duration-300", collapsed && "rotate-180")}
            viewBox="0 0 16 16"
            fill="none"
          >
            <path d="M10 3 L5 8 L10 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-4 space-y-1 px-2 overflow-hidden">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <div
              key={href}
              className="relative"
              onMouseEnter={() => collapsed && setHoveredItem(href)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <Link
                href={href}
                className={cn(
                  "flex items-center py-3 overflow-hidden transition-all duration-300 ease-in-out",
                  collapsed ? "justify-center px-0" : "px-4 gap-3",
                  isActive
                    ? "bg-fg text-white"
                    : "text-fg hover:bg-muted"
                )}
                style={{ borderRadius: "8px" }}
              >
                <Icon className="w-5 h-5 flex-shrink-0" strokeWidth={2.5} />
                <span
                  className={cn(
                    "font-body text-lg whitespace-nowrap transition-all duration-300 ease-in-out",
                    collapsed ? "w-0 opacity-0 ml-0" : "w-auto opacity-100 ml-0"
                  )}
                >
                  {label}
                </span>
              </Link>
              {collapsed && hoveredItem === href && (
                <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-3 py-1.5 bg-fg text-white font-body text-sm whitespace-nowrap z-50 pointer-events-none">
                  {label}
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 w-2 h-2 bg-fg rotate-45" />
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-2 border-t-2 border-fg/20">
        <div
          className="relative"
          onMouseEnter={() => collapsed && setHoveredItem("logout")}
          onMouseLeave={() => setHoveredItem(null)}
        >
          <Link
            href="/"
            className={cn(
              "flex items-center py-3 overflow-hidden transition-all duration-300 ease-in-out",
              collapsed ? "justify-center px-0" : "px-4 gap-3",
              "text-fg/60 hover:text-accent hover:bg-muted/50"
            )}
            style={{ borderRadius: "8px" }}
          >
            <LogOut className="w-5 h-5 flex-shrink-0" strokeWidth={2.5} />
            <span
              className={cn(
                "font-body text-lg whitespace-nowrap transition-all duration-300 ease-in-out",
                collapsed ? "w-0 opacity-0 ml-0" : "w-auto opacity-100 ml-0"
              )}
            >
              Đăng xuất
            </span>
          </Link>
          {collapsed && hoveredItem === "logout" && (
            <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-3 py-1.5 bg-fg text-white font-body text-sm whitespace-nowrap z-50 pointer-events-none">
              Đăng xuất
              <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 w-2 h-2 bg-fg rotate-45" />
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
