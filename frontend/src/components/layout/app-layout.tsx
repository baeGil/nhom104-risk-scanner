"use client";

import { useState } from "react";
import { Sidebar } from "./sidebar";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-shrink-0 h-screen">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      </div>
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <header className="border-b-2 border-fg bg-white/60 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div className="font-body text-fg/60">PhápLý — AI Pháp Lý Việt Nam</div>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
